#!/usr/bin/env ruby

#
# illumina_tile_metrics.rb: produce statistics from an Illumina tile
# metrics interop files.
#
# Phil Lacroute
#

require 'optparse'

class IlluminaTileMetrics

  CLUSTER_DENSITY_CODE = 100
  PF_CLUSTER_DENSITY_CODE = 101
  CLUSTER_COUNT_CODE = 102
  PF_CLUSTER_COUNT_CODE = 103
  PHASING_MIN_CODE = 200
  PHASING_MAX_CODE = 299
  ALIGNED_MIN_CODE = 300
  ALIGNED_MAX_CODE = 399
  CTRLLANE_CODE    = 400

  def parse_args
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: illumina_tile_metrics.rb options"
      opts.separator "Options:"

      opts.on("--tile_metrics FILE",
              "tile metrics metrics input filename",
              "(e.g. TileMetricsOut.bin)") do |file|
        @tile_metrics_file = file
      end

      opts.on("--stats FILE", "output statistics file") do |file|
        @stats_file = file
      end

      opts.on("--lane NUM", "lane number (required)") do |num|
        @lane = num.to_i
      end

      opts.on("--verbose", "print verbose messages") do
        @verbose = true
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

    if @tile_metrics_file.nil?
      STDERR.puts "error: --tile_metrics is required"
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
    puts "Reading #{@tile_metrics_file}:" if @verbose
    @metrics = Hash.new
    (1..8).each do |lane|
      @metrics[lane] = {
        :tiles => Hash.new,
        :cluster_densities => Array.new,
        :pf_cluster_densities => Array.new,
        :cluster_count => 0.0,
        :pf_cluster_count => 0.0,
        :phasing => Array.new,
        :prephasing => Array.new,
        :pct_align => Array.new
      }
    end
    ios = File.open(@tile_metrics_file, "rb")
    version = readb(ios, 1, 'C', :required => true, :single => true)
    puts "Version: #{version}" if @verbose
    case version
    when 2
      read_tile_metrics_v2(ios)
    else
      STDERR.puts "error: invalid file format version number #{version}"
      exit 1
    end
    ios.close
  end

  def read_tile_metrics_v2(ios)
    record_len = readb(ios, 1, 'C', :required => true, :single => true)
    puts "Record Length: #{record_len}" if @verbose
    @read_cnt = 0
    eof = false
    while !eof do
      record = readb(ios, record_len, 'S3F1')
      break if record.nil?
      lane = record[0]
      tile = record[1]
      code = record[2]
      value = record[3]
      @metrics[lane][:tiles][tile] = true
      if code == CLUSTER_DENSITY_CODE
        @metrics[lane][:cluster_densities].push value
      elsif code == PF_CLUSTER_DENSITY_CODE
        @metrics[lane][:pf_cluster_densities].push value
      elsif code == CLUSTER_COUNT_CODE
        @metrics[lane][:cluster_count] += value
      elsif code == PF_CLUSTER_COUNT_CODE
        @metrics[lane][:pf_cluster_count] += value
      elsif code >= PHASING_MIN_CODE && code <= PHASING_MAX_CODE
        read_idx = (code - PHASING_MIN_CODE) / 2
        @read_cnt = [@read_cnt, read_idx + 1].max
        if (code - PHASING_MIN_CODE) % 2 == 0
          data = @metrics[lane][:phasing]
        else
          data = @metrics[lane][:prephasing]
        end
        data[read_idx] = { :list => Array.new } if data[read_idx].nil?
        data[read_idx][:list].push value
      elsif code >= ALIGNED_MIN_CODE && code <= ALIGNED_MAX_CODE
        read_idx = code - ALIGNED_MIN_CODE
        @read_cnt = [@read_cnt, read_idx + 1].max
        data = @metrics[lane][:pct_align]
        data[read_idx] = { :list => Array.new } if data[read_idx].nil?
        data[read_idx][:list].push value
      elsif code == CTRLLANE_CODE
        STDERR.puts "Control Lane: #{value.to_i}" if @verbose
      else
        STDERR.puts "WARNING: unexpected record code #{code}"
      end
    end

    (1..8).each do |lane|
      data = @metrics[lane]
      next if data[:phasing].length() == 0  # Skip unused lanes.
      data[:tile_cnt] = data[:tiles].size
      data[:cluster_density] = median(data[:cluster_densities])
      data[:pf_cluster_density] = median(data[:pf_cluster_densities])
      (0..(@read_cnt-1)).each do |idx|
        data[:phasing][idx][:min] = data[:phasing][idx][:list].min
        data[:phasing][idx][:median] = median(data[:phasing][idx][:list])
        data[:phasing][idx][:max] = data[:phasing][idx][:list].max

        data[:prephasing][idx][:min] = data[:prephasing][idx][:list].min
        data[:prephasing][idx][:median] = median(data[:prephasing][idx][:list])
        data[:prephasing][idx][:max] = data[:prephasing][idx][:list].max

        if !data[:pct_align][idx].nil?
          data[:pct_align][idx][:min] = data[:pct_align][idx][:list].min
          data[:pct_align][idx][:median] = median(data[:pct_align][idx][:list])
          data[:pct_align][idx][:max] = data[:pct_align][idx][:list].max
        end
      end
    end
  end

  def median(list)
    sorted_list = list.sort
    sorted_list[sorted_list.size / 2]
  end

  def make_stats
    return if @stats_file.nil?

    ios = File.new(@stats_file, "w")
    data = @metrics[@lane]
    ios.puts "Tile Count: #{data[:tile_cnt]}"
    ios.puts "Cluster Count: #{data[:cluster_count].round.to_i}"
    ios.puts "Post-Filter Cluster Count: #{data[:pf_cluster_count].round.to_i}"
    ios.puts "Median Cluster Density: #{data[:cluster_density].round.to_i}"
    ios.puts "Median Post-Filter Cluster Density: #{data[:pf_cluster_density].round.to_i}"
    ios.puts "Read Count: #{@read_cnt}"
    (0..(@read_cnt-1)).each do |idx|
      if !data[:phasing][idx].nil?
        phasing = data[:phasing][idx]
        ios.puts "Minimum Phasing Read #{idx+1}: #{'%.6f' % phasing[:min]}"
        ios.puts "Median Phasing Read #{idx+1}: #{'%.6f' % phasing[:median]}"
        ios.puts "Maximum Phasing Read #{idx+1}: #{'%.6f' % phasing[:max]}"
      end

      if !data[:prephasing][idx].nil?
        prephasing = data[:prephasing][idx]
        ios.puts "Minimum Prephasing Read #{idx+1}: #{'%.6f' % prephasing[:min]}"
        ios.puts "Median Prephasing Read #{idx+1}: #{'%.6f' % prephasing[:median]}"
        ios.puts "Maximum Prephasing Read #{idx+1}: #{'%.6f' % prephasing[:max]}"
      end
    end
  end

  def main
    parse_args
    read_metrics
    make_stats
  end
end

IlluminaTileMetrics.new.main
