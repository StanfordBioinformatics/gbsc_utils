#!/usr/bin/env ruby

#
# prepare_run_report.rb: create report for a flow cell at end of an
# analysis run
#
# Phil Lacroute
#

require 'optparse'
require 'fileutils'

class PrepareRunReport

  @@Program = "prepare_run_report.rb"
  @@ArchiveRoot = "/srv/gs1/projects/scg/Archive/IlluminaRuns"

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

  # command-line options
  attr :run_name
  attr :archive_dir
  attr :verbose

  # parse command-line options
  def parse_args
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: #{$0} [options]"
      opts.separator "Options:"

      opts.on("--run RUN", "run name") do |run|
        @run_name = run
      end

      opts.on("--archive DIR",
              "archive directory for the run") do |dir|
        @archive_dir = dir
      end

      opts.on("--verbose", "print status messages to STDERR") do
        @verbose = true
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

    die "--run option is required" if @run_name.nil?

    if !@archive_dir
      year = @run_name[0..1].to_i + 2000
      month = @@MonthNames[@run_name[2..3]]
      @archive_dir = "#{@@ArchiveRoot}/#{year}/#{month}/#{@run_name}"
    end

  end

  def report_illumina_results
    filename = "#{@archive_dir}/run_report.txt"
    cmd = "report_illumina_results.rb --run #{@run_name} " +
      "--archive #{@archive_dir} --fastq > #{filename}.tmp"
    STDERR.puts "Running: #{cmd}" if @verbose
    system(cmd) || die("error: report_illumina_results.rb failed: #{$?}")
    finalize(filename)
  end

  def create_manifest
    filename = "#{@archive_dir}/#{@run_name}_manifest.csv"
    cmd = "create_analysis_manifest.rb --archive #{@archive_dir} " +
      "> #{filename}.tmp"
    STDERR.puts "Running: #{cmd}" if @verbose
    system(cmd) || die("error: create_analysis_manifest.rb failed: #{$?}")
    finalize(filename)
  end

  def finalize(filename)
    FileUtils.chmod(0444, "#{filename}.tmp", :verbose => @verbose)
    FileUtils.mv("#{filename}.tmp", filename, :verbose => @verbose)
  end

  # print an error message and exit
  def die(msg)
    STDERR.puts "#{@@Program}: #{msg}"
    exit 1
  end

  def main
    File.umask(0002)
    parse_args
    report_illumina_results
    create_manifest
  end

end

PrepareRunReport.new.main
