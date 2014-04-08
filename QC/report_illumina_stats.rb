#!/usr/bin/env ruby

#
# report_illumina_stats.rb: create a report for a subset of lanes
# from and illumina run
#
# Phil Lacroute
#

class ReportIlluminaStats

  @@Program = "report_illumina_stats.rb"

  @@RunStats = [
                { :name => "Run" },
                { :name => "Flow Cell" },
                { :name => "Platform" }
               ]

  @@LaneStats = [
                 { :name => "Lane" },
                 { :name => "Sample" },
                 { :name => "Submitter" },
                 { :name => "Genome" },
                 { :name => "Barcode" },
                 { :name => "Read Number" },
                 { :name => "Total Reads", :numeric => true },
                 { :name => "Post-Filter Reads", :numeric => true },
                 { :name => "Post-Filter Unique",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Unique 0mm",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Unique 1mm",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Unique 2mm",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Non-Unique",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Non-Unique 0mm",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Non-Unique 1mm",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Non-Unique 2mm",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Repetitive",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Repetitive 0mm",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Repetitive 1mm",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Repetitive 2mm",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter No-Match",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Too-Many-Ns",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Repeat-Masked",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Post-Filter Contam",
                   :numeric => true, :denom => "Post-Filter Reads" },
                 { :name => "Failed Reads", :numeric => true },
                 { :name => "Failed Unique",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Unique 0mm",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Unique 1mm",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Unique 2mm",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Non-Unique",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Non-Unique 0mm",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Non-Unique 1mm",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Non-Unique 2mm",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Repetitive",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Repetitive 0mm",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Repetitive 1mm",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Repetitive 2mm",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed No-Match",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Too-Many-Ns",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Repeat-Masked",
                   :numeric => true, :denom => "Failed Reads" },
                 { :name => "Failed Contam",
                   :numeric => true, :denom => "Failed Reads" }
                ]

  # parse command-line options
  def parse_args
    die "Usage: #{@@Program} stats1.txt ...\n" if ARGV.empty?
  end

  def report_stats
    # load statistics from input files
    stats = Array.new
    ARGV.each do |filename|
      filestats = parse_stats_file(filename)
      if filestats["Failed Reads"].nil?
        filestats["Failed Reads"] =
          filestats["Total Reads"].to_i - filestats["Post-Filter Reads"].to_i
      end
      compute_stat(filestats, "Post-Filter Unique",
                   [ "Post-Filter Unique 0mm", 
                     "Post-Filter Unique 1mm",
                     "Post-Filter Unique 2mm" ])
      compute_stat(filestats, "Post-Filter Non-Unique",
                   [ "Post-Filter Non-Unique 0mm", 
                     "Post-Filter Non-Unique 1mm",
                     "Post-Filter Non-Unique 2mm" ])
      compute_stat(filestats, "Post-Filter Repetitive",
                   [ "Post-Filter Repetitive 0mm", 
                     "Post-Filter Repetitive 1mm",
                     "Post-Filter Repetitive 2mm" ])
      compute_stat(filestats, "Failed Unique",
                   [ "Failed Unique 0mm", 
                     "Failed Unique 1mm",
                     "Failed Unique 2mm" ])
      compute_stat(filestats, "Failed Non-Unique",
                   [ "Failed Non-Unique 0mm", 
                     "Failed Non-Unique 1mm",
                     "Failed Non-Unique 2mm" ])
      compute_stat(filestats, "Failed Repetitive",
                   [ "Failed Repetitive 0mm", 
                     "Failed Repetitive 1mm",
                     "Failed Repetitive 2mm" ])

      stats.push filestats
    end

    # output per-run info
    @@RunStats.each do |stat_params|
      value = stats[0][stat_params[:name]]
      stats.each do |filestats|
        die "inconsistent values for #{stat_params[:name]}" if
          filestats[stat_params[:name]] != value
      end
      puts "#{stat_params[:name]}: #{value}"
    end

    # output per-lane info
    @@LaneStats.each do |stat_params|
      printf("%-30s", stat_params[:name] + ":")
      stats.each do |filestats|
        value = filestats[stat_params[:name]]
        if !blank?(value)
          if stat_params[:numeric]
            printf("  %15s", commify(value.to_i))
            if stat_params[:denom].nil?
              denom = nil
            else
              denom = filestats[stat_params[:denom]]
            end
            if !blank?(denom) && denom.to_i != 0
              printf(" (%2u%%)", (value.to_i * 100 / denom.to_i).round)
            else
              printf("      ")
            end
          else
            printf(" %22s", value)
          end
        else
          printf("                    N/A")
        end
      end # stats.each
      print "\n"
    end # @@LaneStats.each
  end
      
  def parse_stats_file(filename)
    stats = Hash.new
    IO.foreach(filename) do |line|
      if line =~ /^([^:]+):\s+(.*)$/
        stats[$1] = $2
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

  def commify(number, delimiter = ',')
    number.to_s.reverse.gsub(%r{([0-9]{3}(?=([0-9])))}, "\\1#{delimiter}").reverse
  end

  # print an error message and exit
  def die(msg)
    STDERR.puts "#{@@Program}: #{msg}"
    exit 1
  end

  # test if a string is nil or empty
  def blank?(thing)
    thing.respond_to?(:empty?) ? thing.empty? : !thing
  end

  # main entry point
  def main
    parse_args
    report_stats
  end
end

ReportIlluminaStats.new.main
