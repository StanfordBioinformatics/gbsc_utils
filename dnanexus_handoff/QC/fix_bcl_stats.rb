#!/usr/bin/env ruby

# repair Illumina BaseCalls directory with missing stats files
# to use: cd to rundir/Data/Intensities/BaseCalls and run

require 'optparse'
require 'fileutils'

class FixBclStats

  @@Program = "fix_bcl_stats.rb"

  @@Tiles = {
    :hiseq => [ 1,  2,  3,  4,  5,  6,  7,  8,
                21, 22, 23, 24, 25, 26, 27, 28,
                41, 42, 43, 44, 45, 46, 47, 48,
                61, 62, 63, 64, 65, 66, 67, 68 ],
    :ga2x => (1..120).to_a
  }

  attr :cycles
  attr :platform

  # parse command-line options
  def parse_args
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: #{@@Program} [options]"
      opts.separator "Options:"

      opts.on("--cycles NUM", Integer, "number of cycles") do |num|
        @cycles = num
      end

      opts.on("--platform TYPE", [:ga2x, :hiseq],
              "platform (ga2x or hiseq)") do |type|
        @platform = type
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

    die "--cycles is required" if @cycles.nil?
    die "--platform is required" if @platform.nil?
  end

  def fix_bcl
    (1..8).each do |lane|
      puts "Lane #{lane}..."
      (1..@cycles).each do |cycle|
        @@Tiles[@platform].each do |tile|
          filename = bcl_stats_filename(lane, cycle, tile)
          next if File.exist?(filename)
          puts "*** missing #{filename}"
          (1..@cycles).each do |other_cycle|
            next if other_cycle == cycle
            other_filename = bcl_stats_filename(lane, other_cycle, tile)
            next if !File.exist?(other_filename)
            puts "copying #{other_filename}"
            FileUtils.cp(other_filename, filename, :verbose => true)
            break
          end
        end
      end
    end
  end

  def bcl_stats_filename(lane, cycle, tile)
    "L00#{lane}/C#{cycle}.1/s_#{lane}_#{tile}.stats"
  end

  def main
    parse_args
    fix_bcl
  end
end

FixBclStats.new.main
