#!/usr/bin/env ruby

#
# create_analysis_manifest.rb: create a file containing information
# about the results files for an analysis run
#
# Phil Lacroute
#

require 'optparse'
require 'csv'

class CreateAnalysisManifest

  @@Program = "create_analysis_manifest.rb"
  
  @@FileTypes = [
    { :description => "Unmapped Reads (Fastq), Post-Filter",
      :extension => "_pf.fastq",
      :type => "fastq",
      :includes_passed => true,
      :includes_failed => false },
    { :description => "Unmapped Reads (Fastq), Rejected",
      :extension => "_reject.fastq",
      :type => "fastq",
      :includes_passed => false,
      :includes_failed => true },
    { :description => "Unmapped Reads (Text), Post-Filter",
      :extension => "_pf.txt",
      :type => "sequence_txt",
      :includes_passed => true,
      :includes_failed => false },
    { :description => "Unmapped Reads (Text), Rejected",
      :extension => "_reject.txt",
      :type => "sequence_txt",
      :includes_passed => false,
      :includes_failed => true },
    { :description => "Mapped Reads (Illumina Export)",
      :extension => "_export.txt",
      :type => "export",
      :includes_passed => true,
      :includes_failed => true },
    { :description => "Mapped Reads (Eland Extended), Post-Filter",
      :extension => "_eland_extended_pf.txt",
      :type => "eland_extended",
      :includes_passed => true,
      :includes_failed => false },
    { :description => "Mapped Reads (Eland Extended), Rejected",
      :extension => "_eland_extended_reject.txt",
      :type => "eland_extended",
      :includes_passed => false,
      :includes_failed => true },
    { :description => "Mapped Reads (Eland Multi), Post-Filter",
      :extension => "_pf_eland_multi.txt",
      :type => "eland_multi",
      :includes_passed => true,
      :includes_failed => false },
    { :description => "Mapped Reads (Eland Multi), Rejected",
      :extension => "_reject_eland_multi.txt",
      :type => "eland_multi",
      :includes_passed => false,
      :includes_failed => true },
    { :description => "Signal File (SGR), Post-Filter",
      :extension => "_pf.sgr",
      :type => "sgr",
      :includes_passed => true,
      :includes_failed => false },
    { :description => "Signal File (SGR), Rejected",
      :extension => "_reject.sgr",
      :type => "sgr",
      :includes_passed => false,
      :includes_failed => true },
    { :description => "Signal File (SGR)",
      :extension => ".sgr",
      :type => "sgr",
      :includes_passed => true,
      :includes_failed => true },
    { :description => "BED File, Post-Filter",
      :extension => "_pf.bed",
      :type => "bed",
      :includes_passed => true,
      :includes_failed => false },
    { :description => "BED File, Rejected",
      :extension => "_reject.bed",
      :type => "bed",
      :includes_passed => false,
      :includes_failed => true },
    { :description => "BAM File, Post-Filter",
      :extension => "_pf.bam",
      :type => "bam",
      :includes_passed => true,
      :includes_failed => false },
    { :description => "BAM File, Rejected",
      :extension => "_reject.bam",
      :type => "bam",
      :includes_passed => false,
      :includes_failed => true },
    { :description => "BAM File",
      :extension => ".bam",
      :type => "bam",
      :includes_passed => true,
      :includes_failed => false },
    { :description => "BAM Index File, Post-Filter",
      :extension => "_pf.bam.bai",
      :type => "bai",
      :includes_passed => true,
      :includes_failed => false },
    { :description => "BAM Index File, Rejected",
      :extension => "_reject.bam.bai",
      :type => "bai",
      :includes_passed => false,
      :includes_failed => true },
    { :description => "BAM Index File",
      :extension => ".bam.bai",
      :type => "bai",
      :includes_passed => true,
      :includes_failed => false }
  ]

  @@GeraldSummaryInfo = {
      :description => "GERALD Summary",
      :type => "gerald_summary",
      :includes_passed => false,
      :includes_failed => false }

  @@RunStatusInfo = {
      :description => "Run Status",
      :type => "run_status",
      :includes_passed => false,
      :includes_failed => false }

  # command-line options
  attr :input_dir
  attr :config_file

  def initialize
    @config = Hash.new
  end

  # parse command-line options
  def parse_args
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: #{@@Program} [options]"
      opts.separator "Options:"

      opts.on("--archive DIR", "directory containing the results") do |dir|
        @input_dir = dir
      end

      opts.on("--lane LANE", "use lane-specific archive directory") do |lane|
        @lane = lane
      end

      opts.on("--config_file FILE", "where is the config file? [default = ARCH_DIR/config.txt]") do |file|
        @config_file = file
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
      STDERR.puts "unexpected options: #{ARGV.join(" ")}"
      puts opts
      exit 1
    end

    die "--archive option is required" if @input_dir.nil?
  end

  def print_manifest
    # open csv file writer
    @csv = CSV::Writer.generate(STDOUT)
    @csv << ["Filename", "Type", "Description", "Lane", "Barcode",
             "Read", "IncludesPassed", "IncludesFailed", "Records",
             "Bytes", "Checksum"]

    # If specific lane given, do only that lane, o/w do all lanes.
    if @lane.nil?
      lane_list = (1..8)
    else
      lane_list = [@lane.to_i]
    end

    # print manifest entries for each lane
    lane_list.each do |lane_num|
      lane_config = @config[:lane][lane_num]
      if lane_config[:multiplexed] == "true"
        barcode_count = lane_config[:barcode_count].to_i
      else
        barcode_count = 0
      end
      if barcode_count == 0
        print_sample(lane_num)
      else
        (0..(barcode_count - 1)).each do |barcode_idx|
          barcode = lane_config[:barcode][barcode_idx][:codepoint]
          print_sample(lane_num, barcode, barcode_idx)
        end
        print_sample(lane_num, "unmatched")
      end
    end

    if @lane.nil?
      # print manifest entry for run status file
      print_file(nil, nil, nil, [], @@RunStatusInfo, "run_stats/Status.htm")
    end

  end

  def print_sample(lane_num, barcode = nil, barcode_idx = nil)
    # print manifest entries for data files
    if @config[:paired_end] == "true"
      print_read(lane_num, barcode, 1)
      print_read(lane_num, barcode, 2)
    else
      print_read(lane_num, barcode)
    end

    if @lane.nil?
      # print manifest entry for GERALD summary
      gerald_config = @config[:gerald][0]
      if @config[:index_read] != "true"
        gerald_dir = gerald_config[:gerald_dir]
      elsif barcode_idx.nil?
        gerald_dir = gerald_config[:demux][:binunknown][:gerald_dir]
      else
        lane_config = @config[:lane][lane_num]
        demux_bin = lane_config[:barcode][barcode_idx][:demux_bin]
        demux_bin_sym = "bin#{demux_bin}".to_sym
        gerald_dir = gerald_config[:demux][demux_bin_sym][:gerald_dir]
      end
      if gerald_dir =~ /^.*\/#{@config[:run_name]}\/Data\/(.+)$/
        gerald_status_file = "run_stats/#{$1}/Summary.htm"
        print_file(lane_num, barcode, nil, [], @@GeraldSummaryInfo,
                   gerald_status_file)
      else
        die "could not parse GERALD dir for lane #{lane_num}: #{gerald_dir}"
      end
    end

  end

  def print_read(lane_num, barcode, read_num = nil)
    stats_file = "#{@config[:archive_dir]}/"
    stats_file += "L#{lane_num}/" unless @lane.nil?
    stats_file += "#{@config[:run_name]}_L#{lane_num}"
    stats_file += "_#{barcode}" unless barcode.nil?
    stats_file += "_#{read_num}" unless read_num.nil?
    stats_file += "_stats.txt"
    if File.exists?(stats_file)
      stats = parse_stats_file(stats_file)
    else
      stats = { "Total Reads" => 0, "Post-Filter Reads" => 0 }
      warn "Couldn't find stats file #{stats_file}"
    end
    @@FileTypes.each do |type_info|
      try_file(lane_num, barcode, read_num, stats, type_info)
    end
  end

  def try_file(lane_num, barcode, read_num, stats, type_info)
    filename = "#{@config[:run_name]}_L#{lane_num}"
    filename += "_#{barcode}" unless barcode.nil?
    filename += "_#{read_num}" unless read_num.nil? or (type_info[:extension] =~ /bam/ and read_num != 2)
    filename += type_info[:extension]

    compressed_filename = filename + ".gz"

    return if print_file(lane_num, barcode, read_num, stats, type_info,
                         compressed_filename)
    print_file(lane_num, barcode, read_num, stats, type_info, filename)
  end

  def print_file(lane_num, barcode, read_num, stats, type_info, filename)
    path = "#{@config[:archive_dir]}/"
    path += "L#{lane_num}/" unless @lane.nil?
    path += "#{filename}"
    return false if !File.exists?(path)

    description = type_info[:description]
    description += ", Barcode #{barcode}" unless barcode.nil?
    description += ", Read #{read_num}" unless read_num.nil?

    if type_info[:includes_passed]
      if type_info[:includes_failed]
        record_count = stats["Total Reads"]
      else
        record_count = stats["Post-Filter Reads"]
      end
    else
      if type_info[:includes_failed]
        record_count = (stats["Total Reads"].to_i -
                        stats["Post-Filter Reads"].to_i)
      else
        record_count = 0
      end
    end
        
    byte_count = File.size(path)

    md5sum = nil
    md5_file = path + ".md5"
    if File.exists?(md5_file)
      IO.foreach(md5_file) do |line|
        if line =~ /^(\w{32})\s+\/.*$/
          md5sum = $1
          break
        end
      end
      die "could not find md5sum in #{md5_file}" if md5sum.nil?
    end

    @csv << [filename, type_info[:type], description,
             lane_num, barcode, read_num,
             type_info[:includes_passed], type_info[:includes_failed],
             record_count, byte_count, md5sum]

    return true
  end

  def parse_stats_file(filename)
    stats = Hash.new
    stats["barcodes"] = Array.new
    IO.foreach(filename) do |line|
      if line =~ /^([^:]+):\s+(.*)$/
        key = $1
        value = $2
        stats[key] = value
        if key =~ /^Post-Filter ([ACGT]+)$/
          stats["barcodes"].push(:barcode => $1)
        end
      else
        die "#{filename}: parse error on line #{$.}"
      end
    end
    stats
  end

  def load_config(filename)
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

  # test if a string is nil or empty
  def blank?(thing)
    thing.respond_to?(:empty?) ? thing.empty? : !thing
  end

  # print an error message and exit
  def die(msg)
    STDERR.puts "#{@@Program}: #{msg}"
    exit 1
  end

  def main
    parse_args
    if @config_file.nil?
      load_config("#{@input_dir}/config.txt")
    else
      load_config(@config_file)
    end
    print_manifest
  end

end

CreateAnalysisManifest.new.main
