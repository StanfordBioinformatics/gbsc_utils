#!/usr/bin/env ruby

class PublishRuns

  @@Program = "publish_runs.rb"
  @@Archive = "/srv/gs1/projects/scg/Archive/IlluminaRuns"

  def parse_args
    if ARGV.size < 1
      puts "Usage: #{@@Program} run_dir [run_dir...]"
      exit 1
    end

  end

  def parse_run_dir_w_lanes(run_dir_w_lanes)
    # Parse the run dir arguments to get the lane lists
    (run_dir, lanes) = run_dir_w_lanes.split(":",2)
    
    # Make a list of lane number from the lane numbers.
    if (not lanes.nil?)
      lane_list = lanes.split(//).map{|lane| lane.to_i}
    else
      lane_list = []
    end
      
    return [run_dir, lane_list]
  end
 
  def parse_date(run_dir)
    # Date is in first 6 chars of run_dir
    if (run_dir =~ /^(\d{2})(\d{2})(\d{2})/)
      year  = "20#{$1}"
      # Need to convert month to month name
      date = Time.local(year, $2)
      month = date.strftime("%b").downcase
      
      return [year, month]
    else
      return nil
    end
  end
  
  def publish(run_dir, lane_list, dest)
    
    (year, month) = parse_date(run_dir)

    Dir.chdir @@Archive + "/#{year}/#{month}"
    
    cmd = "rsync -rlptR --chmod=g+rw --progress"
        
    if (not lane_list.empty?)
      exclude_lane_list = (1..8).to_a
      
      # Include the lanes from lane_list by removing them from exclude list.
      lane_list.each do |lane|
        exclude_lane_list.delete lane
      end
      
      exclude_lane_list.each do |exlane|
        cmd += " --exclude *_L#{exlane}*"
      end
    end
    
    # Copy the run directory.
    cmd += " #{run_dir}"
    
    # Copy it to this destination.
    cmd += " #{dest}/#{year}/#{month}" 

    puts "Running: #{cmd}"
    system(cmd) || die("error: rsync failed: #{$?}")
  end

  # print an error message and exit
  def die(msg)
    STDERR.puts "#{@@Program}: #{msg}"
    exit 1
  end

  def main
    parse_args
    
    ARGV.each do |run_dir_w_lanes|
      
      (run_dir, lane_list) = parse_run_dir_w_lanes run_dir_w_lanes
      
      publish run_dir, lane_list, "cygnus:/opt/spg/Archive/SolexaRuns"

    end
  end
end

PublishRuns.new.main
