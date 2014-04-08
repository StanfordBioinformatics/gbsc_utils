#!/usr/bin/env ruby

#
# merge_split_fastq.rb: merge Illumina FASTQ files then split them
#                       into post-filter and reject FASTQ files.
#
# Phil Lacroute
# Keith Bettinger
#

require 'optparse'
require 'zlib'
require 'English'

class MergeSplitFastq

  @@Program = "merge_split_fastq.rb"

  # command-line options
  attr :out_filename
  attr :out_prefix
  attr :pass_filename
  attr :reject_filename
  attr :pass_dir
  attr :reject_dir
  attr :stats_filename
  attr :compress
  attr :stats_only
  attr :verbose

  # file objects
  attr :pass
  attr :reject
  attr :pass_sub
  attr :reject_sub

  # statistics
  attr :total_read_cnt
  attr :pass_read_cnt

  def initialize
    # set defaults for command-line options
    @compress = false
    @stats_only = false
    @remove_spaces = false
    @no_merge = false
    @verbose = false

    @pass_filename = nil
    @reject_filename = nil
    @stats_filename = nil

    @total_read_cnt  = 0
    @pass_read_cnt   = 0
    @reject_read_cnt = 0
    @pass_sub_read_cnt = @reject_sub_read_cnt = @total_sub_read_cnt = 0

  end

  # parse command-line options
  def parse_args
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: #{@@Program} [options] fastq_file ..."
      opts.separator "Options:"

      opts.on("--out FILE",
              "fastq output file (default stdout)") do |file|
        @out_filename = file
      end

      opts.on("--out_prefix FILE",
              "fastq output file prefix (overrides pass/reject switches)") do |file|
        @out_prefix = file
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

      opts.on("--pass_dir FILE",
              "directory to put fastq output file for reads that",
              "pass the quality filter (overrides --out)") do |file|
        @pass_dir = file
      end

      opts.on("--reject_dir FILE",
              "directory to put fastq output file for reads rejected",
              "by the quality filter (overrides --out)") do |file|
        @reject_dir = file
      end

      opts.on("--stats_dir FILE", "directory in which to put statistics output subpart files") do |file|
        @stats_dir = file
      end

      opts.on("--compress", "compress fastq files with gzip") do
        @compress = true
      end

      opts.on("--stats_only", "generate statistics but no fastq files") do
        @stats_only = true
      end

      opts.on("--remove_spaces", "remove spaces from the sequence names [default = false]") do
         @remove_spaces = true
      end

      opts.on("--save_subfiles", "save split files from each FASTQ file' [default = false]") do
         @save_subfiles = true
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

    @pass_dir = "." if @pass_dir.nil?
    @reject_dir = "." if @reject_dir.nil?

    # Deal with argument interactions.

    #if @pass_filename.nil?
    #  if not @out_prefix.nil?
    #    @pass_filename   = File.join(@pass_dir,   @out_prefix + "_pf.fastq")
    #    @pass_filename += ".gz" if @compress
    #  else
    #    STDERR.puts "no pass filename or out_prefix"
    #    puts opts
    #    exit 1
    #  end
    #end
    #
    #if @reject_filename.nil?
    #  if not @out_prefix.nil?
    #    @reject_filename = File.join(@reject_dir, @out_prefix + "_reject.fastq")
    #    @reject_filename += ".gz" if @compress
    #  else
    #    STDERR.puts "no reject filename or out_prefix"
    #    puts opts
    #    exit 1
    #  end
    #end

    if ARGV.empty?
      STDERR.puts "error: at least one fastq file must be specified"
      puts opts
      exit 1
    end
  end

  def make_temp_filename(filename)
    return filename + "_TEMP"
  end

  # open the global stats file, if it exists, and read in its data.
  #def read_global_stats_file
  #  if not @global_stats_filename.nil? and File.file? @global_stats_filename
  #    gs_file = open @global_stats_filename
  #    total_line = gs_file.readline
  #    pf_line    = gs_file.readline
  #    gs_file.close
  #
  #    if total_line =~ /^Total Reads: (\d+)$/
  #      @global_total_read_cnt = $1.to_i
  #    else
  #      die "global stats file #{@global_stats_filename}: malformed Total Reads line"
  #    end
  #
  #    if pf_line =~ /^Post-Filter Reads: (\d+)$/
  #       @global_pass_read_cnt = $1.to_i
  #    else
  #       die "global stats file #{@global_stats_filename}: malformed Post-Filter Reads line"
  #    end
  #
  #    @global_reject_read_cnt = @global_total_read_cnt - @global_pass_read_cnt
  #  end
  #end

  # open the output files, including setting up the compression library
  # if necessary
  def open_fastq_output_files
    return if @stats_only
    if @pass_filename.nil? && @reject_filename.nil? && ! @out_filename.nil?
      # put all reads in the same output file
      STDERR.puts "Opening #{@out_filename} for pass filter FASTQ output." if @verbose
      @pass   = open_fastq_output(make_temp_filename(@out_filename))
      @reject = @pass
    else
      # split the reads that passed and the reads that failed
      # the quality filter into separate files; if either one
      # of the file names was not specified then discard the
      # corresponding reads
      unless @pass_filename.nil?
        STDERR.puts "Opening #{make_temp_filename(@pass_filename)} for pass filter FASTQ output." if @verbose
        @pass   = open_fastq_output(make_temp_filename(@pass_filename))
      end
      unless @reject_filename.nil?
        STDERR.puts "Opening #{make_temp_filename(@reject_filename)} for reject filter FASTQ output." if @verbose
        @reject = open_fastq_output(make_temp_filename(@reject_filename))
      end
    end
  end

 # open the output subpart files, including setting up the compression library
 # if necessary
  def open_fastq_sub_output_files
    return if @stats_only
    if @pass_sub_filename.nil? && @reject_sub_filename.nil?
      # no files open
      @pass_sub = nil
      @reject_sub = nil
    else
      # split the reads that passed and the reads that failed
      # the quality filter into separate files; if either one
      # of the file names was not specified then discard the
      # corresponding reads
      unless @pass_sub_filename.nil?
        STDERR.puts "Opening #{make_temp_filename(@pass_sub_filename)} for subfile pass filter FASTQ output." if @verbose
        @pass_sub   = open_fastq_output(make_temp_filename(@pass_sub_filename))
      end
      unless @reject_sub_filename.nil?
        STDERR.puts "Opening #{make_temp_filename(@reject_sub_filename)} for subfile reject filter FASTQ output." if @verbose
        @reject_sub = open_fastq_output(make_temp_filename(@reject_sub_filename))
      end
    end
  end


  # return an object for writing data to a fastq file (either a File
  # object or a Zlib::GzipWriter object)
  def open_fastq_output(filename)
    if filename == '-'
      out_fp = STDOUT
    else
      begin
        out_fp = File.open(filename, "w")
      rescue Exception => err
        die "cannot open #{filename}: #{err.to_s}"
      end
    end

    if @compress
      return Zlib::GzipWriter.new(out_fp,Zlib::BEST_COMPRESSION,Zlib::DEFAULT_STRATEGY)
    else
      return out_fp
    end

  end

  # close the fastq output files
  def close_fastq_output_files
    if @pass_filename.nil? && @reject_filename.nil? && ! @out_filename.nil?
      STDERR.puts "Closing #{@out_filename}_TEMP for FASTQ output." if @verbose
      @pass.close
      # Move the temp file into place.
      STDERR.puts "Moving #{@out_filename}_TEMP to #{@out_filename}." if @verbose
      File.rename(make_temp_filename(@out_filename), @out_filename)
    else
      if not (@reject.nil? || @reject == STDOUT || @reject == @pass)
        STDERR.puts "Closing #{@reject_filename}_TEMP for reject FASTQ output." if @verbose
        @reject.close
        # Move the temp file into place.
        STDERR.puts "Moving #{@reject_filename}_TEMP to #{@reject_filename}" if @verbose
        File.rename(make_temp_filename(@reject_filename), @reject_filename)
      end

      if not (@pass.nil? || @pass == STDOUT)
        STDERR.puts "Closing #{@pass_filename}_TEMP for reject FASTQ output." if @verbose
        @pass.close
        # Move the temp file in place.
        STDERR.puts "Moving #{@pass_filename}_TEMP to #{@pass_filename}" if @verbose
        File.rename(make_temp_filename(@pass_filename), @pass_filename)
      end
    end
  end

  def close_fastq_sub_output_files
    if not (@pass_sub.nil? || @pass_sub == STDOUT)
      @pass_sub.close
      # Move the temp file in place.
      File.rename(make_temp_filename(@pass_sub_filename), @pass_sub_filename)
      File.chmod(0444, @pass_sub_filename)
    end

    if not (@reject_sub.nil? || @reject_sub == STDOUT)
      @reject_sub.close
      # Move the temp file into place.
      File.rename(make_temp_filename(@reject_sub_filename), @reject_sub_filename)
      File.chmod(0444, @reject_sub_filename)
    end
  end

  # return an object for reading data from a FASTQ file (either a File
  # object or a Zlib::GzipReader object)
  def open_fastq_input(filename)

    return nil if File.zero? filename
    if filename =~ /.gz$/
      return Zlib::GzipReader.open(filename)
    else
      return open(filename,'r')
    end

  end

  # read the FASTQ files and write to the pf/reject FASTQ files, plus collect stats
  def generate_fastq

    # Generate FASTQ file list, expanding patterns if found.
    fastq_input_file_list = []
    fastq_output_prefix_list = []
    fastq_output_group_list  = []
    ARGV.each do |fastq_input_file|
      if fastq_input_file =~ /[\+\?\*]/
        # File is regexp: use it to do our own "glob".
        # If the regexp has at least one group in it, save the group match
        #  in a corresponding list to use in making the output files.
        fastq_input_dir  = File.dirname(fastq_input_file)
        fastq_input_patt = File.basename(fastq_input_file)

        Dir.entries(fastq_input_dir).sort().each do |entry|
          if entry =~ /#{fastq_input_patt}()/o
            fastq_input_file_list << entry
            if not @out_prefix.nil?
              fastq_output_prefix_list << @out_prefix
            else
              fastq_output_prefix_list << entry[0..Regexp.last_match.begin(1)-1-1]  # Second -1 is for underline.
            end
            fastq_output_group_list << $1
          end
        end
      else
        if File.file? fastq_input_file
          fastq_input_file_list << fastq_input_file
          fastq_output_prefix_list << @out_prefix
        end
      end
    end

    die "no FASTQ files found" if fastq_input_file_list.length == 0

    STDERR.puts("Input files: #{fastq_input_file_list}") if @verbose

    fastq_list = fastq_input_file_list.zip(fastq_output_prefix_list, fastq_output_group_list)
    fastq_list.each do |fastq_input_file, fastq_output_prefix, fastq_output_group|

      # If we are splitting to subfiles, reset the output sub filenames to
      # the new destination for the new input file; also reset statistics.
      if @save_subfiles
        if fastq_output_group == ""
          fastq_output_group_mod = fastq_output_group
        else
          fastq_output_group_mod = "_#{fastq_output_group}"
        end
        @pass_sub_filename   = File.join(@pass_dir,   "#{fastq_output_prefix}_pf#{fastq_output_group_mod}.fastq")
        @pass_sub_filename += ".gz" if @compress
        @reject_sub_filename = File.join(@reject_dir, "#{fastq_output_prefix}_reject#{fastq_output_group_mod}.fastq")
        @reject_sub_filename += ".gz" if @compress

        @stats_sub_filename  = File.join(@stats_dir,  "#{fastq_output_prefix}_seq_stats#{fastq_output_group_mod}.txt")
        @pass_sub_read_cnt = @reject_sub_read_cnt = @total_sub_read_cnt = 0
      end

      if @save_subfiles
        open_fastq_sub_output_files
      end

      # split one FASTQ file into post-filter and reject FASTQ
      STDERR.puts "Processing #{fastq_input_file}..." if @verbose
      fastq_input_fp = open_fastq_input(fastq_input_file)
      if fastq_input_fp.nil?
        warn "#{fastq_input_file} is empty...skipping"
        next
      end
      begin
        while fastq_input_fp.readline
          header_line = $_
          if header_line !~ /^@/
            STDERR.puts "Missing header line (#{header_line})...exiting"
            exit(-1)
          end

          header_fields = header_line.split(/[ _]/)
          die "header parse error at #{fastq_input_file}:#{$INPUT_LINE_NUMBER} [#{header_fields.join("!")}]" if header_fields.size != 2

          sub_header_fields = header_fields[1].split(":",-1)
          die "sub header parse error at #{fastq_input_file}:#{$INPUT_LINE_NUMBER} [#{header_fields.join(":")}(#{sub_header_fields.join(":")})]" if sub_header_fields.size != 4

          @total_read_cnt += 1
          @total_sub_read_cnt += 1

          if sub_header_fields[1] == "N"
            out = @pass
            @pass_read_cnt += 1
            out_sub = @pass_sub
            @pass_sub_read_cnt += 1
          elsif sub_header_fields[1] == "Y"
            out = @reject
            @reject_read_cnt += 1
            out_sub = @reject_sub
            @reject_sub_read_cnt += 1
          else
            die "filter field value error at #{fastq_input_file}:#{$INPUT_LINE_NUMBER}...skipping read"
            out = nil
          end

          # Read the rest of the sequence.
          seq_line  = fastq_input_fp.readline
          plus_line = fastq_input_fp.readline
          if plus_line !~ /^\+/
            STDERR.puts "Malformed FASTQ +line (#{plus_line})"
          end
          qual_line = fastq_input_fp.readline

          # Output the sequence to whatever file was chosen above.
          if !out.nil?
            if not @remove_spaces
              out.print "#{header_line}"
              out_sub.print "#{header_line}" if not out_sub.nil?
            else
              out.puts header_fields.join("_")
              out_sub.puts header_fields.join("_") if not out_sub.nil?
            end
            out.print "#{seq_line}"
            out.print "#{plus_line}"
            out.print "#{qual_line}"
            if not out_sub.nil?
              out_sub.print "#{seq_line}"
              out_sub.print "#{plus_line}"
              out_sub.print "#{qual_line}"
            end
          end
        end # while

      rescue EOFError

      end

      fastq_input_fp.close()

      if @save_subfiles
        close_fastq_sub_output_files
        store_stats @stats_sub_filename, @pass_sub_read_cnt, @reject_sub_read_cnt, @total_sub_read_cnt
      end

    end # fastq_list.each
  end

  # store the statistics in the stats output file
  def store_stats(stats_filename, pass_read_cnt, reject_read_cnt, total_read_cnt)
    if pass_read_cnt + reject_read_cnt != total_read_cnt
      die "Pass plus reject != total read cnt (#{pass_read_cnt} + #{reject_read_cnt} != #{total_read_cnt})"
    end
    return if stats_filename.nil?
    File.open(stats_filename, "w") do |file|
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
    store_stats @stats_filename, @pass_read_cnt, @reject_read_cnt, @total_read_cnt

  end

  MergeSplitFastq.new.main

end
