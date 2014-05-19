#!/usr/bin/env ruby

#
# collect_illumina_stats.rb: create a comprehensive statistics report
# for one lane of illumina sequencing data; this script just combines data
# from a variety of sources
#
# Phil Lacroute
#

require 'optparse'
require 'fileutils'

class CollectIlluminaStats

  @@Program = "collect_illumina_stats.rb"

  @@CategoryName = {
    :post_filter => "Post-Filter",
    :rejected => "Failed"
  }

  @@CategoryKey = {
    :post_filter => "Post-Filter Reads",
    :rejected => "Failed Reads"
  }

  @@ElandMappingStats = [
      "Too-Many-Ns",
      "No-Match",
      "Repeat-Masked",
      "Contam",
      "Unique 0mm",
      "Unique 1mm",
      "Unique 2mm",
      "Non-Unique 0mm",
      "Non-Unique 1mm",
      "Non-Unique 2mm",
      "Repetitive 0mm",
      "Repetitive 1mm",
      "Repetitive 2mm"
  ]
  @@BwaMappingStats = [
      "No-Match",
      "Unique 0mm",
      "Unique 1mm",
      "Unique 2mm",
      "Unique 3+mm",
      "Unique w/Indel",
      "Non-Unique 0mm",
      "Non-Unique 1mm",
      "Non-Unique 2mm",
      "Non-Unique 3+mm",
      "Non-Unique w/Indel"
  ]


  # command-line options
  attr :run_name
  attr :lane
  attr :flow_cell
  attr :paired
  attr :read_number
  attr :read_len
  attr :platform
  attr :sample_name
  attr :submitter
  attr :genome
  attr :analysis_dir
  attr :seq_stats_dir
  attr :mapper_stats_dir
  attr :archive_dir
  attr :eland
  attr :bwa
  attr :index
  attr :no_rejects
  attr :use_lane_dirs

  # @barcodes is an array of hashes with the following keys:
  #  :codepoint (barcode sequence)
  #  :name (sample name)
  #  :seq_stats (hash of sequencing stats prior to mapping)
  #  :mapper_pf_stats (hash of mapping stats for post-filter reads)
  #  :mapper_reject_stats (hash of mapping stats for rejected reads)
  attr :barcodes

  # @seq_stats is a hash of sequencing stats for the lane
  attr :seq_stats

  # @mapper_pf_stats and @mapper_reject_stats are hashes of mapping stats
  attr :mapper_pf_stats
  attr :mapper_reject_stats

  def initialize
    @read_number = 1
    @barcodes = []
    @no_rejects = false
    @use_lane_dirs = false
  end

  # parse command-line options
  def parse_args
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: #{@@Program} [options]"
      opts.separator "Options:"

      opts.on("--run RUN", "run name (required)") do |run|
        @run_name = run
      end

      opts.on("--lane LANE", "lane number (required)") do |lane|
        @lane = lane
      end

      opts.on("--flow_cell STR", "flow cell ID") do |str|
        @flow_cell = str
      end

      opts.on("--paired", "report stats for paired-end reads") do
        @paired = true
      end

      opts.on("--read_number NUM", "read number (default 1)") do |num|
        @read_number = num
      end

      opts.on("--read_len NUM", "read length") do |num|
        @read_len = num
      end

      opts.on("--platform STR", "sequencing platform") do |str|
        @platform = str
      end

      opts.on("--sample_name STR", "sample name") do |str|
        @sample_name = str
      end

      opts.on("--submitter STR", "submitter") do |str|
        @submitter = str
      end

      opts.on("--genome STR", "genome") do |str|
        @genome = str
      end

      opts.on("--analysis_dir DIR",
              "analysis directory with raw stats files",
              "(required, or --seq_stats_dir and --mapper_stats_dir)") do |dir|
        @analysis_dir = dir
      end

      opts.on("--seq_stats_dir DIR",
              "analysis directory with seq stats files",
              "(required or --analysis_dir)") do |dir|
        @seq_stats_dir = dir
      end

      opts.on("--mapper_stats_dir DIR",
              "analysis directory with mapping stats files",
              "(required or --analysis_dir)") do |dir|
        @mapper_stats_dir = dir
      end

      opts.on("--archive_dir DIR",
              "archive directory for results (required)") do |dir|
        @archive_dir = dir
      end

      opts.on("--eland", "report eland mapping statistics") do
        @eland = true
      end

      opts.on("--bwa", "report bwa mapping statistics") do
        @bwa = true
      end

      opts.on("--index",
              "sequences include an index read",
              "(specify index sequences with --barcode)") do
        @index = true
      end

      opts.on("--barcode STR",
              "barcode sequence and sample name",
              "in the form: SEQUENCE:NAME",
              "(may be specified multiple times)") do |str|
        fields = str.split(':', 2)
        create_barcode(fields[0], fields[1])
      end

      opts.on("--no_rejects",
              "exclude rejects from analysis") do
        @no_rejects = true
      end

      opts.on("--use_lane_dirs",
              "use lane directories in output paths") do
        @use_lane_dirs = true
      end

      opts.on("--verbose",
              "increase output to stderr") do
        @verbose = true
      end

      opts.on("--debug",
              "WAY increase output to stderr") do
        @debug = true
      end

      opts.on_tail("-h", "--help", "Print help message") do
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
      die err.to_s
    end

    if !ARGV.empty?
      STDERR.puts "error: unexpected options #{ARGV.join(" ")}"
      exit 1
    end

    die "--run is required" if @run_name.nil?
    die "--lane is required" if @lane.nil?
    die "--archive_dir is required" if @archive_dir.nil?
    if @analysis_dir.nil?
      if @seq_stats_dir.nil? or @mapper_stats_dir.nil?
          die "need both --seq_stats_dir and --mapper_stats_dir if no --analysis_dir"
      end
    else
      # --analysis_dir will override --seq_stats_dir and --mapper_stats_dir
      @seq_stats_dir = @mapper_stats_dir = @analysis_dir
    end

    die "only one of --eland and --bwa" if @eland and @bwa
    #die "need one of --eland or --bwa" if not (@eland or @bwa)

    create_barcode("unmatched", "unmatched") unless @barcodes.empty?
  end

  def create_barcode(codepoint, name)
    @barcodes.push(:codepoint => codepoint,
                   :name => name,
                   :post_filter => {},
                   :rejected => {})
  end

  # load all of the input files
  def load_stats
    stats_file_prefix = "#{@run_name}_L#{@lane}"
    stats_file_prefix += "_#{@read_number}" if @paired
    seq_stats_file_prefix = File.join(@seq_stats_dir, stats_file_prefix)
    mapper_stats_file_prefix = File.join(@mapper_stats_dir, stats_file_prefix)

    if @eland
      mapper_suffix = "eland"
    elsif @bwa
      mapper_suffix = "bwa"
    else
      mapper_suffix = nil
    end

    @seq_stats = parse_stats_file(seq_stats_file_prefix + "_seq_stats.txt")

    if @barcodes.empty?
      if not mapper_suffix.nil?
        @mapper_pf_stats =
            parse_stats_file(mapper_stats_file_prefix + "_#{mapper_suffix}_pf_stats.txt")
        @mapper_reject_stats =
            parse_stats_file(mapper_stats_file_prefix + "_#{mapper_suffix}_reject_stats.txt") unless @no_rejects
      end
    elsif @index
      @barcodes.each do |bcinfo|
        bc_stats_file_prefix = "#{@run_name}_L#{@lane}"
        bc_stats_file_prefix += "_#{bcinfo[:codepoint]}"
        bc_stats_file_prefix += "_#{@read_number}" if @paired
        bc_seq_stats_file_prefix = File.join(@seq_stats_dir, bc_stats_file_prefix)
        bc_mapper_stats_file_prefix = File.join(@mapper_stats_dir, bc_stats_file_prefix)
        bcinfo[:seq_stats] = parse_stats_file(bc_seq_stats_file_prefix + "_seq_stats.txt")
        bcinfo[:seq_stats]["Failed Reads"] =
          bcinfo[:seq_stats]["Total Reads"].to_i -
          bcinfo[:seq_stats]["Post-Filter Reads"].to_i

        if bcinfo[:codepoint] != "unmatched"
          if not mapper_suffix.nil?
            bcinfo[:mapper_pf_stats] =
                parse_stats_file(bc_mapper_stats_file_prefix + "_#{mapper_suffix}_pf_stats.txt")
            bcinfo[:mapper_reject_stats] =
                parse_stats_file(bc_mapper_stats_file_prefix + "_#{mapper_suffix}_reject_stats.txt") unless @no_rejects
          end
        end
      end
    else  # Custom barcode.
      parse_barcode_seq_stats(seq_stats_file_prefix + "_barcode_stats.txt")

      if not mapper_suffix.nil?
        @barcodes.each do |bcinfo|
          next if bcinfo[:codepoint] == "unmatched"
          bc_prefix = "#{mapper_stats_file_prefix}_#{bcinfo[:codepoint]}_#{mapper_suffix}"
          bcinfo[:mapper_pf_stats] =
              parse_stats_file("#{bc_prefix}_pf_stats.txt")
          bcinfo[:mapper_reject_stats] =
              parse_stats_file("#{bc_prefix}_reject_stats.txt") unless @no_rejects
        end  # @barcodes.each
      end

    end
  end

  # return a hash containing the statistics from the specified file
  # each line of the file should be of the form:
  # label: value
  def parse_stats_file(filename)
    STDERR.puts "Reading stats file #{filename}" if @verbose
    stats = Hash.new
    IO.foreach(filename) do |line|
      if line =~ /^([^:]+):\s+(.*)$/
        stats[$1] = $2
        STDERR.puts "#{$1} -> #{$2}" if @debug
      else
        die "#{filename}: parse error on line #{$.}"
      end
    end
    stats
  end

  # parse the sequencing statistics from the barcode splitter (for non-index
  # barcodes)
  def parse_barcode_seq_stats(stats_filename)
    @barcodes.each {|bcinfo| bcinfo[:seq_stats] = Hash.new}
    STDERR.puts "Reading barcode stats file #{stats_filename}" if @verbose
    parse_barcode_stats_file(stats_filename)
    @barcodes.each do |bcinfo|
      bcinfo[:seq_stats]["Total Reads"] =
        bcinfo[:seq_stats]["Post-Filter Reads"].to_i +
        bcinfo[:seq_stats]["Failed Reads"].to_i
    end
  end

  # parse the input file which should contain statistics from the
  # barcode splitter (split_barcodes.rb); then store the read count for
  # each barcode in the corresponding :seq_stats hash in @barcodes;
  # category is either :post_filter or :rejected and determines the
  # key in the :seq_stats hash
  def parse_barcode_stats_file(filename)
    # parse the file
    stats = Hash.new
    IO.foreach(filename) do |line|
      next if line =~ /^Barcode/ || line =~ /^total/
      fields = line.split("\t")
      if fields.size != 3 || fields[1] !~ /^\d+$/
        die "#{filename}: parse error: #{line}"
      end
      stats[fields[0]] = fields[1]
      STDERR.puts "#{fields[0]} => #{fields[1]}" if @debug
    end

    # copy the values for the required barcodes (and make sure they
    # are all present)
    @barcodes.each do |bcinfo|
      codepoint = bcinfo[:codepoint]
      die "missing barcode #{codepoint} in #{filename}" if
        stats[codepoint].nil?
      bcinfo[:seq_stats]["Post-Filter Reads"] = stats[codepoint]
    end
  end

  # store the stats in the output files
  def store_stats
    out_file_base = "#{@archive_dir}/"
    out_file_base += "L#{lane}/" if @use_lane_dirs
    out_file_base += "#{@run_name}_L#{@lane}"

    lane_stats_filename = out_file_base
    lane_stats_filename += "_#{@read_number}" if @paired
    lane_stats_filename += "_stats.txt"
    store_lane_stats(lane_stats_filename)

    @barcodes.each do |bcinfo|
      #next if bcinfo[:codepoint] == "unmatched"
      bc_stats_filename = out_file_base + "_#{bcinfo[:codepoint]}"
      bc_stats_filename += "_#{@read_number}" if @paired
      bc_stats_filename += "_stats.txt"
      store_barcoded_sample_stats(bcinfo, bc_stats_filename)
    end
  end

  # store the per-lane stats
  def store_lane_stats(lane_stats_filename)
    File.open("#{lane_stats_filename}.tmp", "w") do |ios|
      seq_total = @seq_stats["Total Reads"].to_i
      seq_pf = @seq_stats["Post-Filter Reads"].to_i
      seq_reject = [seq_total - seq_pf, 0].max
      print_basic_stats(ios,
                        :sample_name => @sample_name,
                        :total_reads => seq_total)
      if @barcodes.empty? && (@eland || @bwa)
        print_mapping_stats(ios, :post_filter, @mapper_pf_stats)
        print_mapping_stats(ios, :rejected, @mapper_reject_stats) unless @no_rejects
      else
        ios.puts "#{@@CategoryName[:post_filter]} Reads: #{seq_pf}"
        print_barcode_stats(ios, :post_filter) unless @barcodes.empty?
        ios.puts "#{@@CategoryName[:rejected]} Reads: #{seq_reject}" unless @no_rejects
        print_barcode_stats(ios, :rejected) unless @barcodes.empty? or @no_rejects
      end
    end
    finalize lane_stats_filename
  end

  def print_basic_stats(ios, opts = {})
    ios.puts "Run: #{@run_name}"
    ios.puts "Lane: #{@lane}"
    ios.puts "Flow Cell: #{@flow_cell}" unless @flow_cell.nil?
    ios.puts "Barcode: #{opts[:barcode]}" unless opts[:barcode].nil?
    ios.puts "Submitter: #{@submitter}" unless @submitter.nil?
    ios.puts "Genome: #{@genome}" unless @genome.nil?
    ios.puts "Read Number: #{@read_number}" unless @read_number.nil?
    ios.puts "Read Length: #{@read_len}" unless @read_len.nil?
    ios.puts "Platform: #{@platform}" unless @platform.nil?
    ios.puts "Sample: #{opts[:sample_name]}" unless opts[:sample_name].nil?
    ios.puts "Total Reads: #{opts[:total_reads]}"
  end

  # print the mapping statistics for one category of reads
  # (:post_filter or :rejected)
  def print_mapping_stats(ios, category, stats)
    name = @@CategoryName[category]
    ios.puts "#{name} Reads: #{stats['Total Reads']}"
    if @eland
      mapping_stats = @@ElandMappingStats
    elsif @bwa
      mapping_stats = @@BwaMappingStats
    else
      return
    end
    mapping_stats.each do |label|
      ios.puts "#{name} #{label}: #{stats[label]}"
    end
  end

  # print basic statistics for all of the barcoded samples in the lane
  # category is :post_filter or :rejected
  def print_barcode_stats(ios, category)
    name = @@CategoryName[category]
    key = @@CategoryKey[category]
    @barcodes.each do |bcinfo|
      ios.puts "#{name} #{bcinfo[:codepoint]}: #{bcinfo[:seq_stats][key]}"
    end
  end

  # store the statistics for one barcoded sample
  def store_barcoded_sample_stats(bcinfo, bc_stats_filename)
    File.open("#{bc_stats_filename}.tmp", "w") do |ios|
      print_basic_stats(ios,
                        :barcode => bcinfo[:codepoint],
                        :sample_name => bcinfo[:name],
                        :total_reads => bcinfo[:seq_stats]["Total Reads"])
      if (@eland or @bwa) and not bcinfo[:codepoint] == "unmatched"
        print_mapping_stats(ios, :post_filter,
                            bcinfo[:mapper_pf_stats])
        print_mapping_stats(ios, :rejected,
                            bcinfo[:mapper_reject_stats]) unless @no_rejects
      else
        ios.puts("#{@@CategoryName[:post_filter]} Reads: " +
                 "#{bcinfo[:seq_stats]['Post-Filter Reads']}")
        ios.puts("#{@@CategoryName[:rejected]} Reads: " +
                 "#{bcinfo[:seq_stats]['Failed Reads']}") unless @no_rejects
      end
    end
    finalize bc_stats_filename
  end

  # check statistics for consistency
  def validate_stats
    seq_total = @seq_stats["Total Reads"].to_i
    seq_pf = @seq_stats["Post-Filter Reads"].to_i
    die "seq_stats_file: missing total" if @seq_stats["Total Reads"].nil?
    die "seq_stats_file: missing post-filter read count" if @seq_stats["Post-Filter Reads"].nil?
    die("seq_stats_file: #{seq_pf} post-filter reads > " +
        "#{seq_total} total reads") if seq_pf > seq_total

    # check mapped-read statistics
    if @barcodes.empty? && (@eland || @bwa)
      mapper_pf = @mapper_pf_stats["Total Reads"].to_i
      die("#{seq_pf} post-filter reads != " +
          "#{mapper_pf} mapped post-filter reads") if seq_pf != mapper_pf
      if not @no_rejects
        mapper_reject = @mapper_reject_stats["Total Reads"].to_i
        mapper_total = mapper_pf + mapper_reject
        die("#{seq_total} sequenced reads != #{mapper_total} mapped reads") if
            seq_total != mapper_total
      end
    end

    # check barcode statistics
    #if !@barcodes.empty?
    #  barcode_pf     = count_and_validate_barcodes(:post_filter, :mapper_pf_stats)
    #  die("#{seq_pf} post-filter reads != " +
    #      "#{barcode_pf} barcoded post-filter reads") if seq_pf != barcode_pf
    #  if not @no_rejects
    #    barcode_reject = count_and_validate_barcodes(:rejected,  :mapper_reject_stats)
    #    barcode_total = barcode_pf + barcode_reject
    #    die("#{seq_total} sequenced reads != #{barcode_total} barcoded reads") if
    #            seq_total != barcode_total
    #  end
    #end
  end

  # validate one category of barcode stats (:post_filter or :rejected)
  # and return the total number of reads for the category
  #def count_and_validate_barcodes(mapper_stats_key)
  #  total_reads = 0
  #  @barcodes.each do |bcinfo|
  #    barcode_reads = bcinfo[:seq_stats]["Total Reads"].to_i
  #    total_reads += barcode_reads
  #    next if bcinfo[:codepoint] == "unmatched" || !(@eland || @bwa)
  #    mapped_reads = bcinfo[mapper_stats_key]["Total Reads"].to_i
  #    if barcode_reads != mapped_reads
  #      die("barcode #{bcinfo[:codepoint]}: #{mapped_reads} mapped reads" +
  #          " != #{barcode_reads} sequenced reads")
  #    else
  #      STDERR.puts "barcode #{bcinfo[:codepoint]}: OK" if @verbose
  #    end
  #  end
  #  total_reads
  #end

  def finalize(filename)
    FileUtils.chmod(0444, "#{filename}.tmp")
    FileUtils.mv("#{filename}.tmp", filename)
  end

  # print an error message and exit
  def die(msg)
    STDERR.puts "#{@@Program}: #{msg}"
    exit 1
  end

  # main entry point
  def main
    File.umask(0002)
    parse_args
    load_stats
    store_stats
    validate_stats
  end

end

CollectIlluminaStats.new.main
