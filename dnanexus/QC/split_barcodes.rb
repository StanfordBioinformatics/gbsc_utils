#!/usr/bin/env ruby

#
# split_barcodes.rb: split a fastq file into multiple fastq files
#                    based on molecular barcodes internal to the sequences
#
# Phil Lacroute
#

require 'optparse'
require 'ostruct'
require 'tempfile'
require 'fileutils'

class SplitBarcodes

  @@Program = "split_barcodes.rb"

  # external programs
  @@Splitter = "fastx_barcode_splitter.pl"
  @@Trimmer = "fastx_trimmer"
  @@Decompressor = "zcat -f"

  # name for file containing reads that don't match any barcode
  @@Unmatched = "unmatched"

  # command-line options
  attr :barcodes
  attr :in_filename
  attr :prefix
  attr :suffix
  attr :position
  attr :mismatches
  attr :strip_barcodes
  attr :stats_filename
  attr :decompress
  attr :compress
  attr :verbose
  attr :tmpdir

  attr :make_intermediate
  attr :tmpdir_prefix
  attr :tmpdir_suffix
  attr :resultdir_prefix
  attr :resultdir_suffix
  attr :barcode_list_file

  def initialize
    # set defaults for command-line options
    @in_filename = "-"
    @position = :bol
    @mismatches = 0

    # The value to subtract from all quality values.
    @quality_base = 64
  end

  # parse command-line options
  def parse_args
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: #{@@Program} [options]"
      opts.separator "Options:"

      opts.on("--barcodes LIST", Array,
              "comma-separated list of barcodes (required)") do |list|
        @barcodes = list
      end

      opts.on("--in FILE",
              "fastq input file (default is standard input)") do |file|
        @in_filename = file
      end

      opts.on("--prefix STR",
              "prefix for output file paths (required)") do |str|
        @prefix = str
      end

      opts.on("--suffix STR",
              "suffix for output file paths") do |str|
        @suffix = str
      end

      opts.on("--position POS", [:bol, :eol],
              "barcode position:",
              "bol (beginning of line, default)",
              "eol (end of line)") do |pos|
        @position = pos
      end

      opts.on("--mismatches NUM",
              "number of mismatches allowed in barcode",
              "(default 0)") do |num|
        @mismatches = num
      end

      opts.on("--strip", "strip barcodes from output") do
        @strip_barcodes = true
      end

      opts.on("--stats FILE", "statistics output file") do |file|
        @stats_filename = file
      end

      opts.on("--decompress", "decompress input file") do
        @decompress = true
      end

      opts.on("--compress", "compress fastq output files") do
        @compress = true
      end

      opts.on("--verbose", "print status messages to STDERR") do
        @verbose = true
      end

      opts.on("--tmpdir DIR", "directory for temporary files") do |dir|
        @tmpdir = dir
      end

      opts.on("--sanger", "use Sanger quality codes, not Illumina [default = false]") do
        @quality_base = 33
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

    die "--barcodes option is required" if @barcodes.nil? || @barcodes.empty?
    die "--prefix option is required" if @prefix.nil?

    @tmpdir = ENV['TMPDIR'] if @tmpdir.nil?
    @tmpdir = Dir.tmpdir if @tmpdir.nil?
    @tmpdir = "/tmp" if @tmpdir.nil?

    # decide if we need to generate intermediate files
    @make_intermediate = @strip_barcodes || @compress

    if @make_intermediate
      # put intermediate files in tmpdir
      @tmpdir_prefix = "#{@tmpdir}/split_barcodes_#{Process.pid}_"
      @tmpdir_suffix = ".fastq"
    end

    # generate the final output in the result directory but append .tmp
    # to each file name until it has been successfully generated
    @resultdir_prefix = @prefix
    @resultdir_suffix = @suffix + ".tmp"
  end

  def prepare_barcodes
    # make a temporary file containing the list of barcodes
    @barcode_list_file = Tempfile.new("split_barcodes", @tmpdir)
    STDERR.puts "Barcode file: #{@barcode_list_file.path}" if @verbose
    @barcodes.each do |barcode|
      @barcode_list_file.puts "#{barcode}\t#{barcode}"
    end
    @barcode_list_file.close
  end

  def run_fastx_barcode_splitter
    if @make_intermediate
      splitter_prefix = @tmpdir_prefix
      splitter_suffix = @tmpdir_suffix
    else
      splitter_prefix = @resultdir_prefix
      splitter_suffix = @resultdir_suffix
    end

    splitter = [ @@Splitter,
                 "--bcfile #{@barcode_list_file.path}",
                 "--prefix #{splitter_prefix}",
                 "--#{@position}",
                 "--mismatches #{@mismatches}" ]
    splitter.push "--suffix #{splitter_suffix}" unless splitter_suffix.nil?
    if @stats_filename.nil?
      splitter.push "--quiet"
    else
      splitter.push " > #{@stats_filename}"
    end

    if @decompress
      splitter.unshift "set -o pipefail && #{@@Decompressor} #{@in_filename} |"
    else
      splitter.push " < #{@in_filename}" unless @in_filename == "-"
    end

    cmd = splitter.join(" ")
    STDERR.puts "Running: #{cmd}" if @verbose
    system(cmd) || die("error: barcode splitter failed: #{$?}")
  end

  def generate_output_files
    split_files = Array.new(@barcodes)
    split_files.push(@@Unmatched)
    split_files.each do |barcode|
      resultdir_file = "#{@resultdir_prefix}#{barcode}#{@resultdir_suffix}"
      final_file = "#{@prefix}#{barcode}#{@suffix}"
      if @make_intermediate
        tmpdir_file = "#{@tmpdir_prefix}#{barcode}#{@tmpdir_suffix}"
        #
        # Test if tmpdir_file is zero-sized.
        #
        if not File.zero? tmpdir_file
          if @strip_barcodes && barcode != @@Unmatched
            cmd = "#{@@Trimmer} -f #{barcode.size + 1}"
            cmd += " -Q #{@quality_base}"
            cmd += " -z" if @compress
          elsif @compress
            cmd = "gzip -cf"
          else
            cmd = "cat"
          end
          cmd += " < #{tmpdir_file} > #{resultdir_file}"
          STDERR.puts "Running: #{cmd}" if @verbose
          system(cmd) || die("error: cannot generate #{barcode}: #{$?}")
          STDERR.puts "Removing #{tmpdir_file}" if @verbose
          FileUtils.rm(tmpdir_file)
        else
          if @compress
            # Make compressed, empty file.
            cmd = "gzip -cf < /dev/null > #{resultdir_file}"
            STDERR.puts "Running: #{cmd}" if @verbose
            system(cmd) || die("error: cannot generate empty file for #{barcode}: #{$?}")
            STDERR.puts "Removing #{tmpdir_file}" if @verbose
            FileUtils.rm(tmpdir_file)
          else
            # Create empty result file.
            STDERR.puts "Moving empty #{tmpdir_file} to become #{resultdir_file}" if @verbose
            FileUtils.mv(tmpdir_file, resultdir_file)
          end
        end
      end
      STDERR.puts "Moving #{resultdir_file} to #{final_file}" if @verbose
      FileUtils.mv(resultdir_file, final_file)
    end
  end

  def cleanup
    @barcode_list_file.unlink
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
    prepare_barcodes
    run_fastx_barcode_splitter
    generate_output_files
    cleanup
  end
end

SplitBarcodes.new.main
