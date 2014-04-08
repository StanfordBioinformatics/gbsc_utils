#!/usr/bin/env ruby

#
# report_illumina_results.rb: create a report containing statistics and links
# to data files for an illumina sequencing run
#
# Phil Lacroute
#

require 'optparse'

class ReportIlluminaResults

  @@Program = "report_illumina_results.rb"
  @@ArchiveRoot = "/srv/gs1/projects/scg/Archive/IlluminaRuns"
  @@UrlRoot = "http://scg-data.stanford.edu/Archive/IlluminaRuns"
  
  @@MonthNames = {
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

  @@RunStats = [
                { :name => "Run" },
                { :name => "Flow Cell" },
                { :name => "Platform" },
                { :name => "Read Length" }
               ]

  @@LaneStats = [
                 { :name => "Lane" },
                 { :name => "Sample", :wrap => true },
                 { :name => "Submitter" },
                 { :name => "Genome", :optional => true },
                 { :name => "Barcode", :optional => true },
                 { :name => "Total Reads", :numeric => true }
                ]

  @@PairStats = [
                 { :name => "Consistent Unique Pairs",
                   :numeric => true, :optional => true, :pair => true },
                 { :name => "Rescued Pairs",
                   :numeric => true, :optional => true, :pair => true },
                 { :name => "Total Consistent Pairs",
                   :numeric => true, :optional => true, :pair => true },
                 { :name => "Median Insert Size",
                   :numeric => true, :optional => true, :pair => true }
                ]

  @@ReadStats = [
                 { :name => "Post-Filter Reads", :numeric => true },
                 { :name => "Post-Filter BARCODE",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Unique", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Unique 0mm", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Unique 1mm", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Unique 2mm", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Non-Unique", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Non-Unique 0mm", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Non-Unique 1mm", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Non-Unique 2mm", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Repetitive", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Repetitive 0mm", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Repetitive 1mm", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Repetitive 2mm", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter No-Match", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Too-Many-Ns", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Repeat-Masked", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Contam", :optional => true,
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Failed Reads", :numeric => true },
                 { :name => "Failed BARCODE",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Unique", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Unique 0mm", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Unique 1mm", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Unique 2mm", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Non-Unique", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Non-Unique 0mm", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Non-Unique 1mm", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Non-Unique 2mm", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Repetitive", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Repetitive 0mm", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Repetitive 1mm", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Repetitive 2mm", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed No-Match", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Too-Many-Ns", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Repeat-Masked", :optional => true,
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Contam", :optional => true,
                   :numeric => true, :denom => "Failed Reads" }
                ]

  @@FileTypes = [
                 { :label => "Unmapped Post-Filter Reads",
                   :extensions => ["_pf.txt"],
                   :args => [:unmapped] },
                 { :label => "Unmapped Rejected Reads",
                   :extensions => ["_reject.txt"],
                   :args => [:unmapped, :reject] },
                 { :label => "Mapped Post-Filter Reads, Eland",
                   :extensions => ["_eland_extended_pf.txt",
                                   "_pf_eland_multi.txt"],
                   :args => [:eland] },
                 { :label => "Mapped Rejected Reads, Eland",
                   :extensions => ["_eland_extended_reject.txt",
                                   "_reject_eland_multi.txt"],
                   :args => [:eland, :reject] },
                 { :label => "Unmapped Post-Filter Reads With Quality Values",
                   :extensions => ["_pf.fastq"],
                   :args => [:fastq] },
                 { :label => "Unmapped Rejected Reads With Quality Values",
                   :extensions => ["_reject.fastq"],
                   :args => [:fastq, :reject] },
                 { :label => "SGR File",
                   :extensions => [".sgr", "_pf.sgr"],
                   :args => [:sgr] },
                 { :label => "SGR File, Rejected Reads",
                   :extensions => ["_reject.sgr"],
                   :args => [:sgr, :reject] },
                 { :label => "BED File, Post-Filter Reads",
                   :extensions => ["_pf.bed"],
                   :args => [:bed] },
                 { :label => "BED File, Rejected Reads",
                   :extensions => ["_reject.bed"],
                   :args => [:bed, :reject] },
                 { :label => "Illumina Export File",
                   :extensions => ["_export.txt"],
                   :args => [:export] }
                ]

  # command-line options
  attr :run_with_lanes
  attr :unmapped
  attr :fastq
  attr :eland
  attr :export
  attr :sgr
  attr :bed
  attr :reject
  attr :paths
  attr :archive_dir

  attr :run_name
  attr :lane_list
  attr :run_dir
  attr :data_dir
  attr :paired
  attr :stats
  attr :label_width
  attr :value_width
  attr :cached_wrapped_lines

  def initialize
    @stats = Array.new
    @label_width = 28
    @value_width = 22
  end

  # parse command-line options
  def parse_args
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: #{@@Program} [options]"
      opts.separator "Options:"

      opts.on("--run RUN",
              "run name with optional list of lanes",
              "(e.g. 100115_MARPLE_0014_FCYEF456:238)") do |run|
        @run_with_lanes = run
      end

      opts.on("--raw", "include raw sequence files") do
        @unmapped = true
      end

      opts.on("--fastq", "include fastq files") do
        @fastq = true
      end

      opts.on("--eland", "include eland-extended mappings") do
        @eland = true
      end

      opts.on("--export", "include Illumina export files") do
        @export = true
      end

      opts.on("--sgr", "include sgr files") do
        @sgr = true
      end

      opts.on("--bed", "include bed files") do
        @bed = true
      end

      opts.on("--reject", "include rejected-read files") do
        @reject = true
      end

      opts.on("--paths", "provide paths instead of URLs") do
        @paths = true
      end

      opts.on("--archive DIR",
              "archive directory for the run",
              "(use only to override default)") do |dir|
        @archive_dir = dir
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

    die "--run option is required" if @run_with_lanes.nil?

    (@run_name, lanes) = @run_with_lanes.split(":", 2)
    lanes = "12345678" if lanes.nil?
    @lane_list = lanes.split(//)
    year = @run_name[0..1].to_i + 2000
    month = @@MonthNames[@run_name[2..3]]
    @run_dir = "#{year}/#{month}/#{@run_name}"
    if @archive_dir
      @data_dir = @archive_dir
    else
      @data_dir = "#{@@ArchiveRoot}/#{@run_dir}"
    end

    die "at least one lane must be specified" if @lane_list.empty?

  end

  def check_for_paired_end
    first_lane = @lane_list.first
    @paired = true
    if File.file?(stats_filename(first_lane, 2))
      @label_width = 35
      return
    end
    @paired = false
    return if File.file?(stats_filename(first_lane))
    die "could not find stats file for lane #{first_lane} in #{@data_dir}"
  end

  def load_stats
    @lane_list.each do |lane|
      if @paired
        read1_stats = load_stats_file(lane, 1)
        read2_stats = load_stats_file(lane, 2)
        pair_stats = {}
        pair_stats = load_pair_stats_file(lane) if
          !blank?(read1_stats["Post-Filter Unique 0mm"])
        bc_pair_stats_list = Array.new
        read1_stats["barcodes"].each do |bcinfo|
          if !blank?(bcinfo[:stats]["Post-Filter Unique 0mm"])
            bc_pair_stats = load_pair_stats_file(lane, bcinfo[:barcode])
            bc_pair_stats_list.push(:barcode => bcinfo[:barcode],
                                    :stats => bc_pair_stats)
          end
        end
        pair_stats["barcodes"] = bc_pair_stats_list
        @stats.push({ :read1_stats => read1_stats,
                      :read2_stats => read2_stats,
                      :pair_stats => pair_stats })
      else
        @stats.push({ :read1_stats => load_stats_file(lane) })
      end
    end
  end

  def load_stats_file(lane, read_number = nil)
    lane_stats = parse_stats_file(stats_filename(lane, read_number))
    lane_stats["barcodes"].each do |bcinfo|
      bcinfo[:stats] = parse_stats_file(stats_filename(lane, read_number,
                                                       bcinfo[:barcode]))
    end

    if lane_stats["Flow Cell"].nil?
      run_fields = lane_stats["Run"].split("_")
      lane_stats["Flow Cell"] = run_fields[-1]
    end

    if lane_stats["Failed Reads"].nil?
      lane_stats["Failed Reads"] =
        lane_stats["Total Reads"].to_i - lane_stats["Post-Filter Reads"].to_i
    end

    compute_stat(lane_stats, "Post-Filter Unique",
                 [ "Post-Filter Unique 0mm", 
                   "Post-Filter Unique 1mm",
                   "Post-Filter Unique 2mm" ])
    compute_stat(lane_stats, "Post-Filter Non-Unique",
                 [ "Post-Filter Non-Unique 0mm", 
                   "Post-Filter Non-Unique 1mm",
                   "Post-Filter Non-Unique 2mm" ])
    compute_stat(lane_stats, "Post-Filter Repetitive",
                 [ "Post-Filter Repetitive 0mm", 
                   "Post-Filter Repetitive 1mm",
                   "Post-Filter Repetitive 2mm" ])
    compute_stat(lane_stats, "Failed Unique",
                 [ "Failed Unique 0mm", 
                   "Failed Unique 1mm",
                   "Failed Unique 2mm" ])
    compute_stat(lane_stats, "Failed Non-Unique",
                 [ "Failed Non-Unique 0mm", 
                   "Failed Non-Unique 1mm",
                   "Failed Non-Unique 2mm" ])
    compute_stat(lane_stats, "Failed Repetitive",
                 [ "Failed Repetitive 0mm", 
                   "Failed Repetitive 1mm",
                   "Failed Repetitive 2mm" ])

    lane_stats
  end

  def stats_filename(lane, read_number = nil, barcode = nil)
    filename = @data_dir + "/#{@run_name}_L#{lane}"
    filename += "_#{barcode}" unless barcode.nil?
    filename += "_#{read_number}" if @paired
    filename += "_stats.txt"
    filename
  end

  def load_pair_stats_file(lane, barcode = nil)
    filename = @data_dir + "/#{@run_name}_L#{lane}"
    filename += "_#{barcode}" unless barcode.nil?
    filename += "_pair_stats.txt"
    parse_stats_file(filename)
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

  # compute the statistic identified by label as the sum of the
  # statistics in components (an array of labels)
  def compute_stat(stats, label, components)
    return unless stats[label].nil?
    value = 0
    components.each do |comp|
      return if stats[comp].nil?
      value = value + stats[comp].to_i
    end
    stats[label] = value
  end

  def report_lane_stats
    # collect list of barcodes
    barcodes = []
    @stats.each do |lane_stats|
      lane_stats[:read1_stats]["barcodes"].each do |barcode_info|
        barcodes.push barcode_info[:barcode]
      end
    end
    barcodes.uniq!
    barcodes.push "unmatched" unless barcodes.empty?

    # print a key to the statistics
    print_key
    print "\n"

    # output per-run info
    @@RunStats.each do |stat_params|
      value = @stats[0][:read1_stats][stat_params[:name]]
      @stats.each do |lane_stats|
        die "inconsistent values for #{stat_params[:name]}" if
          lane_stats[:read1_stats][stat_params[:name]] != value
      end
      puts "#{stat_params[:name]}: #{value}"
    end

    # output per-lane info
    @@LaneStats.each do |stat_params|
      report_one_stat stat_params, barcodes, :read1_stats
    end

    # output pair info
    if @paired
      @@PairStats.each do |stat_params|
        report_one_stat stat_params, barcodes, :pair_stats
      end
    end

    # output per-read info
    if @paired
      @@ReadStats.each do |stat_params|
        report_one_stat stat_params, barcodes, :read1_stats, "Read 1 "
      end
      @@ReadStats.each do |stat_params|
        report_one_stat stat_params, barcodes, :read2_stats, "Read 2 "
      end
    else
      @@ReadStats.each do |stat_params|
        report_one_stat stat_params, barcodes, :read1_stats
      end
    end
  end

  def report_one_stat(stat_params, barcodes, read_sym, label_modifier = "")
    if stat_params[:name] =~ /BARCODE/
      # print this statistic multiple times, once per barcode
      barcodes.each do |barcode|
        stat_name = stat_params[:name].gsub("BARCODE", barcode)
        barcode_stat_params = stat_params.merge(:name => stat_name)
        print_stat_row(label_modifier + stat_name, @stats) do |lane_stats|
          print_stat(barcode_stat_params, lane_stats[read_sym])
        end
      end # barcodes.each
    else
      # print a simple (non-barcode) statistic
      return if skip_stat?(stat_params)
      print_stat_row(label_modifier + stat_params[:name],
                     @stats) do |lane_stats|
        print_stat(stat_params, lane_stats[read_sym])
      end
    end
  end

  # print a report showing full statistics for each barcode in one lane
  def report_barcode_stats(lane_stats)
    read1_barcode_list = lane_stats[:read1_stats]["barcodes"]
    return if read1_barcode_list.empty?
    print "\n"

    # output per-lane info
    @@LaneStats.each do |stat_params|
      report_one_barcode_stat(stat_params, read1_barcode_list)
    end

    # output pair info
    if @paired
      paired_barcode_list = lane_stats[:pair_stats]["barcodes"]
      @@PairStats.each do |stat_params|
        report_one_barcode_stat(stat_params, paired_barcode_list)
      end
    end

    # output per-read info
    if @paired
      read2_barcode_list = lane_stats[:read2_stats]["barcodes"]
      @@ReadStats.each do |stat_params|
        report_one_barcode_stat(stat_params, read1_barcode_list, "Read 1 ")
      end
      @@ReadStats.each do |stat_params|
        report_one_barcode_stat(stat_params, read2_barcode_list, "Read 2 ")
      end
    else
      @@ReadStats.each do |stat_params|
        report_one_barcode_stat(stat_params, read1_barcode_list)
      end
    end
  end

  def report_one_barcode_stat(stat_params, barcode_list, label_modifier = "")
    return if stat_params[:name] =~ /BARCODE/
    return if (stat_params[:optional] &&
               missing_barcode_stat?(stat_params[:name], barcode_list))
    label = label_modifier + stat_params[:name]
    print_stat_row(label, barcode_list) do |bcinfo|
      print_stat(stat_params, bcinfo[:stats])
    end
  end

  def print_key
    puts "Key for the statistics table:"
    puts "Post-Filter = reads that passed the base-caller's quality filter"
    puts "Failed = reads that failed the base-caller's quality filter"
    puts "Unique = reads that mapped to a single position in the genome"
    puts "Non-Unique = reads that mapped to 2-10 positions"
    puts "Repetitive = reads that mapped to >10 positions"
    puts "No-Match = reads that did not map anywhere"
    puts "0mm = zero mismatches (perfect match to the genome)"
    puts "1mm = one mismatching base"
    puts "2mm = two mismatching bases"
    puts "Too-Many-Ns = reads with too many uncalled bases to map"
    puts "Contam = reads that match the sequencing linkers"
    if @paired
      puts "Consistent Unique Pairs = paired reads where both reads map"
      puts "    uniquely and have consistent distance and orientation"
      puts "Rescued Pairs = paired reads where one read maps uniquely"
      puts "    and the other read has one consistent position"
      puts "Total Consistent Pairs = Consistent Unique + Rescued Pairs"
    end
  end

  # print a row of statistics; this method takes a block that prints
  # each column
  def print_stat_row(label_text, column_data)
    # print label
    printf("%-#{@label_width}s", label_text + ":")

    # print columns of data
    @cached_wrapped_lines = []
    column_data.each {|column| yield column}
    print "\n"

    # print wrapped lines if there are any
    num_wrapped_lines = 0
    @cached_wrapped_lines.each do |wrapped_lines|
      num_wrapped_lines += 1 if (!wrapped_lines.nil? && !wrapped_lines.empty?)
    end
    while num_wrapped_lines > 0
      print(" " * @label_width)
      next_num_wrapped_lines = 0
      @cached_wrapped_lines.each do |wrapped_lines|
        if wrapped_lines.nil? || wrapped_lines.empty?
          printf(" " * @value_width)
        else
          printf(" %#{@value_width}s", wrapped_lines.shift)
          next_num_wrapped_lines += 1 if !wrapped_lines.empty?
        end
      end
      print "\n"
      num_wrapped_lines = next_num_wrapped_lines
    end
    @cached_wrapped_lines = nil
  end

  # print one column in a row of stats
  def print_stat(stat_params, read_stats)
    value = read_stats[stat_params[:name]]
    wrapped_lines = nil
    if blank?(value)
      printf("                    N/A")
    elsif stat_params[:numeric]
      printf("  %15s", commify(value.to_i))
      denom = read_stats[stat_params[:denom]]
      if !blank?(denom) && denom.to_i != 0
        printf(" (%2u%%)", (value.to_i * 100 / denom.to_i).round)
      else
        printf("      ")
      end
    elsif stat_params[:wrap] && value.size > @value_width
      wrapped_lines = value.gsub(/(.{1,#{@value_width}})(\s+|_|-|$)/,
                                 "\\1\\2\n").strip.split("\n")
      printf(" %#{@value_width}s", wrapped_lines.shift)
    else
      printf(" %#{@value_width}s", value)
    end
    @cached_wrapped_lines.push wrapped_lines
  end

  def commify(number, delimiter = ',')
    number.to_s.reverse.
      gsub(%r{([0-9]{3}(?=([0-9])))}, "\\1#{delimiter}").reverse
  end

  def skip_stat?(stat_params)
    return false unless stat_params[:optional]
    name = stat_params[:name]
    @stats.each do |lane_stats|
      if stat_params[:pair]
        return false if !blank?(lane_stats[:pair_stats][name])
      else
        return false if !blank?(lane_stats[:read1_stats][name])
        return false if @paired && !blank?(lane_stats[:read2_stats][name])
      end
    end
    true
  end

  def missing_barcode_stat?(name, barcode_list)
    barcode_list.each do |bcinfo|
      return false if !blank?(bcinfo[:stats][name])
    end
    true
  end

  # print URLs or paths to retrieve data
  def report_data_location
    puts ""
    if @paths
      puts "Data is located on the scg1 compute cluster as indicated below."
    else
      puts "Data may be downloaded using the URLs below."
    end
    @stats.each do |lane_stats|
      lane = lane_stats[:read1_stats]["Lane"]
      sample = lane_stats[:read1_stats]["Sample"]
      if lane_stats[:read1_stats]["barcodes"].empty?
        puts ""
        puts "Run #{@run_name}, Lane #{lane}:"
        puts "  Sample name: #{sample}" unless blank?(sample)
        print_locations(lane)
      else
        lane_stats[:read1_stats]["barcodes"].each do |bcinfo|
          barcode_sample = bcinfo[:stats]["Sample"]
          puts ""
          puts "Run #{@run_name}, Lane #{lane}, Barcode #{bcinfo[:barcode]}"
          puts "  Library name: #{sample}" unless blank?(sample)
          puts "  Barcoded sample name: #{barcode_sample}" unless
            blank?(barcode_sample)
          print_locations(lane, :barcode => bcinfo[:barcode])
        end
        puts ""
        puts "Run #{@run_name}, Lane #{lane}, Unmatched Reads"
        puts "  Library name: #{sample}" unless blank?(sample)
        print_locations(lane, :barcode => "unmatched",
                        :eland => false, :sgr => false, :bed => false)
      end
    end
  end

  def print_locations(lane, opts = {})
    @@FileTypes.each do |type_info|
      print_type = true
      type_info[:args].each do |arg|
        print_type &&= instance_variable_get("@#{arg}")
        print_type &&= opts[arg] unless opts[arg].nil?
      end
      next unless print_type
      found = false
      type_info[:extensions].each do |extension|
        found = print_locations_for_file_type(lane, opts[:barcode], extension,
                                              type_info[:label])
        break if found
      end
      puts "WARNING: could not find: #{type_info[:label]}" if !found
    end
  end

  def print_locations_for_file_type(lane, barcode, extension, label)
    if @paired
      result = print_file_location(lane, barcode, 1, extension,
                                   label + " (Read 1)")
      return false if !result
      return print_file_location(lane, barcode, 2, extension,
                                 label + " (Read 2)")
    else
      return print_file_location(lane, barcode, 1, extension, label)
    end
  end

  def print_file_location(lane, barcode, read_number, extension, label)
    filename = "#{@run_name}_L#{lane}"
    filename += "_#{barcode}" unless barcode.nil?
    filename += "_#{read_number}" if @paired
    filename += extension + ".gz"

    if @archive_dir
      path = "#{@archive_dir}/#{filename}"
    else
      path = "#{@@ArchiveRoot}/#{@run_dir}/#{filename}"
    end

    return false if !File.exists?(path)
    size = File.size(path)
    if size == 0
      STDERR.puts "WARNING: empty file #{path}"
      return false
    end
    puts ""
    puts "  #{label}, Compressed (#{commify(size)} bytes)"
    if @paths
      puts "  #{path}"
    else
      url = "#{@@UrlRoot}/#{@run_dir}/#{filename}"
      puts "  #{url}"
    end

    return true
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
    check_for_paired_end
    load_stats
    report_lane_stats
    @stats.each {|lane_stats| report_barcode_stats(lane_stats)}
    report_data_location
  end

end

ReportIlluminaResults.new.main
