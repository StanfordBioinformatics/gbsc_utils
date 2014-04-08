#!/usr/bin/env ruby

#
# qseq2fastq.rb: convert Illumina qseq files into a fastq file
#
# Phil Lacroute
#

require 'optparse'
require 'zlib'
require 'English'

class Qseq2Fastq

  @@Program = "qseq2fastq.rb"

  # command-line options
  attr :out_filename
  attr :pass_filename
  attr :reject_filename
  attr :stats_filename
  attr :compress
  attr :stats_only
  attr :verbose

  # file objects
  attr :pass
  attr :reject

  # statistics
  attr :total_read_cnt
  attr :pass_read_cnt

  def initialize
    # set defaults for command-line options
    @out_filename = "-"
    @total_read_cnt = 0
    @pass_read_cnt = 0
  end

  # parse command-line options
  def parse_args
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: #{@@Program} [options] qseq_file ..."
      opts.separator "qseq_file may include shell-style regular expressions"
      opts.separator "Options:"

      opts.on("--out FILE",
              "fastq output file (default stdout)") do |file|
        @out_filename = file
      end

      opts.on("--pass FILE",
              "fastq output file for reads that",
              "pass the quality filter (overrides --out)") do |file|
        @pass_filename = file
      end

      opts.on("--reject FILE",
              "fastq output file for reads rejected",
              "by the quality filter (overrides --out)") do |file|
        @reject_filename = file
      end

      opts.on("--stats FILE", "statistics output file") do |file|
        @stats_filename = file
      end

      opts.on("--compress", "compress fastq files with gzip") do
        @compress = true
      end

      opts.on("--stats_only", "generate statistics but no fastq files") do
        @stats_only = true
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

    if ARGV.empty?
      STDERR.puts "error: at least one qseq file must be specified"
      puts opts
      exit 1
    end
  end

  # open the output files, including setting up the compression library
  # if necessary
  def open_fastq_output_files
    return if @stats_only
    if @pass_filename.nil? && @reject_filename.nil?
      # put all reads in the same output file
      @pass = open_fastq_output(@out_filename)
      @reject = @pass
    else
      # split the reads that passed and the reads that failed
      # the quality filter into separate files; if either one
      # of the file names was not specified then discard the
      # corresponding reads
      @pass = open_fastq_output(@pass_filename) unless @pass_filename.nil?
      @reject = open_fastq_output(@reject_filename) unless @reject_filename.nil?
    end
  end

  # return an object for writing data to a fastq file (either a File
  # object or a Zlib::GzipWriter object)
  def open_fastq_output(filename)
    if @compress
      if filename == "-"
        return Zlib::GzipWriter.new(STDOUT, Zlib::BEST_COMPRESSION, nil)
      else
        begin
          return Zlib::GzipWriter.open(filename)
        rescue Exception => err
          die "cannot open #{filename}: #{err.to_s}"
        end
      end
    else
      if filename == "-"
        STDOUT
      else
        begin
          return File.open(filename, "w")
        rescue Exception => err
          die "cannot open #{filename}: #{err.to_s}"
        end
      end
    end
  end

  # close the fastq output files
  def close_fastq_output_files
    @reject.close unless @reject.nil? || @reject == STDOUT || @reject == @pass
    @pass.close unless @pass.nil? || @pass == STDOUT
  end

  # read the qseq files and write to the fastq files, plus collect stats
  def generate_fastq
    total_read_cnt = 0
    pass_read_cnt = 0
    ARGV.each do |qseq_arg|
      # expand metacharacters in the qseq file expression
      Dir.glob(qseq_arg).sort.each do |qseq_file|
	# convert one qseq file to fastq
	STDERR.puts "Processing #{qseq_file}..." if @verbose
        IO.foreach(qseq_file) do |line|
          line.chomp
          fields = line.split(" ")
          die "parse error at #{qseq_file}:#{$INPUT_LINE_NUMBER}" if
            fields.size != 11
          @total_read_cnt += 1
          machine, runid, lane, tile, dx, dy, idx, readid, seq, qual, pass =
            fields
          rname = "#{machine}:#{lane}:#{tile}:#{dx}:#{dy}##{idx}/#{readid}"
          seq.tr!('.', 'N')	# convert . to N
	  out = nil
          if pass == "1"
            out = @pass
            @pass_read_cnt += 1
          else
            out = @reject;
          end
          if !out.nil?
            out.print "@#{rname}\n"
            out.print "#{seq}\n"
            out.print "+#{rname}\n"
            out.print "#{qual}\n"
          end
        end # IO.foreach
      end # Dir.glob
    end # ARGV.each
  end

  # store the statistics in the stats output file
  def store_stats
    return if @stats_filename.nil?
    File.open(@stats_filename, "w") do |file|
      file.puts "Total Reads: #{total_read_cnt}"
      file.puts "Post-Filter Reads: #{pass_read_cnt}"
    end
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
    open_fastq_output_files
    generate_fastq
    close_fastq_output_files
    store_stats
  end
end

Qseq2Fastq.new.main
