from argparse import ArgumentParser
import os
import json
import runPaths
import glob

conf = os.path.join(os.path.dirname(__file__),"conf.json")
conf = json.load(open(conf,'r'))

urlBase = conf["urlBase"]
pubBaseDir = conf["pubDir"]


parser = ArgumentParser(description="")
parser.add_argument("-r","--run-name",required=True,help="The name of the sequencing run.")
parser.add_argument("-l","--lane",required=True,help="The sequecing lane as named in the run directory.")
args = parser.parse_args()

run = args.run_name
lane = args.lane

runPubPath = runPaths.getPubPath(run)
year,month = runPaths.getRunYearMonth(run)
lanePubPath = os.path.join(runPubPath,lane)
if not os.path.isdir(lanePubPath):
	raise OSError("Can't locate the run and lane provided! Expected {} but that path does not exist.".format(lanePubPath))

title = "Sequencing FASTQ Results for Run {run} {lane}".format(run=run,lane=lane)
print('<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n<title>{title}</title>\n</head>'.format(title=title))
print('<body>\n')

for i in glob.glob(os.path.join(lanePubPath,"*_pf.fastq")) + glob.glob(os.path.join(lanePubPath,"*_pf.fastq.gz")):
	fileName = os.path.basename(i)
	url = os.path.join(urlBase,year,month,run,lane,fileName)
	print('<a href="{url}">{fileName}</a></br>'.format(url=url,fileName=fileName))

print('</body>\n</html>')

