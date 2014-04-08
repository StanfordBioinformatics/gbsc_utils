#!/usr/bin/env ruby

require 'optparse'
require 'fileutils'
require 'rexml/document'
include REXML

class CollectIlluminaBaseCallStats

  @@Program = "collect_illumina_base_call_stats.rb"

  @@Params = [ "Total Reads",
               "Post-Filter Reads" ]

  # command-line options
  attr :run_name
  attr :lanes
  attr :base_calls_dir
  attr :archive_dir
  attr :verbose

  attr :lane_numbers
  attr :lane_stats

  def initialize
    @lanes = "12345678"
    @lane_stats = {}
  end

  # parse command line options
  def parse_options
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: #{@@Program} options"

      opts.on("--run NAME", "run name (required)") do |name|
        @run_name = name
      end

      opts.on("--lanes STR", "lane numbers (default 12345678)") do |str|
        @lanes = str
      end

      opts.on("--base_calls_dir DIR",
              "directory containing BustardSummary.xml") do |dir|
        @base_calls_dir = dir
      end

      opts.on("--archive_dir DIR", "directory for result files") do |dir|
        @archive_dir = dir
      end

      opts.on("--verbose", "enable verbose output") do
        @verbose = true
      end

      opts.on_tail("--help", "Print help message") do
        STDERR.puts opts
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

    die "--run is required" if blank?(@run_name)
    die "invalid --lanes option: #{@lanes}" if @lanes !~ /^\d+$/
    die "--base_calls_dir is required" if blank?(@base_calls_dir)
    die "--archive_dir is required" if blank?(@archive_dir)

    @lane_numbers = []
    lane_digits = @lanes.split(//)
    lane_digits.each do |digit|
      lane_num = digit.to_i
      @lane_numbers.push lane_num
      @lane_stats[lane_num] = {}
    end
  end

  # read the BustardSummary.xml file from Bustard or BclConverter
  def read_summary_xml
    STDERR.puts "Reading BustardSummary.xml..." if @verbose
    summary_xml_file = File.new("#{@base_calls_dir}/BustardSummary.xml")
    doc = Document.new(summary_xml_file)
    doc.elements.each("BustardSummary/TileResultsByLane/Lane") do |lane_elem|
      lane_number = lane_elem.elements["laneNumber"].text.to_i
      next unless @lane_numbers.include?(lane_number)
      STDERR.puts "Reading lane #{lane_number} from Summary.xml..." if @verbose
      lane_elem.elements.each("Read") do |read_elem|
        read_number = read_elem.elements["readNumber"].text.to_i
        next if read_number != 1
        raw_clusters = 0
        pf_clusters = 0
        tile_count = 0
        read_elem.elements.each("Tile") do |tile_elem|
          tile_number = tile_elem.elements["tileNumber"].text.to_i
          tile_count += 1
          tile_raw = tile_elem.elements["clusterCountRaw"].text.to_i
          tile_pf = tile_elem.elements["clusterCountPF"].text.to_i
          STDERR.print " #{tile_number} #{tile_raw} #{tile_pf}\n" if @verbose
          raw_clusters += tile_raw
          pf_clusters += tile_pf
        end
        STDERR.print "\n" if @verbose
        if tile_count != 32 && tile_count != 100 && tile_count != 120
          warn "Summary.xml lane #{lane_number}: unexpected tile count #{tile_count}"
        end

        lstats = @lane_stats[lane_number]
        lstats["Total Reads"] = raw_clusters
        lstats["Post-Filter Reads"] = pf_clusters
      end
    end
  end

  def make_lane_report(lane_num)
    lane_stats_file = "#{@archive_dir}/#{@run_name}_L#{lane_num}"
    lane_stats_file += "_base_call_stats.txt"
    File.open("#{lane_stats_file}.tmp", "w") do |ios|
      ios.puts "Run: #{@run_name}"
      ios.puts "Lane: #{lane_num}"
      lstats = @lane_stats[lane_num]
      @@Params.each {|param| ios.puts "#{param}: #{lstats[param]}"}
    end
    FileUtils.chmod(0444, "#{lane_stats_file}.tmp")
    FileUtils.mv("#{lane_stats_file}.tmp", lane_stats_file)
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

  # main entry point: generate a statistics report
  def main
    parse_options
    read_summary_xml
    @lane_numbers.each {|lane_num| make_lane_report(lane_num)}
  end

end

CollectIlluminaBaseCallStats.new.main
