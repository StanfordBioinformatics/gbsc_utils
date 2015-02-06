##############################################################################
#
# composeResultsEmail.py - .
#
# ARGS:
#   1st: Run name
#   2nd: Recipient list, comma-separated.
#  REST: Extra output formats (sgr, export)
#
# SWITCHES:
#  --svcctr: Add extra CC for service center email.
#  --scg1:   Output paths instead of URLs.
#  --fastq_only: Only report fastq results (no eland)
#
# OUTPUT:
#   None.
#   SIDE EFFECT: an email is composed in Apple Mail.
#
# ASSUMPTIONS:
#
# AUTHOR:
#   Keith Bettinger
#
###############################################################################

#####
#
# IMPORTS
#
#####
from optparse import OptionParser
import datetime
import os
import os.path
import re
import subprocess
import sys
import tempfile

#####
#
# CONSTANTS
#
#####
RUN_HOST_DEFAULT = "carmack.stanford.edu"

URL_PATTERN = re.compile(r"(\s*)(https?://[\w\./-]+)")

WEB_HOST = "scg-data.stanford.edu"
WEB_ROOT = "PublishedResults"

PUBLISHED_ROOT = "/srv/gsfs0/projects/seq_center/Illumina/PublishedResults"

CONFIG = {}

#####
#
# FUNCTIONS
#
#####
def convert_http_to_link(line):
    url_match = URL_PATTERN.match(line)
    if url_match is not None:
        return "%s<A HREF='%s'>%s</A>\n" % (url_match.group(1), url_match.group(2), url_match.group(2))
    else:
        return line + "\n"

def set_param(param, value, no_overwrite=False):
    component = None
    subconfig = CONFIG
    int_re = re.compile("^\d+$")
    for next_component in param.split(':'):
        if component is not None:
            # Find or create a level of hierarchy
            if subconfig.get(component) is None: subconfig[component] = dict()
            subconfig = subconfig[component]
            if not isinstance(subconfig, dict):
                raise "invalid components after %s in param %s" % (component, param)

        if int_re.match(next_component):
            component = int(next_component)
        else:
            component = next_component

    oldvalue = subconfig.get(component)
    if isinstance(oldvalue, dict):
        raise "incomplete parameter path: %s" % param

    if oldvalue is None or not no_overwrite:
        subconfig[component] = value

def read_config_file(run_name,publishedRunName=""):
    pub_dir = os.path.join(PUBLISHED_ROOT,str(runyear),runmon)
    if publishedRunName:
      pub_dir  = os.path.join(pub_dir,publishedRunName)
    else:
      pub_dir = os.path.join(pub_dir,run_name)

    config_path = os.path.join(pub_dir, "config.txt")
    cmd="ssh -f {RUN_HOST_DEFAULT} cat {config_path}".format(RUN_HOST_DEFAULT=RUN_HOST_DEFAULT,config_path=config_path)
    if verbose:
        print(cmd)
    proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)

    for line in proc.stdout:
        line = line.strip()
        if verbose:
            print(line)
        try:
            param, value = line.split(" ",1)
        except ValueError:
            evalue = ""
        set_param(param, value)


# ASSUMPTION: CONFIG has values from the run.
def make_result_table(incl_links=False):

    table_html = """
<table border="1" cellpadding="5">
 <tr>
  <td>Sample name</td>
  <td>Submitter</td>
  <td>Flowcell</td>
  <td>Lane</td>
  <td>Results</td>
 </tr>
"""

    for lane in lane_list:
        lane_config = CONFIG['lane'][lane]

        if opts.pub_dir is not None:
            publishedRunName = opts.pub_dir
        else:
            publishedRunName = run_name

        lane_result_url = "%s/%s/%s_L%d_results.html" % (lane_result_root, publishedRunName, run_name, lane)
        sample_link     = "<A HREF='%s'>%s</A>" % (lane_result_url, lane_config['sample_name'])
        if incl_links:
            download_link   = "<A HREF='%s'>%s</A>" % (lane_result_url,lane_result_url)
        else:
            download_link   = "<A HREF='%s'>Web Page</A>" % (lane_result_url)
        
        table_html += " <tr>"
        table_html += "  <td>%s</td>" % sample_link
        table_html += "  <td>%s</td>" % lane_config['submitter']
        table_html += "  <td>%s</td>" % flowcell
        table_html += "  <td>%d</td>" % lane
        table_html += "  <td>%s</td>" % download_link
        table_html += " </tr>"

    table_html += "</table>"
    return table_html
    
    
# INCOMPLETE
def query_lims(run):
    lims_host     = os.environ.get('LIMS_HOST')
    lims_rake_cmd = os.environ.get('LIMS_RAKE_CMD')
    lims_rakefile = os.environ.get('LIMS_RAKEFILE')

    query_cmd = "ssh %s %s -f %s RAILS_ENV=production analysis:config" % (lims_host, lims_rake_cmd, lims_rakefile)


    
#####
#
# SCRIPT BODY
#
#####

usage = "%prog [options] run_name recipients [extras]"
parser = OptionParser(usage=usage)

parser.add_option("-s", "--svcctr", dest="svcctr", action="store_true",
                  default=False,
                  help='make this as a service center run [default = False]')
parser.add_option("-m", "--scg1", dest="scg1", action="store_true",
                  default=False,
                  help='use scg1 for reporting instead of cygnus [default = False]')
parser.add_option("-f", "--fastq_only", dest="fastq_only", action="store_true",
                  default=False,
                  help='only report fastq results (no eland) [default = False]')
parser.add_option("-a", "--pub_dir", dest="pub_dir", type="string",
                  default=None,
                  help='Use this as the published directory name. [default = <run_name>].')
parser.add_option('-o','--outfile',help="Output file.")
parser.add_option("-l", "--full_links", action="store_true",
                  default=False,
                  help='use full links in results table [default = False]')
parser.add_option('-v','--verbose',action="store_true",help="Turn on verbose output")

(opts, args) = parser.parse_args()
verbose = opts.verbose
publishedRunName = opts.pub_dir
outfile=opts.outfile
if len(args) < 2:
    print >> sys.stderr, os.path.basename(__file__), ": Missing arguments."
    sys.exit(1)

run_name_w_lanes = args[0]
recipients = args[1]
extras = args[2:]

if opts.svcctr:
    print "THIS RUN IS FOR THE SERVICE CENTER."

#
# Tweak arguments
#

# Split off lane numbers from run name, if necessary.
lanes = None
lane_list = range(1,9)
colon_idx = run_name_w_lanes.find(':')
if colon_idx != -1:
    run_name = run_name_w_lanes[0:colon_idx]
    lanes    = run_name_w_lanes[colon_idx+1:]

    # If lanes start with '-', remove the numbers that follow from a lane list 12345678.
    if lanes[0] == '-':
        for l in lanes[1:]:
            lane_list.remove(int(l))
        lanes = "".join(map(lambda d: str(d), lane_list))
    else:
        lane_list = map(lambda s: int(s), list(lanes))
else:
    run_name = run_name_w_lanes

# Find the flowcell name within the run name.
run_name_split = run_name.split('_')
if len(run_name_split) < 2:
    print >> sys.stderr, "Could not split %s into run name components." % run_name
    sys.exit(1)
    
rundatestr = run_name_split[0]
runmach = run_name_split[1]
if len(run_name_split) == 3:
    flowcell = run_name_split[2]
else:
    runidx  = run_name_split[2]
    flowcell = run_name_split[3]

rundate = datetime.date(int(rundatestr[0:2])+2000,int(rundatestr[2:4]),int(rundatestr[4:6]))
runyear = int(rundate.strftime("%Y"))
runmon  = rundate.strftime("%b").lower()

if flowcell.startswith("FC"):
    flowcell = flowcell[2:]
else:
    hiseq_re = re.search("^[AB](.+)ABXX$",flowcell)
    if hiseq_re:
        flowcell = hiseq_re.group(1)

# Make list of recipients.
recipient_list = recipients.split(",")

#
# Create HTML body for email.
#
# Read the config.txt file from the Archive dir.
read_config_file(run_name,publishedRunName=publishedRunName)

# Create links for each lane to report.
lane_result_root = "http://%s/%s/%d/%s" % (WEB_HOST, WEB_ROOT, runyear, runmon)

# Make HTML table for result links.
result_table = make_result_table(opts.full_links)

submitter_name = CONFIG['lane'][lane_list[0]]['submitter'] #assumes same submitter for all lanes
names = submitter_name.split()
first_name = " ".join(names[:-1])

report_text_head = """
Hello %s,

<p>The results from sequencing your samples can be found at the links below:</p>

""" % first_name

report_text_body = "<ul style='list-style: none;'>\n"
report_text_body += result_table
report_text_body += "</ul>\n"

report_text_foot = """
<p>These pages contain:</p>
<ul>
  <li>Links for you to download your sequencing results (you are encouraged to do so as soon as possible).</li>
  <li>Statistics and graphs from sequencing and alignment.</li>
</ul>
<p></p>
<p>NOTES ON THE RESULTS:</p>
<ul>
  <li>The FASTQ files containing sequencing results are in Illumina 1.8+ format, as opposed to the Illumina 1.5+ (proprietary) format. &nbsp;This difference means two things:</li>
  <ul>
    <li>They use Sanger quality values (Q + 33), not Illumina quality values (Q + 64).</li>
    <li>Filtering information is stored in the sequence name.</li>
  </ul>
  <li>BWA was used to align the reads to reference.</li>
  <li>Alignment results are returned in BAM, BED, and SGR formats.</li>
</ul>
</ul>
<p></p>
<p>Let me know if you have any questions about the results.</p>
<p></p>
<p>Regards,</p>
"""
report_text = report_text_head + report_text_body + report_text_foot
fout = open(outfile,'w')
fout.write(report_text)
fout.close()
