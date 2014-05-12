#!/usr/bin/env ruby

#
# publish_illumina_results.rb: create an HTML document with Illumina
# sequencing run results
#
# Phil Lacroute
#

require 'csv'
require 'optparse'

class PublishIlluminaResults

  def initialize
    @out_dir = "."
    @config = Hash.new
    @bwa = true
    @eland = false
    @fastq_only = false
  end

  ################################################################
  # Command-Line Options
  ################################################################

  ARCHIVE_ROOT = "/srv/gs1/projects/scg/Archive/IlluminaRuns"
  URL_ROOT = "http://scg-data.stanford.edu/Archive/IlluminaRuns"

  MONTH_NAMES = {
    "01" => "jan",
    "02" => "feb",
    "03" => "mar",
    "04" => "apr",
    "05" => "may",
    "06" => "jun",
    "07" => "jul",
    "08" => "aug",
    "09" => "sep",
    "10" => "oct",
    "11" => "nov",
    "12" => "dec"
  }

  def parse_args
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: publish_illumina_results.rb options"
      opts.separator "Options:"

      opts.on("--run STR", "run name (required)") do |run|
        @run_name = run
      end

      opts.on("--lane NUM", "lane number (required)") do |lane|
        @lane_num = lane.to_i
      end

      opts.on("--out DIR", "output directory",
              "(defaults to current dir)") do |dir|
        @out_dir = dir
      end

      opts.on("--archive DIR", "archive directory for the run",
              "(defaults to standard archive)") do |dir|
        @archive_dir = dir
      end

      opts.on("--config FILE", "config file",
              "(default comes from archive)") do |file|
        @config_file = file
      end

      opts.on("--stats DIR", "directory containing statistics files",
              "(default comes from archive)") do |dir|
        @stats_dir = dir
      end

      opts.on("--interop DIR",
              "Illumina InterOp directory",
              "(default comes from archive)") do |dir|
        @interop_dir = dir
      end

      opts.on("--bam FILE1,FILE2,...", Array,
              "BAM file(s) containing aligned reads ",
              "(default comes from archive)") do |filelist|
        @bam_files = filelist
      end

      opts.on("--eland", "mapping statistics are from eland (default = false)") do
        @eland = true
        @bwa = false
      end

      opts.on("--bwa", "mapping statistics are from bwa (default = true)") do
         @eland = false
         @bwa = true
      end

      opts.on("--fastq_only", "ignore mapping results, if any (default = false)") do
        @fastq_only = true
      end

      opts.on("--noplot", "don't generate the plots") do
        @noplot = true
      end

      opts.on("--force", "Continue past some error conditions") do
         @force = true
      end

      opts.on("--verbose", "print verbose messages") do
        @verbose = true
      end

      opts.on("--debug", "print debug messages") do
        @debug = true
      end

      opts.on_tail("-h", "--help", "print help message") do
        puts opts
        exit
      end
    end

    if ARGV.empty?
      puts opts
      exit
    end

    begin
      opts.parse!(ARGV)
    rescue OptionParser::ParseError => err
      STDERR.puts err.to_s
      exit 1
    end

    if ARGV.size > 0
      STDERR.puts "error: unexpected arguments"
      exit 1
    end

    if @run_name.nil?
      STDERR.puts "error: --run is required"
      exit 1
    end

    if @lane_num.nil?
      STDERR.puts "error: --lane is required"
      exit 1
    end

    year = @run_name[0..1].to_i + 2000
    month = MONTH_NAMES[@run_name[2..3]]
    run_dir = "#{year}/#{month}/#{@run_name}"
    @run_url = "#{URL_ROOT}/#{year}/#{month}/#{@run_name}"
    if @archive_dir
      @data_dir = @archive_dir
    else
      @data_dir = "#{ARCHIVE_ROOT}/#{run_dir}"
    end
    @lane_dir = "#{@data_dir}/L#{@lane_num}"
    @lane_dir = @data_dir unless File.exists?(@lane_dir)

    @config_file = "#{@data_dir}/config.txt" if @config_file.nil?
    @stats_dir = @lane_dir if @stats_dir.nil?
    @interop_dir = "#{@data_dir}/InterOp" if @interop_dir.nil?
  end

  ################################################################
  # Config File Parsing
  ################################################################

  def load_config(filename)
    puts "Loading file #{filename}..." if @verbose
    IO.foreach(filename) do |line|
      fields = line.split(/ /, 2)
      raise "invalid line in #{filename}: #{line}" if
        fields.length == 0 || blank?(fields[0])
      if fields.length == 1
        value = nil
      else
        value = fields[1].chomp
      end
      set_param fields[0], value
    end
  end

  # set the value of a parameter specified with a hierarchical path
  # (consisting of components separated by colons)
  # opts can include:
  #   :config => subconfig        specify a subtree of @config
  #   :no_overwrite => true       don't overwrite existing values
  def set_param(param, value, opts = {})
    config = opts[:config] || @config
    subconfig = config
    component = nil
    param.split(':').each do |next_component|
      if !component.nil?
        # find or create a level of hierarchy
        subconfig[component] = Hash.new if subconfig[component].nil?
        subconfig = subconfig[component]
        raise "invalid components after #{component} in param #{param}" unless
          subconfig.is_a?(Hash)
      end

      # construct the next index which is either a number or a symbol
      if next_component =~ /^\d+$/
        component = next_component.to_i
      else
        component = next_component.to_sym
      end
    end
    oldvalue = subconfig[component]
    raise "incomplete parameter path: #{param}" if oldvalue.is_a?(Hash)
    if blank?(oldvalue) || !opts[:no_overwrite]
      subconfig[component] = value
    end
  end

  def paired_end?
    @config[:paired_end] == "true" and not (@config[:read1_only] == "true")
  end

  def index_read?
    @config[:index_read] == "true"
  end

  def multiplexed?
    @config[:lane][@lane_num][:multiplexed] == "true"
  end

  def mapped?
    @config[:gerald][0][:lane][@lane_num][:analysis_type] == "map" and not @fastq_only
  end

  ################################################################
  # Stats File Parsing
  ################################################################

  def load_stats
    if paired_end?
      read1_stats = load_lane_stats(@lane_num, 1)
      read2_stats = load_lane_stats(@lane_num, 2)
      if !blank?(read1_stats["Post-Filter Unique 0mm"])
        pair_stats = load_pair_stats_file(@lane_num)
        pair_stats[:bcstats] = {}
      else
        pair_stats = {}
        pair_stats[:bcstats] = {}
        read1_stats[:barcodes].each do |barcode|
          if !blank?(read1_stats[:bcstats][barcode]["Post-Filter Unique 0mm"])
            pair_stats[:bcstats][barcode] =
              load_pair_stats_file(@lane_num, barcode)
          end
        end
      end
        
      @stats = {
        :read1_stats => read1_stats,
        :read2_stats => read2_stats,
        :pair_stats => pair_stats
      }
    else
      @stats = {
        :read1_stats => load_lane_stats(@lane_num)
      }
    end

    @barcodes = Array.new(@stats[:read1_stats][:barcodes])
    @barcodes.push "unmatched" unless @barcodes.empty?
  end

  def load_lane_stats(lane, read_number = nil)
    lane_stats = parse_stats_file(stats_filename(:lane => lane,
                                                 :read => read_number))
    compute_derived_stats(lane_stats)
    if lane_stats["Flow Cell"].nil?
      run_fields = lane_stats["Run"].split("_")
      lane_stats["Flow Cell"] = run_fields[-1]
    end

    lane_stats[:bcstats] = {}
    lane_stats[:barcodes].each do |barcode|
      bcstats = parse_stats_file(stats_filename(:lane => lane,
                                                :read => read_number,
                                                :barcode => barcode))
      compute_derived_stats(bcstats)
      lane_stats[:bcstats][barcode] = bcstats
    end

    lane_stats
  end

  def compute_derived_stats(stats)
    if stats["Failed Reads"].nil?
      stats["Failed Reads"] =
        stats["Total Reads"].to_i - stats["Post-Filter Reads"].to_i
    end

    if @eland
      # for compatibility with old-style Eland stats files, add the
      # "repetitive" statistic (if it exists) to the "non-unique" statistic
      compute_stat(stats, "Post-Filter Non-Unique",
                   [ "Post-Filter Non-Unique",
                     "Post-Filter Repetitive" ],
                   true)
      compute_stat(stats, "Post-Filter Non-Unique 0mm",
                   [ "Post-Filter Non-Unique 0mm",
                     "Post-Filter Repetitive 0mm" ],
                   true)
      compute_stat(stats, "Post-Filter Non-Unique 1mm",
                   [ "Post-Filter Non-Unique 1mm",
                     "Post-Filter Repetitive 1mm" ],
                   true)
      compute_stat(stats, "Post-Filter Non-Unique 2mm",
                   [ "Post-Filter Non-Unique 2mm",
                     "Post-Filter Repetitive 2mm" ],
                   true)

      compute_stat(stats, "Post-Filter Unclassified",
                   [ "Post-Filter Too-Many-Ns",
                     "Post-Filter Repeat-Masked" ])
    end

    unique_categories = [ "Post-Filter Unique 0mm",
                          "Post-Filter Unique 1mm",
                          "Post-Filter Unique 2mm" ]
    nonunique_categories = [ "Post-Filter Non-Unique 0mm",
                             "Post-Filter Non-Unique 1mm",
                             "Post-Filter Non-Unique 2mm" ]
    # HACK?: should I have "3+mm" in categories here?
    if @bwa
      unique_categories << "Post-Filter Unique 3+mm"
      unique_categories << "Post-Filter Unique w/Indel"

      nonunique_categories << "Post-Filter Non-Unique 3+mm"
      nonunique_categories << "Post-Filter Non-Unique w/Indel"
    end

    compute_stat(stats, "Post-Filter Unique",
                 unique_categories)
    compute_stat(stats, "Post-Filter Non-Unique",
                 nonunique_categories)

    compute_stat(stats, "Post-Filter Mapped",
                 [ "Post-Filter Unique", 
                   "Post-Filter Non-Unique" ])

  end

  # compute the statistic identified by label as the sum of the
  # statistics in components (an array of labels)
  def compute_stat(stats, label, components, overwrite = false)
    return unless stats[label].nil? || overwrite
    value = 0
    found = false
    components.each do |comp|
      next if stats[comp].nil?
      value = value + stats[comp].to_i
      found = true
    end
    if found
      stats[label] = value
      puts "Computed statistic #{label}: #{value}" if @verbose
    end
  end

  def load_pair_stats_file(lane, barcode = nil)
    parse_stats_file(stats_filename(:lane => lane, :barcode => barcode,
                                    :read => :pair))
  end

  def stats_filename(opts)
    filename = @lane_dir + "/#{@run_name}_L#{opts[:lane]}"
    filename += "_#{opts[:barcode]}" unless opts[:barcode].nil?
    if opts[:read] == :pair
      filename += "_pair_stats.txt"
    else
      filename += "_#{opts[:read]}" unless opts[:read].nil?
      filename += "_stats.txt"
    end
    filename
  end

  def parse_stats_file(filename)
    puts "Loading file #{filename}..." if @verbose
    stats = Hash.new
    stats[:barcodes] = Array.new
    IO.foreach(filename) do |line|
      if line =~ /^([^:]+):\s+(.*)$/
        key = $1
        value = $2
        stats[key] = value
        if key =~ /^Post-Filter ([ACGT-]+)$/
          stats[:barcodes].push $1
        end
      else
        die "#{filename}: parse error on line #{$.}"
      end
    end
    stats
  end

  ################################################################
  # Plot Generation
  ################################################################

  def make_plots
    # set @bam_files if necessary
    if @bam_files.nil? && mapped?
      @bam_files = []
      filebase = "#{@lane_dir}/#{@run_name}_L#{@lane_num}"
      if multiplexed?
        @barcodes.each do |barcode|
          next if barcode == "unmatched"
          barcode_bam_file = "#{filebase}_#{barcode}_pf.bam"
          if not File.exists? barcode_bam_file
            STDERR.puts "Expected BAM file #{barcode_bam_file} does not exist, skipping."
            next
          else
            @bam_files.push barcode_bam_file
          end
        end
      else
        bam_file = "#{filebase}_pf.bam"
        if not File.exists? bam_file
          STDERR.puts "Expected BAM file #{bam_file} does not exist, skipping."
        else
          @bam_files.push bam_file
        end
      end
      warn "empty BAM file list?" if @bam_files.empty?
    end

    # if there is more than one read then make a list of read lengths
    if paired_end? || index_read?
      @read_len = Array.new
      @read_len.push @config[:read1_cycles]
      if index_read?
        if @config[:index_cycles].nil?
          @read_len.push 7
        else
          @read_len.push @config[:index_cycles]
        end
      end
      @read_len.push @config[:read2_cycles] if paired_end?
    end

    make_interop_plots
    make_bam_plots
  end

  def make_interop_plots
    cmd = ("illumina_intensities.rb" +
           " --extraction #{@interop_dir}/ExtractionMetricsOut.bin" +
           " --corrected_int #{@interop_dir}/CorrectedIntMetricsOut.bin" +
           " --raw_summary_plot #{outfile_base}_raw_int_summary.png" +
           " --raw_details_plot #{outfile_base}_raw_int_details.png" +
           " --corr_summary_plot #{outfile_base}_int_summary.png" +
           " --corr_details_plot #{outfile_base}_int_details.png" +
           " --call_summary_plot #{outfile_base}_call_summary.png" +
           " --call_details_plot #{outfile_base}_call_details.png" +
           " --focus_summary_plot #{outfile_base}_focus_summary.png" +
           " --lane #{@lane_num}")
    cmd += " --read_lengths #{@read_len.join(',')}" unless @read_len.nil?
    cmd += " --verbose" if @verbose
    cmd += " --debug" if @debug
    cmd += " --force" if @force
    puts "Running command: #{cmd}" if @verbose
    if !system(cmd)
      STDERR.puts "error making intensity plots"
      exit 1
    end

    cmd = ("illumina_qscores.rb" +
           " --qmetrics #{@interop_dir}/QMetricsOut.bin" +
           " --details_plot #{outfile_base}_qual_details.png" +
           " --summary_plot #{outfile_base}_qual_summary.png" +
           " --lane #{@lane_num}")
    cmd += " --read_lengths #{@read_len.join(',')}" unless @read_len.nil?
    cmd += " --verbose" if @verbose
    cmd += " --force" if @force
    puts "Running command: #{cmd}" if @verbose
    if !system(cmd)
      STDERR.puts "error making qscore plots"
      exit 1
    end

    cmd = ("illumina_tile_metrics.rb" +
           " --tile_metrics #{@interop_dir}/TileMetricsOut.bin" +
           " --lane #{@lane_num}" +
           " --stats #{outfile_base}_tile_metrics.txt")
    cmd += " --verbose" if @verbose
    puts "Running command: #{cmd}" if @verbose
    if !system(cmd)
      STDERR.puts "error processing tile metrics"
      exit 1
    end
  end

  def make_bam_plots
    return if @bam_files.nil? or @bam_files.empty?

    cmd = ("illumina_mismatches.rb" +
           " --bam #{@bam_files.join(',')}" +
           " --details_plot #{outfile_base}_mm_details.png" +
           " --summary_plot #{outfile_base}_mm_summary.png")
    cmd += " --read_lengths #{@read_len.join(',')}" unless @read_len.nil?
    cmd += " --verbose" if @verbose
    puts "Running command: #{cmd}" if @verbose
    if !system(cmd)
      STDERR.puts "error making mismatch plots"
      exit 1
    end
  end

  ################################################################
  # HTML File Generation
  ################################################################

  SECTION_TITLES = {
    "stats" => "Sequencing Statistics",
    "data" => "Data Files",
    "mismatch" => "Mismatches vs Read Cycle",
    "quality" => "Quality Score vs Read Cycle",
    "calls" => "Base Call Composition vs Read Cycle",
    "intensity" => "Image Intensity vs Read Cycle",
    "raw" => "Raw Image Intensity vs Read Cycle",
    "focus" => "Focus Metric (FWHM) vs Read Cycle",
    "tile_metrics" => "Tile Metrics"
  }

  def make_html
    write_results_file
    write_details_file
    write_diags_file
  end

  def write_results_file
    puts "Writing HTML file #{results_html}..." if @verbose
    puts "Writing CSV file #{results_csv}..." if @verbose

    title = "Results for #{@run_name} Lane #{@lane_num}"
    @html = File.new(results_html, "w")
    csv_ios = File.new(results_csv, "w")
    @csv = CSV::Writer.generate(csv_ios)

    html_prolog(title)
    show_contents
    show_stats
    show_data_files
    show_plot_links
    html_epilog

    @html.close
    csv_ios.close

    @html = nil
    @csv = nil
  end

  def show_contents
    @html.puts "      <h3>Contents</h3>"
    begin_contents
    contents_entry("stats")
    contents_entry("data")
    if !@noplot
      contents_entry("mismatch") unless @bam_files.nil?
      contents_entry("quality")
      contents_entry("calls")
      contents_entry("intensity")
    end
    end_contents
  end

  def html_prolog(title)
    @html.puts '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"'
    @html.puts '"http://www.w3.org/TR/html4/strict.dtd">'
    @html.puts '<html>'
    @html.puts '   <head>'
    @html.puts "      <title>#{title}</title>"
    @html.puts "      <style type=\"text/css\">"
    @html.puts "        * {font-family:Arial,Helvetica,sans-serif;}"
    @html.puts "      </style>"
    @html.puts '   </head>'
    @html.puts '   <body>'
    @html.puts "      <h2>#{title}</h2>"
  end

  def html_epilog
    @html.puts '   </body>'
    @html.puts '</html>'
  end

  def begin_contents
    @html.puts "      <ol>"
  end

  def contents_entry(section, opts = {})
    title = SECTION_TITLES[section]
    @html.puts "      <li><a href=\"##{section}\">#{title}</a></li>"
  end

  def end_contents
    @html.puts "      </ol>"
  end

  def begin_section(section, opts = {})
    title = SECTION_TITLES[section]
    title += " #{opts[:title_suffix]}" unless opts[:title_suffix].nil?
    @html.puts "      <a name=\"#{section}\"><h3>#{title}</h3></a>"
    @html.puts "      <p>"
  end

  def end_section
    @html.puts "      </p>"
  end

  def begin_table
    @html.puts "<table border=\"1\" cellspacing=\"0\" cellpadding=\"4\">"
  end

  def end_table
    @html.puts "</table>"
  end

  def begin_row
    @html_data = Array.new
    @csv_data = Array.new
  end

  def table_cell(value, opts = {})
    align = opts[:align]

    case opts[:type]
    when :numeric
      cell = {:value => commify(value)}
      align = "right" if align.nil?
    else
      cell = {:value => value}
    end

    cell[:align] = align unless align.nil?

    @html_data.push(opts[:html] || cell) unless opts[:html] == :skip
    @csv_data.push(opts[:csv] || cell) unless opts[:csv] == :skip
  end

  def end_row
    @html.puts "<tr>"
    @html_data.each do |field|
      attrib = ""
      value = field[:value]
      attrib += " align=#{field[:align]}" unless field[:align].nil?
      @html.puts "<td#{attrib}>#{value}</td>"
    end
    @html.puts "</tr>"

    @csv << @csv_data.collect {|cell| cell[:value]} unless @csv.nil?
  end

  def table_row(values, opts = {})
    begin_row
    values.each {|value| table_cell value, opts}
    end_row
  end

  def commify(number, delimiter = ',')
    number.to_s.reverse.
      gsub(%r{([0-9]{3}(?=([0-9])))}, "\\1#{delimiter}").reverse
  end

  def compute_pct(value, denom)
    return 0 if denom == 0
    "%.1f" % (value.to_f * 100.0 / denom.to_f)
  end

  def outfile_base
    "#{@out_dir}/#{@run_name}_L#{@lane_num}"
  end

  def results_html
    "#{outfile_base}_results.html"
  end

  def results_csv
    "#{outfile_base}_stats.csv"
  end

  def details_html
    "#{outfile_base}_details.html"
  end

  def diags_html
    "#{outfile_base}_diags.html"
  end

  def details_url(section)
    "#{@run_name}_L#{@lane_num}_details.html##{section}"
  end

  ################################################################
  # HTML File Generation, Statistics
  ################################################################

  READ_STATS = [
                { :name => "Reads" },
                { :name => "Mapped", :denom => "Reads" },
                { :name => "Unique", :denom => "Reads" },
                { :name => "Unique 0mm", :denom => "Reads" },
                { :name => "Unique 1mm", :denom => "Reads" },
                { :name => "Unique 2mm", :denom => "Reads" },
                { :name => "Unique 3+mm", :denom => "Reads" },
                { :name => "Unique w/Indel", :denom => "Reads" },
                { :name => "Non-Unique", :denom => "Reads" },
                { :name => "Non-Unique 0mm", :denom => "Reads" },
                { :name => "Non-Unique 1mm", :denom => "Reads" },
                { :name => "Non-Unique 2mm", :denom => "Reads" },
                { :name => "Non-Unique 3+mm", :denom => "Reads" },
                { :name => "Non-Unique w/Indel", :denom => "Reads" },
                { :name => "No-Match", :denom => "Reads" },
                { :name => "Contam", :denom => "Reads" },
                { :name => "Unclassified", :denom => "Reads" }
               ]

  def show_stats
    begin_section("stats")
    show_run_stats
    show_sequencing_stats
    show_barcode_stats
    if multiplexed?
      @barcodes.each do |barcode|
        show_mapping_stats(barcode)
      end
    else
      show_mapping_stats
    end
    show_key
    end_section
  end

  def show_key
    @html.puts "<p>"
    @html.puts "Key for the statistics tables:"
    @html.puts "<br />"
    @html.puts "Post-Filter = reads that passed the base-caller's quality filter"
    @html.puts "<br />"
    @html.puts "Failed = reads that failed the base-caller's quality filter"
    @html.puts "<br />"
    @html.puts "Unique = reads that mapped to a single position in the genome"
    @html.puts "<br />"
    @html.puts "Non-Unique = reads that mapped to more than one position"
    @html.puts "<br />"
    @html.puts "No-Match = reads that did not map anywhere"
    @html.puts "<br />"
    @html.puts "0mm = zero mismatches (perfect match to the genome)"
    @html.puts "<br />"
    @html.puts "1mm = one mismatching base"
    @html.puts "<br />"
    @html.puts "2mm = two mismatching bases"
    @html.puts "<br />"
    @html.puts "3+mm = three or more mismatching bases"
    @html.puts "<br />"
    @html.puts "w/Indel = alignment contains an insertion or deletion"
    @html.puts "<br />"
    @html.puts "Contam = reads that match the sequencing linkers"
    @html.puts "<br />"
    @html.puts "Unclassified = read was not mapped"
    if paired_end?
      @html.puts "<br />"
      @html.puts "Consistent Unique Pairs = paired reads where both reads map"
      @html.puts "uniquely and have consistent distance and orientation"
      @html.puts "<br />"
      @html.puts "Rescued Pairs = paired reads where one read maps uniquely"
      @html.puts "and the other read has one consistent position"
      @html.puts "<br />"
      @html.puts "Total Consistent Pairs = Consistent Unique + Rescued Pairs"
    end
    @html.puts "</p>"
  end

  def show_run_stats
    @html.puts "<p>"
    @html.puts "Run Information:"
    @csv << ["Run Information"]
    begin_table
    table_row(["Run Name", @config[:run_name]])
    table_row(["Flow Cell", @config[:flow_cell]])
    table_row(["Lane", @lane_num])
    table_row(["Sample", @config[:lane][@lane_num][:sample_name]])
    table_row(["Submitter", @config[:lane][@lane_num][:submitter]])
    table_row(["Platform", @config[:platform_name]])
    if paired_end?
      run_type = "Paired Reads, "
      if @config[:read1_cycles] == @config[:read2_cycles]
        run_type += "2x#{@config[:read1_cycles]}bp"
      else
        run_type += "#{@config[:read1_cycles]}bp + #{@config[:read2_cycles]}bp"
      end
    else
      run_type = "Single Read, #{@config[:read1_cycles]}bp"
    end
    run_type += " plus Index Read" if index_read?
    table_row(["Run Type", run_type])

    genome = @stats[:read1_stats]["Genome"] || "N/A"
    table_row(["Genome", genome])
    end_table
    @html.puts "</p>"
  end

  def show_sequencing_stats
    @html.puts "<p>"
    @html.puts "Sequencing Results:"
    @csv << []
    @csv << ["Sequencing Results"]

    begin_table

    total_reads = @stats[:read1_stats]["Total Reads"].to_i
    begin_row
    table_cell "Total Reads"
    table_cell total_reads, :type => :numeric
    table_cell ""
    end_row

    pf_reads = @stats[:read1_stats]["Post-Filter Reads"].to_i
    pf_pct = compute_pct(pf_reads, total_reads)
    begin_row
    table_cell "Post-Filter Reads"
    table_cell pf_reads, :type => :numeric
    table_cell "#{pf_pct}% of Total Reads"
    end_row

    fail_reads = @stats[:read1_stats]["Failed Reads"].to_i
    fail_pct = compute_pct(fail_reads, total_reads)
    begin_row
    table_cell "Failed Reads"
    table_cell fail_reads, :type => :numeric
    table_cell "#{fail_pct}% of Total Reads"
    end_row

    if mapped?
      if paired_end?
        mapped1 = get_lane_stat(@stats[:read1_stats], "Post-Filter Mapped")
        mapped_pct1 = compute_pct(mapped1, pf_reads)
        begin_row
        table_cell "Mapped PF Reads (Read 1)"
        table_cell mapped1, :type => :numeric
        table_cell "#{mapped_pct1}% of Post-Filter Reads"
        end_row

        mapped2 = get_lane_stat(@stats[:read2_stats], "Post-Filter Mapped")
        mapped_pct2 = compute_pct(mapped2, pf_reads)
        begin_row
        table_cell "Mapped PF Reads (Read 2)"
        table_cell mapped2, :type => :numeric
        table_cell "#{mapped_pct2}% of Post-Filter Reads"
        end_row

        unique1 = get_lane_stat(@stats[:read1_stats], "Post-Filter Unique")
        unique_pct1 = compute_pct(unique1, pf_reads)
        begin_row
        table_cell "Uniquely-Mapped PF Reads (Read 1)"
        table_cell unique1, :type => :numeric
        table_cell "#{unique_pct1}% of Post-Filter Reads"
        end_row

        unique2 = get_lane_stat(@stats[:read2_stats], "Post-Filter Unique")
        unique_pct2 = compute_pct(unique2, pf_reads)
        begin_row
        table_cell "Uniquely-Mapped PF Reads (Read 2)"
        table_cell unique2, :type => :numeric
        table_cell "#{unique_pct2}% of Post-Filter Reads"
        end_row

        consistent = get_lane_stat(@stats[:pair_stats],
                                   "Total Consistent Pairs")
        consistent_pct = compute_pct(consistent, pf_reads)
        begin_row
        table_cell "Consistent Pairs"
        table_cell consistent, :type => :numeric
        table_cell "#{consistent_pct}% of Post-Filter Reads"
        end_row

        insert_size = get_lane_stat(@stats[:pair_stats], "Median Insert Size",
                                    :average => true)
        begin_row
        table_cell "Insert Size"
        table_cell insert_size, :align => "right"
        table_cell ""
        end_row
      else
        mapped1 = get_lane_stat(@stats[:read1_stats], "Post-Filter Mapped")
        mapped_pct1 = compute_pct(mapped1, pf_reads)
        begin_row
        table_cell "Mapped PF Reads"
        table_cell mapped1, :type => :numeric
        table_cell "#{mapped_pct1}% of Post-Filter Reads"
        end_row

        unique1 = get_lane_stat(@stats[:read1_stats], "Post-Filter Unique")
        unique_pct1 = compute_pct(unique1, pf_reads)
        begin_row
        table_cell "Uniquely-Mapped PF Reads"
        table_cell unique1, :type => :numeric
        table_cell "#{unique_pct1}% of Post-Filter Reads"
        end_row
      end
    end

    end_table
    @html.puts "</p>"
  end

  def get_lane_stat(stats, key, opts = {})
    if multiplexed?
      value = 0
      cnt = 0
      @barcodes.each do |barcode|
        next if barcode == "unmatched"
        value += stats[:bcstats][barcode][key].to_i
        cnt += 1
      end
      value = (value.to_f / cnt.to_f).round.to_i if opts[:average]
    else
      value = stats[key].to_i
    end
    value
  end

  def show_barcode_stats
    return unless multiplexed?

    @html.puts "<p>"
    @html.puts "Barcode Results:"
    @csv << []
    @csv << ["Barcode Results"]
    begin_table

    begin_row
    table_cell "Barcode"
    table_cell "Matching Reads"
    table_cell "% of Total Reads"
    table_cell "Post-Filter Reads"
    table_cell "Failed Reads"
    if mapped?
      if paired_end?
        table_cell "Mapped PF Reads (Read 1)"
        table_cell "Mapped PF Reads (Read 2)"
        table_cell "Uniquely-Mapped PF Reads (Read 1)"
        table_cell "Uniquely-Mapped PF Reads (Read 2)"
        table_cell "Consistent Pairs"
        table_cell "Insert Size"
      else
        table_cell "Mapped PF Reads"
        table_cell "Uniquely-Mapped PF Reads"
      end
    end
    end_row

    total_reads = @stats[:read1_stats]["Total Reads"].to_i
    @barcodes.each do |barcode|
      begin_row
      if barcode == "unmatched" || !mapped?
        table_cell barcode
      else
        link = "<a href=\"#details_#{barcode}\">#{barcode}</a>"
        table_cell(barcode, :html => {:value => link})
      end
      bc_pf_reads = @stats[:read1_stats]["Post-Filter #{barcode}"].to_i
      bc_fail_reads = @stats[:read1_stats]["Failed #{barcode}"].to_i
      bc_total_reads = bc_pf_reads + bc_fail_reads
      table_cell bc_total_reads, :type => :numeric
      table_cell("#{compute_pct(bc_total_reads, total_reads)}%",
                 :align => "right")
      table_cell bc_pf_reads, :type => :numeric
      table_cell bc_fail_reads, :type => :numeric
      if mapped?
        if barcode == "unmatched"
          mapped1 = ""
          unique1 = ""
        else
          bcstats1 = @stats[:read1_stats][:bcstats][barcode]
          mapped1 = bcstats1["Post-Filter Mapped"].to_i
          unique1 = bcstats1["Post-Filter Unique"].to_i
        end
        if paired_end?
          if barcode == "unmatched"
            mapped2 = ""
            unique2 = ""
          else
            bcstats2 = @stats[:read2_stats][:bcstats][barcode]
            mapped2 = bcstats2["Post-Filter Mapped"].to_i
            unique2 = bcstats2["Post-Filter Unique"].to_i
            bcpair_stats = @stats[:pair_stats][:bcstats][barcode]
            consistent = bcpair_stats["Total Consistent Pairs"].to_i
            insert = bcpair_stats["Median Insert Size"].to_i
          end
          table_cell mapped1, :type => :numeric
          table_cell mapped2, :type => :numeric
          table_cell unique1, :type => :numeric
          table_cell unique2, :type => :numeric
          table_cell consistent, :type => :numeric
          table_cell insert, :align => "right"
        else
          table_cell mapped1, :type => :numeric
          table_cell unique1, :type => :numeric
        end
      end
      end_row
    end
    end_table
    @html.puts "</p>"
  end

  def show_mapping_stats(barcode = nil)
    return if barcode == "unmatched"

    if barcode.nil?
      read1_stats = @stats[:read1_stats]
    else
      read1_stats = @stats[:read1_stats][:bcstats][barcode]
    end
    if paired_end?
      if barcode.nil?
        read2_stats = @stats[:read2_stats]
      else
        read2_stats = @stats[:read2_stats][:bcstats][barcode]
      end
    else
      read2_stats = nil
    end
    return if blank?(read1_stats["Post-Filter Unique 0mm"])

    @html.puts "<p>"
    title = "Detailed Alignment Results"
    title += " for Barcode #{barcode}" unless barcode.nil?
    title += ":"
    @html.puts "<a name=\"details_#{barcode}\">" unless barcode.nil?
    @html.puts title
    @html.puts "</a>" unless barcode.nil?
    @csv << []
    @csv << [title]

    begin_table

    begin_row
    table_cell ""
    if read2_stats.nil?
      table_cell "Post-Filter Reads"
      table_cell "% of Post-Filter Reads"
    else
      table_cell "Read 1, Post-Filter"
      table_cell "% of PF Reads"
      table_cell "Read 2, Post-Filter"
      table_cell "% of PF Reads"
    end
    end_row

    READ_STATS.each do |stat_params|
      begin_row
      table_cell stat_params[:name]
      stat_table_cell(stat_params, "Post-Filter", read1_stats)
      stat_table_cell(stat_params, "Post-Filter", read2_stats) unless
        read2_stats.nil?
      end_row
    end
    end_table
  end

  def stat_table_cell(stat_params, filter_class, stats)
    name = "#{filter_class} #{stat_params[:name]}"
    value = stats[name]
    if blank?(value)
      table_cell "N/A", :align => "right"
      table_cell ""
    else
      table_cell value.to_i, :type => :numeric
      denom_name = "#{filter_class} #{stat_params[:denom]}"
      denom = stats[denom_name]
      if !blank?(denom) && denom.to_i != 0
        table_cell "#{compute_pct(value, denom)}%", :align => "right"
      else
        table_cell ""
      end
    end
  end

  ################################################################
  # HTML File Generation, Data Locations
  ################################################################

  PF_FILE_TYPES = [
                { :description => "Unmapped Post-Filter Reads",
                  :format => "FASTQ",
                  :extension => "_pf.fastq",
                  :read_num_specific => true },
                { :description => "Mapped Post-Filter Reads",
                  :format => "BAM",
                  :extension => "_pf.bam",
                  :read_num_specific => false },
                { :description => "Mapped Post-Filter Reads",
                  :format => "Illumina Export",
                  :extension => "_export.txt",
                  :read_num_specific => true },
                { :description => "Mapped Post-Filter Reads",
                  :format => "Eland-Extended",
                  :extension => "_eland_extended_pf.txt",
                  :read_num_specific => true },
                { :description => "Mapped Post-Filter Reads",
                  :format => "Eland-Multi",
                  :extension => "_pf_eland_multi.txt",
                  :read_num_specific => true },
                { :description => "Mapped Post-Filter Reads",
                  :format => "BED",
                  :extension => "_pf.bed",
                  :read_num_specific => true },
                { :description => "Post-Filter Signal",
                  :format => "SGR",
                  :extension => ".sgr",
                  :read_num_specific => true },  # HACK: this is for legacy support, and will also match files that match below.
                { :description => "Post-Filter Signal",
                  :format => "SGR",
                  :extension => "_pf.sgr",
                  :read_num_specific => true }
               ]

  FAIL_FILE_TYPES = [
                { :description => "Unmapped Failed Reads",
                  :format => "FASTQ",
                  :extension => "_reject.fastq",
                  :read_num_specific => true }
               ]

  def show_data_files
    begin_section("data")
    @html.puts "<p>"
    @html.puts "Sequencing and analysis data may be downloaded using "
    @html.puts "the links in this section.  The URLs are also included "
    @html.puts "in the statistics CSV file below.  If you have an "
    @html.puts "account on the SCG1 compute cluster then you can use "
    @html.puts "the path names in the CSV file instead of the links."
    @html.puts "</p>"

    @html.puts "<p>"
    @html.puts "<b><a href=\"#{@run_name}_L#{@lane_num}_stats.csv\">"
    @html.puts "Statistics and URLs (CSV File)</a></b>"
    @html.puts "</p>"

    show_data_file_table("Post-Filter Data", PF_FILE_TYPES)
    show_data_file_table("Failed Data", FAIL_FILE_TYPES)

    end_section
  end

  def show_data_file_table(title, file_types)
    @html.puts "<p>"
    @html.puts title
    @csv << []
    @csv << [title]

    begin_table

    begin_row
    table_cell "Description"
    table_cell "Barcode"
    table_cell "Read Number"
    table_cell "Format"
    table_cell "File Size (Bytes)"
    table_cell "SCG1 Path", :html => :skip
    table_cell "Link"
    end_row

    file_types.each do |type_info|
      if @stats[:read1_stats][:barcodes].empty?
        show_file_type(type_info)
      else
        @barcodes.each do |barcode|
          show_file_type(type_info, barcode)
        end
      end
    end

    end_table
    @html.puts "</p>"
  end

  def show_file_type(type_info, barcode = nil)
    if paired_end? and type_info[:read_num_specific]
      if not show_file_location(type_info, barcode, 1)
        STDERR.puts "Read 1: No #{type_info[:format]}" if @verbose
      end
      if not show_file_location(type_info, barcode, 2)
        STDERR.puts "Read 2: No #{type_info[:format]}" if @verbose
      end
    else
      if not show_file_location(type_info, barcode, nil)
        STDERR.puts "No #{type_info[:format]}" if @verbose
      end
    end
  end

  def show_file_location(type_info, barcode, read_number=nil)
    filename = "#{@run_name}_L#{@lane_num}"
    filename += "_#{barcode}" unless barcode.nil?
    filename += "_#{read_number}" unless read_number.nil?
    filename += type_info[:extension]

    lanedir = "#{@data_dir}/L#{@lane_num}"
    if File.exists?(lanedir)
      filedir = lanedir
      urldir  = "#{@run_url}/L#{@lane_num}"
    else
      filedir = @data_dir
      urldir  = @run_url
    end

    # Check if file exists.
    #  If not, check if file.gz exists.
    path = "#{filedir}/#{filename}"
    url  = "#{urldir}/#{filename}"
    if not File.exists?(path)
      path = path + ".gz"
      url = url + ".gz"
      if !File.exists?(path)
        STDERR.puts "Can't find file #{path}" if @verbose
        return false
      end
    end

    size = File.size(path)

    begin_row
    table_cell type_info[:description]
    table_cell barcode
    table_cell read_number
    table_cell type_info[:format]
    table_cell commify(size), :type => :numeric
    table_cell path, :html => :skip
    table_cell url, :html => {:value => "<a href=\"#{url}\">Download</a>"}
    end_row

    return true
  end

  ################################################################
  # HTML File Generation, Plots
  ################################################################

  def show_plot_links
    return if @noplot

    if !@bam_files.nil?
      show_plot("mismatch",
                "#{@run_name}_L#{@lane_num}_mm_summary.png") do
        @html.puts "<p>"
        @html.puts "This plot shows the fraction of bases that mismatch "
        @html.puts "the reference sequence "
        @html.puts "for each sequencing cycle (i.e. each position in the read). "
        @html.puts "Vertical lines show boundaries between the reads if the run "
        @html.puts "has multiple reads. "
        @html.puts "An <a href=\"#{details_url('mismatch')}\">expanded plot</a> "
        @html.puts "is also available (useful for longer read lengths)."
        @html.puts "</p>"
      end
    end

    show_plot("quality", "#{@run_name}_L#{@lane_num}_qual_summary.png") do
      @html.puts "<p>"
      @html.puts "The black points show the median quality score "
      @html.puts "for each sequencing cycle (i.e. each position in the read). "
      @html.puts "The gray lines show the 25% and 75% quartiles. "
      @html.puts "Vertical lines show boundaries between the reads if the run "
      @html.puts "has multiple reads. "
      @html.puts "An <a href=\"#{details_url('quality')}\">expanded plot</a> "
      @html.puts "is also available (useful for longer read lengths)."
      @html.puts "</p>"
    end

    show_plot("calls", "#{@run_name}_L#{@lane_num}_call_summary.png") do
      @html.puts "<p>"
      @html.puts "This plot shows the base composition for each sequencing "
      @html.puts "cycle (i.e. each position in the read).  The vertical axis "
      @html.puts "is the percentage for each base relative to all called bases. "
      @html.puts "Vertical lines show boundaries between the reads if the run "
      @html.puts "has multiple reads. "
      @html.puts "An <a href=\"#{details_url('calls')}\">expanded plot</a> "
      @html.puts "is also available (useful for longer read lengths)."
      @html.puts "</p>"
    end

    show_plot("intensity",
              "#{@run_name}_L#{@lane_num}_int_summary.png") do
      @html.puts "<p>"
      @html.puts "This plot shows the average image intensities "
      @html.puts "for each sequencing cycle (i.e. each position in the read). "
      @html.puts "These intensities have been corrected for cross talk "
      @html.puts "and amplitude differences and are the input to the "
      @html.puts "base caller. "
      @html.puts "Vertical lines show boundaries between the reads if the run "
      @html.puts "has multiple reads. "
      @html.puts "An <a href=\"#{details_url('intensity')}\">expanded plot</a> "
      @html.puts "is also available (useful for longer read lengths)."
      @html.puts "</p>"
    end

    @html.puts "<p>"
    @html.puts "Additional <a href=\"#{@run_name}_L#{@lane_num}_diags.html\">Diagnostic Plots</a>"
    @html.puts "</p>"
  end

  def write_details_file
    return if @noplot

    puts "Writing HTML file #{details_html}..." if @verbose
    title = "Expanded Results for #{@run_name} Lane #{@lane_num}"
    @html = File.new(details_html, "w")
    html_prolog(title)

    @html.puts "      <h3>Contents</h3>"
    begin_contents
    contents_entry("mismatch") unless @bam_files.nil?
    contents_entry("quality")
    contents_entry("calls")
    contents_entry("intensity")
    end_contents

    @html.puts "      <p>"
    @html.puts "      Back to <a href=\"#{@run_name}_L#{@lane_num}_results.html\">Main Results Page</a>"
    @html.puts "      </p>"

    if !@bam_files.nil?
      show_plot("mismatch", "#{@run_name}_L#{@lane_num}_mm_details.png",
                :title_suffix => "(Expanded)") do
        @html.puts "<p>"
        @html.puts "This plot shows the fraction of bases that mismatch "
        @html.puts "the reference sequence "
        @html.puts "for each sequencing cycle (i.e. each position in the read). "
        @html.puts "Vertical lines show boundaries between the reads if the run "
        @html.puts "has multiple reads. "
        @html.puts "</p>"
      end
    end

    show_plot("quality", "#{@run_name}_L#{@lane_num}_qual_details.png",
              :title_suffix => "(Expanded)") do
      @html.puts "<p>"
      @html.puts "This plot shows the median quality score (black bar) "
      @html.puts "for each sequencing cycle (i.e. each position in the read). "
      @html.puts "The boxes show the 25% and 75% quartiles and the "
      @html.puts "whiskers show the minimum and maximum values. "
      @html.puts "Vertical lines show boundaries between the reads if the run "
      @html.puts "has multiple reads. "
      @html.puts "</p>"
    end

    show_plot("calls", "#{@run_name}_L#{@lane_num}_call_details.png",
              :title_suffix => "(Expanded)") do
      @html.puts "<p>"
      @html.puts "This plot shows the base composition for each sequencing "
      @html.puts "cycle (i.e. each position in the read).  The vertical axis "
      @html.puts "is the percentage for each base relative to all called bases. "
      @html.puts "Vertical lines show boundaries between the reads if the run "
      @html.puts "has multiple reads. "
      @html.puts "</p>"
    end

    show_plot("intensity", "#{@run_name}_L#{@lane_num}_int_details.png",
              :title_suffix => "(Expanded)") do
      @html.puts "<p>"
      @html.puts "This plot shows the average image intensities "
      @html.puts "for each sequencing cycle (i.e. each position in the read). "
      @html.puts "These intensities have been corrected for cross talk "
      @html.puts "and amplitude differences and are the input to the "
      @html.puts "base caller. "
      @html.puts "Vertical lines show boundaries between the reads if the run "
      @html.puts "has multiple reads. "
      @html.puts "</p>"
    end

    html_epilog
    @html.close
    @html = nil
  end

  def write_diags_file
    return if @noplot

    puts "Writing HTML file #{diags_html}..." if @verbose
    title = "Diagnostic Plots for #{@run_name} Lane #{@lane_num}"
    @html = File.new(diags_html, "w")
    html_prolog(title)

    @html.puts "      <h3>Contents</h3>"
    begin_contents
    contents_entry("raw")
    contents_entry("focus")
    contents_entry("tile_metrics")
    end_contents

    @html.puts "      <p>"
    @html.puts "      Back to <a href=\"#{@run_name}_L#{@lane_num}_results.html\">Main Results Page</a>"
    @html.puts "      </p>"

    show_plot("raw", "#{@run_name}_L#{@lane_num}_raw_int_summary.png") do
      @html.puts "<p>"
      @html.puts "This plot shows the average raw image intensities "
      @html.puts "for each sequencing cycle (i.e. each position in the read). "
      @html.puts "Vertical lines show boundaries between the reads if the run "
      @html.puts "has multiple reads. "
      @html.puts "</p>"
    end

    show_plot("focus", "#{@run_name}_L#{@lane_num}_focus_summary.png") do
      @html.puts "<p>"
      @html.puts "This plot shows the average focus metric (FWHM) "
      @html.puts "for each sequencing cycle (i.e. each position in the read). "
      @html.puts "Vertical lines show boundaries between the reads if the run "
      @html.puts "has multiple reads. "
      @html.puts "</p>"
    end

    show_tile_metrics

    html_epilog
    @html.close
    @html = nil
  end

  TILE_STATS = [ "Tile Count",
                 "Cluster Count",
                 "Post-Filter Cluster Count",
                 "Median Cluster Density",
                 "Median Post-Filter Cluster Density" ]

  PHASING_STATS = [ "Minimum Phasing",
                    "Median Phasing",
                    "Maximum Phasing" ]

  PREPHASING_STATS = [ "Minimum Prephasing",
                       "Median Prephasing",
                       "Maximum Prephasing" ]

  def show_tile_metrics
    metrics = parse_stats_file("#{outfile_base}_tile_metrics.txt")

    begin_section("tile_metrics")

    # show the clustering statistics table

    @html.puts "<p>"
    @html.puts "Clustering Statistics:"
    begin_table
    TILE_STATS.each do |stat_name|
      begin_row
      table_cell(stat_name)
      table_cell(metrics[stat_name], :type => :numeric)
      end_row
    end
    end_table
    @html.puts "</p>"

    # show the phasing statistics table

    @html.puts "<p>"
    @html.puts "Phasing Statistics:"
    begin_table

    begin_row
    table_cell ""
    read_cnt = metrics["Read Count"].to_i
    (1..read_cnt).each {|read_num| table_cell "Read #{read_num}"}
    end_row

    PHASING_STATS.each do |stat_name|
      begin_row
      table_cell(stat_name)
      (1..read_cnt).each do |read_num|
        table_cell metrics["#{stat_name} Read #{read_num}"]
      end
      end_row
    end
    end_table
    @html.puts "</p>"

    # show the prephasing statistics table

    @html.puts "<p>"
    @html.puts "Prephasing Statistics:"
    begin_table

    begin_row
    table_cell ""
    (1..read_cnt).each {|read_num| table_cell "Read #{read_num}"}
    end_row

    PREPHASING_STATS.each do |stat_name|
      begin_row
      table_cell(stat_name)
      (1..read_cnt).each do |read_num|
        table_cell metrics["#{stat_name} Read #{read_num}"]
      end
      end_row
    end
    end_table
    @html.puts "</p>"

    end_section
  end

  def show_plot(section, plotfile, opts = {})
    begin_section(section, opts)
    yield
    @html.puts "        <img src=\"#{plotfile}\" alt=\"plot\" />"
    end_section
  end

  # test if a string is nil or empty
  def blank?(thing)
    thing.respond_to?(:empty?) ? thing.empty? : !thing
  end

  ################################################################
  # Main Program
  ################################################################

  def main
    parse_args
    load_config(@config_file)
    load_stats
    make_plots unless @noplot
    make_html
  end

end

PublishIlluminaResults.new.main
