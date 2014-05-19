#
# convert_illumina_bcl.rb
#
# APF analysis module to convert BCL files to FASTQ
# for an Illumina Genome Analyzer or HiSeq sequencing run
#
# Phil Lacroute
# Keith Bettinger (conversion to CASAVA 1.8 and BWA)
#

require 'fileutils'
require 'csv'

require 'illumina_manager'

module ConvertIlluminaBcl

  include IlluminaManager

  # set default values for parameters
  def default_params

    set_param("rerun", false)
    set_param("read1_only", false)
    set_param("run_bwa", false)

    # Default list of lanes to use
    @@lane_list = [1, 2, 3, 4, 5, 6, 7, 8]
  end

  # define command-line options
  def analysis_options(opts)

    opts.on("-r", "--run RUN", "Set run name") do |run|
      # Parse lanes from run_name, if necessary.
      if run =~ /^(.*):(\d+)$/
        set_param("run_name", $1)
        @@lane_list = $2.split(//).map{|lane| lane.to_i}
      else
        set_param("run_name", run)
      end
    end

    opts.on("-p", "--params FILE", "Parameter file") do |file|
      set_param("params_file", file)
    end

    opts.on("-l", "--lanes LANES", "Lane numbers to run on, concatenated (e.g., 1234)") do |lanes|
      @@lane_list = lanes.split(//).map{|lane| lane.to_i}
    end

    opts.on("--out_dir DIR", "The directory to put the full FASTQ output files under") do |dir|
       set_param("out_dir", dir)
    end

    opts.on("--subpart_dir DIR", "The directory to put the subpart FASTQ output files under") do |dir|
      set_param("subpart_dir", dir)
    end

    opts.on("--rerun", "Analyze this run again. Certain files/directories, if present, will be overwritten for the rerun lanes, such as the Unalighed_L\d directories, the samplesheet") do
      set_param("rerun", true)
    end

    opts.on("--run_bwa", "Run BWA on results of this job") do
      set_param("run_bwa", true)
    end

    opts.on("--read1_only", "Only run read 1 of paired end run") do
      set_param("read1_only", true)
    end

    opts.on("--pipeline_mode", "This APF job is run within a pipeline (e.g., allow existing archive dir).") do
      set_param("pipeline_mode", true)
    end

    opts.on("--barcode_length LEN","Trim the barcode to this maximum length") do |len|
      set_param("barcode_length", len)

      puts "barcode_length  following switch: #{@config[:barcode_length]}"
    end

    opts.on("--force", "Continue past some error conditions") do
       @force = true
    end

    opts.on("--dev", "Run with development modules") do
      @dev = true
    end

    opts.on("--verbose", "Increase detail of log output") do
      set_param("verbose", true)
      set_param("log_level", "verbose")
    end

  end

  # validate command-line options
  def validations
    die "either --run or --params option must be specified" if
      @config[:run_name].nil? && @config[:params_file].nil?
  end

  # prepare the analysis
  def analysis_definition

    # set the file-creation umask (group-writable)
    File.umask(0002)

    # fetch parameters
    if !@config[:params_file].nil?
      load_config @config[:params_file]
    else
      query_lims(run = @config[:run_name], ##defined in apf.rb
                 status = "new")
    end
    die "missing run_dir" if blank?(@config[:run_dir])
    die "missing pipeline_run_id" if blank?(@config[:pipeline_run_id])
    # Set lane_list to [1] if MiSeq run.
    @@lane_list = [1] if @config[:platform] == "miseq"

    # Parse run name for use in job suffixes.
    (run_date, run_mach, run_numb, run_flow) = @config[:run_name].split(/_/,4)
    set_param "job_suffix", "#{@config[:pipeline_run_id]}_#{run_mach[0,4]}_#{run_numb}"

    # get pipeline version
    pipeline_version = @config[:pipeline_version]
    throw "missing pipeline version" if blank?(pipeline_version)
    if pipeline_version =~ /^([0-9.]+)[-\/]([0-9.]+)$/
      olb_version = $1
      casava_version = $2
    else
      olb_version = casava_version = pipeline_version
    end
    set_param("casava_version", casava_version, :no_overwrite => true)

    die "need CASAVA 1.8 (not #{casava_version})" if casava_version !~ /^1\.8/

    # prepare directories for config files and results
    prepare_directories(@@lane_list)
    Dir.chdir(@config[:analysis_dir])

    # copy parameters to analysis directory prior to checking for errors
    # this makes it easier to manually edit the config to fix problems
    set_param("stored_params_file", "#{@config[:analysis_dir]}/config.txt")
    store_config(@config[:stored_params_file]) ##defined in apf

    # Set up modules parameters.
    if not @dev
      set_production_modules ##defined in IlluminaManager
    else
      set_development_modules ##defined in IlluminaManager
    end

    # prepare Illumina pipeline config files and makefiles
    prepare_illumina_pipeline(@@lane_list)

    # copy the final set of parameters to analysis and archive dirs
    store_config(@config[:stored_params_file])  ##defined in apf
    store_config(File.join(@config[:archive_dir],"config_bcl.txt"))  ##defined in apf

    # construct the job description file
    prepare_jobs(@@lane_list)

  end

  def prepare_directories(lane_list)

    # make analysis directory
    analysis_root =
      "#{@config[:run_dir]}/analysis_#{@config[:pipeline_run_id]}"
    Dir.mkdir(analysis_root) unless File::exists?(analysis_root)

    analysis_dir = "#{analysis_root}/convert_illumina_bcl"
    Dir.mkdir(analysis_dir) unless File::exists?(analysis_dir)

    # Set log file for APF output.
    set_param("bcl_log_file", File.join(analysis_dir, "#{@config[:run_name]}.apf.log") )
    set_log_file @config[:bcl_log_file]

    log :info, "Analysis Dir: #{analysis_dir}"

    set_param "analysis_dir", analysis_dir
    set_param "bcl_analysis_dir", analysis_dir

    # Create lane-specific subdirectories in analysis_dir.
    lane_list.each do |lane|
      analysis_lane_dir = File.join(analysis_dir, "L#{lane}")
      if not File::exists?(analysis_lane_dir)
        Dir.mkdir(analysis_lane_dir)
      else
        # Rerun: remove the seq_stats.txt files from the analysis dir.
        if @config[:rerun]
          log :info, "rerun: Removing the seq_stats.txt files for lane #{lane} from Analysis dir #{analysis_lane_dir}"
          Dir.glob(File.join(analysis_lane_dir, "*_L#{lane}_*seq_stats*.txt")) do |file|
            log :verbose, "       removing #{file}"
            remove_file file
          end  # glob
        end  # config[:rerun]
      end
    end

    # check directory names and set defaults
    set_param("intensities_dir", "#{@config[:run_dir]}/Data/Intensities",
              :no_overwrite => true)  # if not already set
    set_param("base_calls_dir", "#{@config[:intensities_dir]}/BaseCalls",
              :no_overwrite => true)  # if not already set
    intensities_dir = @config[:intensities_dir]
    #log :info, "Intensities: #{intensities_dir}"
    base_calls_dir = @config[:base_calls_dir]
    log :info, "Base calls Dir: #{base_calls_dir}"
    archive_dir = @config[:archive_dir]
    log :info, "Archive Dir: #{archive_dir}"
    if (blank?(intensities_dir) || blank?(base_calls_dir) || blank?(archive_dir))
      die "LIMS record is incomplete"
    end

    # check starting_data_type
    if @config[:starting_data_type] == "base_calls"
      throw "please change starting_data_type to BCL"
    end
    if @config[:starting_data_type] == "base_calls_qseq"
      throw "you will need to convert Qseq -> FASTQ yourself."
    end
    if @config[:starting_data_type] == "intensities"
      throw "Bustard not supported in this apf version."
    end
    if @config[:starting_data_type] != "base_calls_bcl"
      throw "invalid starting_data_type: #{@config[:starting_data_type]}"
    end

    # Make defaults for "out_dir", "subpart_dir".
    set_param("out_dir", @config[:archive_dir]) if @config[:out_dir].nil?
    set_param("subpart_dir", File.join(@config[:run_dir],"BCL_temp")) if @config[:subpart_dir].nil?

    # make out dir, if necessary.
    out_dir = @config[:out_dir]
    if File::exists? out_dir
      if not @config[:pipeline_mode]
        if not @config[:rerun]
          die "#{out_dir} already exists"
        else  # Rerun:
          lane_list.each do |lane|
            # Rerun: Remove the lane directories in the out dir dir.
            log :info, "rerun: Removing existing out dir lane #{lane} dir in #{out_dir}"
            remove_dir File.join(out_dir, "L#{lane}")

            # Rerun: Remove lane files in out dir (publish files).
            log :info, "rerun: Removing lane #{lane} files from out dir #{out_dir}"
            Dir.glob(File.join(out_dir, "*_L#{lane}_*")) do |file|
              remove_file file
            end

          end  # lane_list.each

        end  # if not rerun
      else
        # Pipeline mode: assume out_dir was created upstream.
      end # if not pipeline_mode
    else
      log :info, "Creating out dir #{out_dir}"
      Dir.mkdir out_dir
    end

    # Create lane-specific subdirectories in out_dir, if necessary.
    lane_list.each do |lane|
      out_lane_dir = File.join(@config[:out_dir], "L#{lane}")
      Dir.mkdir(out_lane_dir) if not File::exists?(out_lane_dir)
    end

    # make subpart dir, if necessary.
    subpart_dir = @config[:subpart_dir]
    if File::exists? subpart_dir
      #if not @config[:rerun]
      #  die "Subpart dir #{subpart_dir} already exists"
      #end
    else
      log :info, "Creating subpart dir #{subpart_dir}"
      Dir.mkdir subpart_dir
    end

    # Create lane-specific subdirectories in subpart_dir.
    lane_list.each do |lane|
      subpart_lane_dir = File.join(@config[:subpart_dir], "L#{lane}")
      if File::exists? subpart_lane_dir
        if not @config[:rerun]
          die "Subpart lane dir #{subpart_lane_dir} already exists"
        else
          # Rerun: Remove lane subdir in subpart dir.
          log :info, "rerun: Removing subpart lane dir #{subpart_lane_dir}"
          remove_dir subpart_lane_dir
        end
      end

      log :info, "Creating subpart lane dir #{subpart_lane_dir}"
      Dir.mkdir subpart_lane_dir
    end

  end


  # run the Illumina scripts to prepare the analysis makefiles
  def prepare_illumina_pipeline(lane_list)

    set_param("fastq_cluster_count", 12000000) # 12M reads in each FASTQ file.

    if @config[:starting_data_type] == "base_calls_bcl"
      # create BCL converter makefiles
      prepare_bcl_converter lane_list
    else
      throw "starting data type of #{@config[:starting_data_type]} not supported"
    end

  end

  # run the BCL converter setup script
  def prepare_bcl_converter(lane_list)

    paired_end_run = paired_end_run? # (@config[:paired_end] == "true")
    index_read_run = (@config[:index_read] == "true")
    dual_index_run = (@config[:index2_cycles].to_i != 0)

    lane_list.each do |lane|

      unaligned_lane_dir = File.join(@config[:run_dir],"Unaligned_L#{lane}")
      if File::exists? unaligned_lane_dir
        if not @config[:rerun]
          die "#{unaligned_lane_dir} already exists"
        else
          # Remove existing Unaligned dir.
          log :info, "rerun: Removing existing Unaligned dir #{unaligned_lane_dir}"
          remove_dir unaligned_lane_dir
        end
      end

      # if rerunning, delete the old samplesheet from the analysis directory
      samplesheet = File.join(@config[:analysis_dir], "L#{lane}", "samplesheet_L#{lane}.csv")
      if File::exists?(samplesheet)
        if not @config[:rerun]
          die "samplesheet #{samplesheet} already exists"
        else
          # Remove samplesheet.csv
          log :info, "rerun: removing old samplesheet #{samplesheet}"
          remove_file samplesheet
        end
      end

      # create the sample sheet
      configure_samplesheet samplesheet, [lane]

      use_bases_mask = calculate_use_bases_mask lane, paired_end_run, index_read_run, dual_index_run
      raise "use_bases_mask could not be calculated for lane #{lane}" if use_bases_mask.nil?

      bcl_cmd = "configureBclToFastq.pl" +
        " --input-dir #{@config[:base_calls_dir]}" +
        " --output-dir #{unaligned_lane_dir}" +
        " --fastq-cluster-count #{@config[:fastq_cluster_count]}" +
        " --sample-sheet #{samplesheet}" +
        " --ignore-missing-bcl --ignore-missing-stats"
      # BRITTLE CODE WARNING: What if casava_version goes past 1.8.2?
      if @config[:casava_version] == "1.8.2"
        bcl_cmd += " --with-failed-reads"
        bcl_cmd += " --use-bases-mask '#{use_bases_mask}'"
      end
      bcl_cmd += " 2>&1"
      log :info, bcl_cmd

      # Run the command to configure the BCL/demux conversion.
      run_bcl_cmd = run_with_modules(bcl_cmd, "casava/#{@config[:casava_version]}")
      log :info, run_bcl_cmd

      success = false
      IO.popen(run_bcl_cmd).each do |line|
        log :info, line
        success = true if line =~ /self tests.*completed with no problems/
      end
      die "BCL converter exited abnormally: #{$?}" if $? != 0
      die "BCL converter failed" unless success

    end  # lane_list.each
  end

  # prepare the jobs to run the analysis
  def prepare_jobs(lane_list)

    # generate fastq files for each lane
    lane_list.each do |lane|

      lane_analysis_dir = File.join(@config[:analysis_dir], "L#{lane}")

      # create an sjm job description file
      sjm_lane_file = File.join(lane_analysis_dir, "#{@config[:run_name]}_L#{lane}.sjm")
      define_jobs(sjm_lane_file) do |sjm| ##defined in apf

        # set some sjm options
        sjm.default_queue "seq_pipeline"

        sjm.log_dir lane_analysis_dir

        # post-process the FASTQ files from BCL conversion.
        #  Subpart files go into :subpart_dir, while merged files go into :out_dir.

        unaligned_lane_dir = File.join(@config[:run_dir], "Unaligned_L#{lane}")
        subpart_lane_dir   = File.join(@config[:subpart_dir], "L#{lane}")
        outdir_lane_dir    = File.join(@config[:out_dir], "L#{lane}")

        ###
        # Set the analysis status to BCL_STARTED.
        ###
        status_cmd = "analysis_status.py"
        status_cmd += " --set"
        status_cmd += " --lane #{lane}"
        status_cmd += " #{@config[:run_dir]}"
        status_cmd += " BCL_STARTED"

        status_bcl_started_job_name = "status_bcl_started_L#{lane}_#{@config[:job_suffix]}"

        status_job = Hash.new()
        status_job[:name] = status_bcl_started_job_name
        status_job[:cmd]  = status_cmd
        status_job[:host] = "localhost"
        status_job[:modules] = @config[:module_rundir]

        sjm.job(status_job)

        dependency = nil
        paired_end_run = paired_end_run? # (@config[:paired_end] == "true")

        ###
        # Create symlinks from subpart_dir into unaligned dir
        ###
        if @config[:platform] != "miseq"

          ###
          # Convert BCL files to FASTQ.
          ###
          if @config[:starting_data_type] == "base_calls_bcl"
            dependency = prepare_bcl_converter_job(sjm, lane, unaligned_lane_dir,
                                                   status_bcl_started_job_name)
          else
            throw "starting data type of #{@config[:starting_data_type]} not supported"
          end

          # Link output of BCL conversion to our subpart dir.
          link_cmd = "link_unaligned_fastqs.py"
          link_cmd += " --paired_end" if paired_end_run
          link_cmd += " --verbose" # if @config[:verbose]
          link_cmd += " #{@config[:run_name]}"
          link_cmd += " #{unaligned_lane_dir}"
          link_cmd += " #{subpart_lane_dir}"
        else

          ### BCL conversion already done by MiSeq.

          # Link output of MiSeq run to our subpart dir.
          link_cmd = "link_miseq_fastqs.py"
          link_cmd += " #{@config[:run_name]}"
          link_cmd += " #{@config[:run_dir]}"
          link_cmd += " #{subpart_lane_dir}"
        end

        link_job = Hash.new
        link_job[:name] = "link_fastq_L#{lane}_#{@config[:job_suffix]}"
        link_job[:cmd]  = link_cmd
        link_job[:host] = "localhost"
        link_job[:directory] = @config[:run_dir]
        link_job[:modules]   = @config[:module_bwa_tools]
        link_job[:after] = dependency unless dependency.nil?

        sjm.job(link_job)

        dependency = link_job[:name]

        # Demultiplex the lane, if necessary.
        multiplexed_lane = (@config[:lane][lane][:multiplexed] == "true")
        index_read_lane  = (@config[:lane][lane][:barcode_position] =~ /index_read$/)

        # If we are doing the demultiplexing ourselves, do it here.
        #  O/W, the bcl conversion has already done it.
        if multiplexed_lane and not index_read_lane
          demux_dependency = prepare_multiplexed_lane_analysis(sjm, lane, dependency, subpart_lane_dir)
        else
          demux_dependency = dependency
        end

        # Split the FASTQ files into pf and reject files, and merge the subparts together,
        #  putting the result in out_dir.
        fastq_dependency = prepare_mergesplit_jobs(sjm, lane, demux_dependency,
                                                   outdir_lane_dir, subpart_lane_dir)

        # Run FASTQC on all complete FASTQ files.
        fastqc_dependency_list = []
        ["pf", "reject"].each do |filter|
          fastqc_dependency_list += prepare_fastqc_jobs(sjm, lane, filter, fastq_dependency, outdir_lane_dir)
        end

        ###
        # Set the analysis status to BCL_COMPLETE.
        ###
        status_cmd = "analysis_status.py"
        status_cmd += " --set"
        status_cmd += " --lane #{lane}"
        status_cmd += " #{@config[:run_dir]}"
        status_cmd += " BCL_COMPLETE"

        status_bcl_complete_job_name = "status_bcl_complete_L#{lane}_#{@config[:job_suffix]}"

        status_job = Hash.new()
        status_job[:name] = status_bcl_complete_job_name
        status_job[:cmd]  = status_cmd
        status_job[:host] = "localhost"
        status_job[:modules] = @config[:module_rundir]
        status_job[:after] = fastqc_dependency_list

        sjm.job(status_job)

        # Run BWA, if requested, as soon as FASTQs are ready.
        if map_lane? lane

          if @config[:run_bwa]
            prepare_bwa(sjm, lane, status_bcl_complete_job_name,
                        @config[:subpart_dir])
          end
        else
          # We will run publish now, because BWA won't run it.
          prepare_publish(sjm, lane, status_bcl_complete_job_name)
        end

      end  # define_jobs

    end  # lane_list.each

  end

  def prepare_bcl_converter_job(sjm, lane, unaligned_lane_dir, dependency)

    bcl_job_name = "unpack_bcl_L#{lane}_#{@config[:job_suffix]}"

    bcl_job = Hash.new()
    bcl_job[:name] = bcl_job_name
    bcl_job[:cmd]  = "gap_make -j 4"
    bcl_job[:directory] = unaligned_lane_dir
    bcl_job[:modules] = @config[:module_illumina_tools]
    bcl_job[:slots] = 4
    bcl_job[:after] = dependency
    bcl_job[:memory] = "1G"

    sjm.job(bcl_job)

    return bcl_job_name
  end


  def prepare_multiplexed_lane_analysis(sjm, lane, dependency, subpart_dir)

    # find the barcodes
    barcodes = find_barcodes(lane)
    return if barcodes.size == 0

    # process each of the fastq files for this lane
    opts = {
      :sjm => sjm,
      :barcodes => barcodes,
      :barcode_dir => subpart_dir,
      :lane => lane,
      :dependency => dependency,
    }
    if paired_end_run?
      throw "paired-end barcoded samples not supported"
    else
      return analyze_multiplexed_fastq(opts)
    end
  end

  # define analysis jobs for a set of internal barcodes
  # (not used for index reads)
  def analyze_multiplexed_fastq(opts)

    sjm = opts[:sjm]
    lane = opts[:lane]
    barcodes = opts[:barcodes]

    multiplexed_lane = (@config[:lane][lane][:multiplexed] == "true")
    if not multiplexed_lane
      log :info, "Lane #{lane} not multiplexed -- no need to demux...skipping"
      return
    end

    run_name    = @config[:run_name]
    out_dir     = @config[:out_dir]
    subpart_dir = @config[:subpart_dir]

    split_prefix = File.join subpart_dir, "L#{lane}", "#{run_name}_L#{lane}"
    split_suffix = "_(\\d+).fastq.gz"

    stats_file  = File.join @config[:analysis_dir], "L#{lane}", "#{run_name}_L#{lane}"
    stats_file += "_barcode_stats.txt"

    # split the reads based on the barcode
    split_cmd = "split_barcodes.py"
    split_cmd += " --barcodes #{barcodes.join(',')}"
    split_cmd += " --decompress"
    split_cmd += " --prefix '#{split_prefix}'"
    split_cmd += " --suffix '#{split_suffix}'"
    split_cmd += " --compress"
    split_cmd += " --position bol"
    split_cmd += " --mismatches 1"
    split_cmd += " --strip"
    split_cmd += " --stats #{stats_file}"
    split_cmd += " --tmpdir #{opts[:barcode_dir]}"
    split_cmd += " --verbose" # if @config[:verbose]

    split_job_name = "demux_L#{lane}_#{@config[:job_suffix]}"

    split_job = Hash.new
    split_job[:name] = split_job_name
    split_job[:cmd]  = split_cmd
    split_job[:modules] = [ @config[:module_bwa_tools], @config[:module_fastx_toolkit] ]
    split_job[:group] = "demux_L#{lane}"
    split_job[:after] = opts[:dependency]

    sjm.job(split_job)

    return split_job_name

  end

  def prepare_mergesplit_jobs(sjm, lane, dependency, out_dir, subpart_dir)

    lp = @config[:lane][lane]
    multiplexed_lane = (lp[:multiplexed] == "true")
    index_read_lane  = (lp[:barcode_position] =~ /index_read$/)

    # Get the barcodes for this lane.
    barcodes = []
    if multiplexed_lane
      # Find the barcodes for this lane, if any.
      barcodes = find_barcodes(lane)
      barcodes << "unmatched"
    else
      # Add a no-barcode index to the list for the non-multiplexed lanes.
      barcodes << "NoIndex"
    end

    # Get list of read numbers to look for.
    paired_end_run = paired_end_run? # (@config[:paired_end] == "true")
    if paired_end_run
       read_number_list = [1,2]
    else
       read_number_list = [1]
    end

    run_name = @config[:run_name]

    analysis_lane_dir = File.join(@config[:analysis_dir], "L#{lane}")

    #
    # Merge the subpart files together to output complete FASTQs
    #  into the out_dir, while splitting the pf reads from the reject reads.
    #
    merge_lane_job_list = []
    read_number_list.each do |read_num|

      # Create a file path to a stats file for all the barcodes if
      # lane is multiplexed.
      if multiplexed_lane
        lane_file_prefix  = "#{run_name}_L#{lane}"
        lane_file_prefix += "_#{read_num}" if read_number_list.length > 1

        lane_stats_file = lane_file_prefix + "_seq_stats.txt"
        lane_stats_path = File.join(analysis_lane_dir, lane_stats_file)
      end

      merge_job_list = []
      stats_path_list = []
      barcodes.each do |barcode|

        files_prefix = "#{run_name}_L#{lane}"
        files_prefix += "_#{barcode}"  if barcode != "NoIndex"
        files_prefix += "_#{read_num}" if read_number_list.length > 1

        # FASTQ files to be merged/split into the Archive dir are in subpart_dir.
        fastq_pattern = File.join(subpart_dir, files_prefix)
        fastq_pattern += "_(\\d+).fastq.gz"

        pass_file  = files_prefix + "_pf.fastq.gz"
        rej_file   = files_prefix + "_reject.fastq.gz"
        stats_file = files_prefix + "_seq_stats.txt"

        pass_path  = File.join(out_dir, pass_file)
        rej_path   = File.join(out_dir, rej_file)
        stats_path = File.join(analysis_lane_dir, stats_file)

        # Save the stats_paths in a list if this lane is index reads.
        stats_path_list << stats_path if multiplexed_lane

        fastq_cmd = "merge_split_fastq.rb"
        fastq_cmd += " --out_prefix #{files_prefix}"
        fastq_cmd += " --pass   #{pass_path}"
        fastq_cmd += " --reject #{rej_path}"
        fastq_cmd += " --stats  #{stats_path}"
        fastq_cmd += " --pass_dir   #{subpart_dir}"
        fastq_cmd += " --reject_dir #{subpart_dir}"
        fastq_cmd += " --stats_dir  #{analysis_lane_dir}"
        fastq_cmd += " --compress"
        #fastq_cmd += " --remove_spaces"
        fastq_cmd += " --save_subfiles"
        fastq_cmd += " '#{fastq_pattern}'"

        merge_jobname = "mergesplit_L#{lane}"
        merge_jobname += "_#{barcode}"   if barcode != "NoIndex"
        merge_jobname += "_R#{read_num}" if read_number_list.length > 1
        merge_jobname += "_#{@config[:job_suffix]}"

        merge_job = Hash.new
        merge_job[:name] = merge_jobname
        merge_job[:cmd]  = fastq_cmd
        merge_job[:directory] = subpart_dir
        merge_job[:modules] = @config[:module_illumina_tools]
        merge_job[:after] = dependency
        merge_job[:group] = "merge_L#{lane}_#{@config[:job_suffix]}"

        sjm.job(merge_job)

        merge_job_list << merge_jobname

      end # barcodes.each

      # For multiplexed lanes, run a script to merge the statistics
      #  from the barcode seq_stats.txt files into one for the lane.
      if multiplexed_lane

        merge_seq_stats_cmd = "merge_seq_stats.py"
        merge_seq_stats_cmd += " --out_file #{lane_stats_path}"
        merge_seq_stats_cmd += " --verbose" # if @config[:verbose]
        merge_seq_stats_cmd += " " + stats_path_list.join(" ")

        merge_seq_stats_jobname = "merge_seq_stats_L#{lane}"
        merge_seq_stats_jobname += "_R#{read_num}" if read_number_list.length > 1
        merge_seq_stats_jobname += "_#{@config[:job_suffix]}"

        merge_seq_stats_job = Hash.new
        merge_seq_stats_job[:name] = merge_seq_stats_jobname
        merge_seq_stats_job[:cmd]  = merge_seq_stats_cmd
        merge_seq_stats_job[:modules] = @config[:module_bwa_tools]
        merge_seq_stats_job[:after] = merge_job_list

        sjm.job(merge_seq_stats_job)

        merge_lane_job_list << merge_seq_stats_jobname
      else
        merge_lane_job_list += merge_job_list
      end  # if multiplexed_lane (merge stats files)

    end # read_number_list.each

    return merge_lane_job_list

  end


  def prepare_fastqc_jobs(sjm, lane, filter, dependency, out_dir)

    fastqc_job_memory = "3G"
    fastqc_deps = []

    run_name = @config[:run_name]

    # Get list of read numbers to look for.
    paired_end_run = paired_end_run? # (@config[:paired_end] == "true")
    if paired_end_run
       read_number_list = [1,2]
    else
       read_number_list = [1]
    end

    lp = @config[:lane][lane]
    multiplexed_lane = (lp[:multiplexed] == "true")
    #index_read_lane  = (lp[:barcode_position] =~ /index_read$/)

    # Do fastqc for pf and reject files for lane, if no demux or custom barcode.
    if not multiplexed_lane

      read_number_list.each do |read_num|
        fastq_file_prefix  = "#{run_name}"

        fastq_file_suffix  = "L#{lane}"
        fastq_file_suffix += "_#{read_num}" if read_number_list.length > 1
        fastq_file_suffix += "_#{filter}"

        fastq_file = "#{fastq_file_prefix}_#{fastq_file_suffix}.fastq.gz"
        fastq_path = File.join(out_dir, fastq_file)

        fastq_output_zipfile = "#{fastq_file_prefix}_#{fastq_file_suffix}_fastqc.zip"
        fastq_output_zippath = File.join(out_dir, fastq_output_zipfile)

        fastqc_cmd = "fastqc #{fastq_path} ; rm -f #{fastq_output_zippath}"

        fastqc_job_name = "fastqc_#{fastq_file_suffix}_#{@config[:job_suffix]}"

        fastqc_job = Hash.new()
        fastqc_job[:name] = fastqc_job_name
        fastqc_job[:cmd]  = fastqc_cmd
        fastqc_job[:memory] = fastqc_job_memory
        fastqc_job[:modules] = ["java", @config[:module_fastqc]]
        fastqc_job[:group]  = "fastqc_L#{lane}"
        fastqc_job[:after]  = dependency

        sjm.job(fastqc_job)

        fastqc_deps << fastqc_job_name

      end  # read_number_list.each

    else
      #
      # Do fastqc for barcoded subfiles for lane.
      #

      # Find the barcodes for this lane, if any.
      barcodes = find_barcodes(lane)
      barcodes << "unmatched"

      barcodes.each do |barcode|
        read_number_list.each do |read_num|
            fastq_file_prefix  = "#{run_name}"

            fastq_file_suffix  = "L#{lane}"
            fastq_file_suffix += "_#{barcode}"
            fastq_file_suffix += "_#{read_num}" if read_number_list.length > 1
            fastq_file_suffix += "_#{filter}"

            fastq_file = "#{fastq_file_prefix}_#{fastq_file_suffix}.fastq.gz"
            fastq_path = File.join(out_dir, fastq_file)

            fastq_output_zipfile = "#{fastq_file_prefix}_#{fastq_file_suffix}_fastqc.zip"
            fastq_output_zippath = File.join(out_dir, fastq_output_zipfile)

            fastqc_cmd = "fastqc #{fastq_path} ; rm -f #{fastq_output_zippath}"

            merge_dependency = "mergesplit_L#{lane}_#{barcode}"
            merge_dependency += "_R#{read_num}" if read_number_list.length > 1
            merge_dependency += "_#{@config[:job_suffix]}"

            fastqc_job_name = "fastqc_#{fastq_file_suffix}_#{@config[:job_suffix]}"

            fastqc_job = Hash.new()
            fastqc_job[:name] = fastqc_job_name
            fastqc_job[:cmd]  = fastqc_cmd
            fastqc_job[:memory] = fastqc_job_memory
            fastqc_job[:modules] = ["java", @config[:module_fastqc]]
            fastqc_job[:group]  = "fastqc_L#{lane}"
            fastqc_job[:after]  = merge_dependency

            sjm.job(fastqc_job)

            fastqc_deps << fastqc_job_name

        end  # read_number_list.each
      end  # barcodes.each

    end  #if not multiplexed lane

    return fastqc_deps
  end

  def prepare_bwa(sjm, lane, dependency,
                  subpart_dir)

    #
    # Create BWA job.
    #
    bwa_cmd = init_apf_cmd()
    bwa_cmd += "align_bwa --params #{@config[:stored_params_file]}"
    #bwa_cmd += " --temp_dir #{subpart_dir}"
    bwa_cmd += " --src_dir #{subpart_dir}"
    bwa_cmd += " --lanes #{lane}"
    #bwa_cmd += " --rerun" if @config[:rerun] == "true"
    #bwa_cmd += " --dev" if @dev
    #bwa_cmd += " --force" if @force

    bwa_job_name = "bwa_master_L#{lane}_#{@config[:job_suffix]}"

    bwa_job = Hash.new
    bwa_job[:name] = bwa_job_name
    bwa_job[:cmd]  = bwa_cmd
    bwa_job[:host] = "localhost"
    bwa_job[:modules] = [@config[:module_sjm], @config[:module_limshostenv], @config[:module_apf], @config[:module_apf_pipelines], @config[:module_illumina_tools]]
    bwa_job[:directory] = @config[:analysis_dir]
    bwa_job[:after] = dependency

    sjm.job(bwa_job)

    return bwa_job_name
  end


  # create the samplesheet file
  def configure_samplesheet(samplesheet, lane_list)

    log :info, "Storing samplesheet in #{samplesheet}"
    die "cannot overwrite #{samplesheet}" if File::exists?(samplesheet)
    begin
      out_file = File.new(samplesheet, "w")
    rescue Exception => err
      die "cannot open #{samplesheet}: #{err.to_s}"
    end

    # Output field headers.
    out_file.puts("FCID,Lane,SampleID,SampleRef,Index," +
                  "Description,Control,Recipe,Operator,Project")
    lane_list.each do |lane_num|

      lp = @config[:lane][lane_num]

      multiplexed_lane = (lp[:multiplexed] == "true")
      index_read_lane  = (lp[:barcode_position] =~ /index_read$/)
      dual_index_lane  = (lp[:barcode_position] =~ /dual_index_read$/)

      if multiplexed_lane && index_read_lane
        barcodes = find_barcodes(lane_num, :with_metadata => true)
      else
        barcodes = [:codepoint => '']
      end

      if @config[:control_lane] == lane_num
        control = 'Y'
      else
        control = 'N'
      end

      barcodes.each do |bcinfo|
        #                       FCID              Lane      SampleID
        out_file.print "#{@config[:flow_cell]},#{lane_num},lane#{lane_num},"
        #                 SampleRef
        if bcinfo[:codepoint] != ''
          out_file.print "lane#{lane_num}_#{bcinfo[:codepoint]}_ref,"
        else
          out_file.print "lane#{lane_num}_ref,"
        end
        #                Index               Desc,Control,Recipe,Operator,Project
        out_file.print "#{bcinfo[:codepoint]},na,#{control},na,na,#{@config[:flow_cell]}\n"
      end # barcodes.each

      # Create a "NoIndex" barcode for the index read runs.
      if multiplexed_lane && index_read_lane
        #               FCID                   Lane        SampleID        SampleRef
        out_file.print "#{@config[:flow_cell]},#{lane_num},lane#{lane_num},unknown,"
        #                Index  Desc                                    Control,Recipe,Operator,Project
        out_file.print "Undetermined,Unmatched barcodes for lane #{lane_num},#{control},na,na,#{@config[:flow_cell]}\n"
      end

    end # lane_list.each

    out_file.close
  end


  #def get_min_barcode_length(lane_list)
  #
  #  min_barcode_length = nil
  #  discrepancy = false
  #
  #  lane_list.each do |lane|
  #    lane_barcode_length = nil
  #    barcode_list = find_barcodes lane
  #    next if barcode_list.length == 0
  #    barcode_list.each do |barcode|
  #      if lane_barcode_length.nil?
  #        lane_barcode_length = barcode.length
  #      elsif barcode.length != lane_barcode_length
  #        warn "Lane #{lane} has differing barcode length #{barcode.length} (#{barcode}) from lane prevailing length #{lane_barcode_length}."
  #        discrepancy = true
  #      end
  #    end
  #    if min_barcode_length.nil?
  #      min_barcode_length = lane_barcode_length
  #    elsif min_barcode_length != lane_barcode_length
  #      warn "Lane #{lane} has differing barcode length #{lane_barcode_length} from prevailing length #{min_barcode_length}."
  #    end
  #    # Save the new barcode length if it is shorter than the last one we found.
  #    min_barcode_length = lane_barcode_length if lane_barcode_length < min_barcode_length
  #  end
  #
  #  if discrepancy
  #    return nil
  #  else
  #    return min_barcode_length
  #  end
  #
  #end

  # Get the length of the barcodes associated with a lane.
  # Return nil if these lengths are not all the same.
  def get_barcode_length(lane, index_num = 0)

    discrepancy = false
    lane_barcode_length = nil
    barcode_list = find_barcodes lane ##defined in IlluminaManager
    barcode_list.each do |barcode_indices|
      indices = barcode_indices.split("-")

      if not indices.nil? and indices.length > index_num
        barcode = indices[index_num]
      else
        return nil
      end
      if lane_barcode_length.nil?
        lane_barcode_length = barcode.length
      elsif barcode.length != lane_barcode_length
        warn "get_barcode_length(): Lane #{lane} has differing barcode length #{barcode.length} (#{barcode}) from lane prevailing length #{lane_barcode_length}."
        discrepancy = true
      end
    end

    if discrepancy
      return nil
    else
      return lane_barcode_length
    end
  end

  def calculate_use_bases_mask(lane, paired_end_run, index_read_run, dual_index_run)

    # Start with single read.
    use_bases_mask_list = ["Y*"]

    if index_read_run
      if dual_index_run
        index_list = [0,1]
      else
        index_list = [0]
      end

      index_list.each do |index_num|
        index_mask = calculate_index_mask(lane, index_num)
        if not index_mask.nil?
          use_bases_mask_list << index_mask
        else
          use_bases_mask_list << "n*"
        end
      end
    end

    # Add paired end read2, if necessary.
    if paired_end_run
      use_bases_mask_list << "Y*"
    elsif @config[:paired_end] == "true" and @config[:read1_only]
      # Ignore read2.
      use_bases_mask_list << "n*"
    end

    return use_bases_mask_list.join(",")
  end

  def calculate_index_mask(lane, index_num)

    # Compute barcode length for the lane.
    barcode_length = get_barcode_length lane, index_num
    return nil if barcode_length.nil?

    if index_num == 0
      index_length = @config[:index1_cycles].to_i
    elsif index_num == 1
      index_length = @config[:index2_cycles].to_i
    else
      warn "calc_index_mask(): index_num not either 0 or 1: returning nil"
      return nil
    end

    # Compare the barcode lengths used in the lanes with the index length used for the run.
    if index_length == 7  # version one
      if barcode_length == 6
        index_mask = "IIIIIIn"
      else
        warn "calc_index_mask(): Barcode length of lanes #{barcode_length} does not match index1 cycles of #{index_length}."
        return nil
      end
    elsif index_length == 8  # nextera, version two
      if barcode_length == 8
        index_mask = "I*"
      elsif barcode_length == 6  # Version one barcodes used on Version two run.
        index_mask = "IIIIIInn"
      elsif barcode_length == 4  # Weird barcodes.
        index_mask = "IIIInnnn"
      else
        warn "calc_index_mask(): Barcode length of lanes #{barcode_length} does not match index1 cycles of #{index_length}."
        return nil
      end
    else
      warn "calc_index_mask(): index length #{index_length} unknown: using default use_bases_mask (I*)"
      index_mask = "I*"
    end

    return index_mask
  end


end
