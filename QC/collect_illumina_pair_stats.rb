#!/usr/bin/env ruby

require 'optparse'
require 'fileutils'
require 'rexml/document'
include REXML

class CollectIlluminaPairStats

  @@Program = "collect_illumina_pair_stats.rb"

  @@Params = [ "Read 1 Total",
               "Read 1 Post-Filter",
               "Read 2 Total",
               "Read 2 Post-Filter",
               "Min Insert Size",
               "Max Insert Size",
               "Median Insert Size",
               "Consistent Unique Pairs",
               "Rescued Pairs",
               "Total Consistent Pairs" ]

  # command-line options
  attr :run_name
  attr :lanes
  attr :index_seq
  attr :gerald_dir
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

      opts.on("--index SEQ", "reads are indexed with sequence SEQ") do |seq|
        @index_seq = seq
      end

      opts.on("--gerald_dir DIR",
              "GERALD directory containing Summary.xml file") do |dir|
        @gerald_dir = dir
      end

      opts.on("--archive_dir DIR", "directory for result files") do |dir|
        @archive_dir = dir
      end

      opts.on("--verbose", "enable verbose output") do
        @verbose = true
      end

      opts.on("--summary_file FILE", "summary XML file to be analyzed") do |file|
        @summary_file = file
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
    #die "--gerald_dir is required" if blank?(@gerald_dir)
    die "--archive_dir is required" if blank?(@archive_dir)

    @lane_numbers = []
    lane_digits = @lanes.split(//)
    lane_digits.each do |digit|
      lane_num = digit.to_i
      @lane_numbers.push lane_num
      @lane_stats[lane_num] = {}
    end
  end

  # read the Summary.xml file from GERALD
  def read_summary_xml(summary_xml_file)
    STDERR.puts "Reading Summary XML file..." if @verbose
    doc = Document.new(summary_xml_file)
    doc.elements.each("Summary/TileResultsByLane/Lane") do |lane_elem|
      lane_number = lane_elem.elements["laneNumber"].text.to_i
      next unless @lane_numbers.include?(lane_number)
      STDERR.puts "Reading lane #{lane_number} from Summary.xml..." if @verbose
      lane_elem.elements.each("Read") do |read_elem|
        read_number = read_elem.elements["readNumber"].text.to_i
        STDERR.print "  Read #{read_number}:" if @verbose
        raw_clusters = 0
        pf_clusters = 0
        tile_count = 0
        read_elem.elements.each("Tile") do |tile_elem|
          tile_number = tile_elem.elements["tileNumber"].text.to_i
          STDERR.print " #{tile_number}" if @verbose
          tile_count += 1
          raw_clusters += tile_elem.elements["clusterCountRaw"].text.to_i
          pf_clusters += tile_elem.elements["clusterCountPF"].text.to_i
        end
        STDERR.print "\n" if @verbose
        if tile_count != 32 && tile_count != 48 && tile_count != 100 && tile_count != 120
          warn "Summary.xml lane #{lane_number}: unexpected tile count #{tile_count}"
        end

        lstats = @lane_stats[lane_number]
        lstats["Read #{read_number} Total"] = raw_clusters
        lstats["Read #{read_number} Post-Filter"] = pf_clusters
      end
    end

    doc.elements.each("Summary/PairSummary") do |pair_elem|
      lane_number = pair_elem.elements["laneNumber"].text.to_i
      next unless @lane_numbers.include?(lane_number)
      pair_filename = pair_elem.elements["fileName"].text
      pair_file = File.new("#{@gerald_dir}/#{pair_filename}")
      pair_doc = Document.new(pair_file)
        
      insert_elem = pair_doc.elements["ReadPairProperties/InsertSize"]
      if insert_elem.nil?
        insert_min = 0
        insert_max = 0
        insert_median = 0
        insert_pair_cnt = 0
      else
        insert_min = insert_elem.elements["Min"].text.to_i
        insert_max = insert_elem.elements["Max"].text.to_i
        insert_median = insert_elem.elements["Median"].text.to_i
        pairs_elem = pair_doc.elements["ReadPairProperties/Pairs"]
        insert_pair_cnt =
          pairs_elem.elements["ClustersUsedToComputeInsert"].text.to_i
      end
        
      unique_pairs = 0
      rescued_pairs = 0
      reads_elem = pair_doc.elements["ReadPairProperties/Reads"]
      if not reads_elem.nil?
        unique_paths = [
                        "Read1SingleAlignmentFound/Read2SingleAlignmentFound/" +
                        "UniquePairedAlignment"
                       ]
        unique_paths.each do |path|
          if !reads_elem.elements[path].nil?
            unique_pairs += reads_elem.elements[path].text.to_i
          end
        end
        rescued_paths = [
                         "Read1ManyAlignmentsFound/Read2ManyAlignmentsFound/" +
                         "UniquePairedAlignment",
                         "Read1ManyAlignmentsFound/Read2SingleAlignmentFound/" +
                         "UniquePairedAlignment",
                         "Read1SingleAlignmentFound/Read2ManyAlignmentsFound/" +
                         "UniquePairedAlignment",
                        ]
        rescued_paths.each do |path|
          if !reads_elem.elements[path].nil?
            rescued_pairs += reads_elem.elements[path].text.to_i
          end
        end
      else
        warn "collect_illumina_pair_stats.rb: ReadPairProperties has no Reads attribute."
      end
      
      lstats = @lane_stats[lane_number]
      lstats["Min Insert Size"] = insert_min
      lstats["Max Insert Size"] = insert_max
      lstats["Median Insert Size"] = insert_median
      lstats["Consistent Unique Pairs"] = unique_pairs
      lstats["Rescued Pairs"] = rescued_pairs
      lstats["Total Consistent Pairs"] = unique_pairs + rescued_pairs
      
      pair_file.close
    end
  end

  def make_lane_report(lane_num)
    lane_stats_file = "#{@archive_dir}/#{@run_name}_L#{lane_num}"
    lane_stats_file += "_#{@index_seq}" unless @index_seq.nil?
    lane_stats_file += "_pair_stats.txt"
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
    File.umask(0002)
    parse_options

    if @summary_file.nil?
      summary_xml_file = File.new("#{@gerald_dir}/Summary.xml")
    else
      summary_xml_file = @summary_file
    end

    read_summary_xml summary_xml_file
    @lane_numbers.each {|lane_num| make_lane_report(lane_num)}
  end

end

CollectIlluminaPairStats.new.main
