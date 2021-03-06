#!/usr/bin/env ruby

#
# illumina_qscores.rb: produce statistics from an Illumina quality-metrics
# interop file.
#
# Phil Lacroute
#

require 'optparse'
require 'tempfile'

class IlluminaQScores

  def initialize
    @counts = Hash.new
    @max_cycle = 0
    @min_qual = 1
    @max_qual = 50
  end

  def parse_args
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: illumina_qscores.rb options"
      opts.separator "Options:"

      opts.on("--qmetrics FILE",
              "input filename (e.g. QMetricsOut.bin, required)") do |file|
        @qmetrics_file = file
      end

      opts.on("--details_plot FILE", "detailed plot output file") do |file|
        @details_plot = file
      end

      opts.on("--summary_plot FILE", "summary plot output file") do |file|
        @summary_plot = file
      end

      opts.on("--lane NUM", "lane number (required)") do |num|
        @lane = num.to_i
      end

      opts.on("--read_lengths LENGTH1,LENGTH2,LENGTH3", Array,
              "read lengths (bases)") do |list|
        @read_lengths = list
      end

      opts.on("--force", "Continue past some error conditions") do
         @force = true
      end

      opts.on("--verbose", "print verbose messages") do
        @verbose = true
      end

      opts.on("--debug", "print debugging messages") do
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

    if @qmetrics_file.nil?
      STDERR.puts "error: --qmetrics is required"
      exit 1
    end

    if @lane.nil?
      STDERR.puts "error: --lane is required"
      exit 1
    end
  end

  def readb(ios, bytecnt, format, opts = {})
    rawdata = ios.read(bytecnt)
    if rawdata.nil?
      if opts[:required]
        STDERR.puts "error: input file is truncated"
        exit 1
      else
        return nil
      end
    end
    data = rawdata.unpack(format)
    if opts[:single]
      return data[0]
    else
      return data
    end
  end

  def read_metrics
    puts "Reading #{@qmetrics_file}:" if @verbose
    (1..8).each {|lane| @counts[lane] = Hash.new}
    ios = File.open(@qmetrics_file, "rb")
    version = readb(ios, 1, 'C', :required => true, :single => true)
    puts "Version: #{version}" if @verbose
    case version
    when 4
      read_metrics_v4(ios)
    else
      STDERR.puts "error: invalid file format version number #{version}"
      exit 1
    end
    ios.close
  end

  def read_metrics_v4(ios)
    record_len = readb(ios, 1, 'C', :required => true, :single => true)
    puts "Record Length: #{record_len}" if @verbose
    eof = false
    while !eof do
      record = readb(ios, record_len, 'S3L50')
      break if record.nil?
      lane = record[0]
      tile = record[1]
      cycle = record[2]
      @max_cycle = cycle if cycle > @max_cycle
      if @counts[lane].nil?
        STDERR.puts "read_metrics_v4(): error: invalid lane #{lane}"
        if @force
          next
        else
          exit 1
        end
      end
      if @counts[lane][cycle].nil?
        @counts[lane][cycle] = Hash.new
      end
      @counts[lane][cycle][tile] = Hash.new if @counts[lane][cycle][tile].nil?
      ccounts = @counts[lane][cycle][tile]
      (1..50).each do |score|
        # Don't know why Phil was adding these across all the tiles, but it
        # seems that only the last record for any lane/tile/cycle is valid.
        # ccounts[score] = 0 if ccounts[score].nil?
        # ccounts[score] += record[(score - 1) + 3]
        ccounts[score] = record[(score - 1) + 3]
        #print "#{ccounts[score]} " if @debug
      end
      #print "\n" if @debug
    end
    puts "Found #{cycle} cycles." if @verbose
  end

  def make_plots
    tmpio = Tempfile.new('interop')
    puts "Writing data to #{tmpio.path}..." if @verbose

    # print banner
    (@min_qual..@max_qual).each do |qual|
      tmpio.print "q#{qual} "
      print "q#{qual} " if @debug
    end
    tmpio.print "\n"
    print "\n" if @debug

    # for each cycle, print number of bases with each quality value
    (1..@max_cycle).each do |cycle|
      (@min_qual..@max_qual).each do |qual|
        tiles_total = 0
        if not @counts[@lane][cycle].nil?
          @counts[@lane][cycle].keys.sort.each do |tile|
            tiles_total += @counts[@lane][cycle][tile][qual]
          end
          tmpio.print "#{tiles_total} "
          print "#{tiles_total} " if @debug
        end
      end
      tmpio.print "\n"
      print "\n" if @debug
    end

    tmpio.close

    if !@read_lengths.nil?
      @read_starts = []
      cycle = 1
      @read_lengths.each do |len|
        @read_starts.push(cycle) unless cycle == 1
        cycle += len.to_i
      end
    end

    run_plotter("plot_qscore_details.r", tmpio.path, @details_plot)
    run_plotter("plot_qscore_summary.r", tmpio.path, @summary_plot)

    tmpio.unlink
  end

  def run_plotter(plotscript, datafile, plotfile)
    return if plotfile.nil?
    plotcmd = ("#{plotscript} datafile=\\\"#{datafile}\\\" " +
               "plotfile=\\\"#{plotfile}\\\"")
    if !@read_lengths.nil?
      plotcmd += " read.starts=c\\(#{@read_starts.join(',')}\\)"
    end
    puts "Running cmd: #{plotcmd}" if @verbose
    if !system(plotcmd)
      STDERR.puts "error running R to make plot"
      exit 1
    end
  end

  def print_lane_metrics(lane)
    puts "Lane #{lane}:"
    (1..@max_cycle).each do |cycle|
      print "Cycle #{cycle}:"
      ccounts = @counts[lane][cycle]
      total_q20 = 0
      total_q30 = 0
      total = 0
      weighted_sum = 0
      (@min_qual..@max_qual).each do |qual|
        total_q20 += ccounts[qual] if qual >= 20
        total_q30 += ccounts[qual] if qual >= 30
        total += ccounts[qual]
        weighted_sum += qual * ccounts[qual]
      end
      average = "%.2f" % (weighted_sum.to_f / total.to_f)
      q20_pct = "%.2f" % (100.0 * total_q20.to_f / total.to_f)
      q30_pct = "%.2f" % (100.0 * total_q30.to_f / total.to_f)
      print " average #{average}, #{q30_pct}% >= Q30, #{q20_pct}% >= Q20\n"
    end
  end

  def main
    parse_args
    read_metrics
    make_plots
  end
end

IlluminaQScores.new.main
