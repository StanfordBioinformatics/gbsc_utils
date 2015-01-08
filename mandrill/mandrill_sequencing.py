###
#AUTHOR: Nathaniel Watson
###

import mandrill
from argparse import ArgumentParser
import random
import sys,os
import subprocess
import confparse

def processEmailAddrs(txt):
	"""
	Funtion : 
	Args    : txt - str. Comma-delimited string of email addresses."
	Returns : list
	"""
	addrs = [x.strip() for x in txt.strip().split(",")]
	for i in addrs:
		if not "@" in i :
			raise ValueError("Invalid email address '{}'".format(i))
	return addrs	


signaturesFile = os.path.join(os.path.dirname(__file__),"signatures.txt")
sigs = confparse.parseSignatures(signaturesFile)

parser = ArgumentParser()
parser.add_argument("--to",required=True,help="One or more comma-delimited recipient email addresses.")
parser.add_argument("--cc",default="scg-informatics-seq@lists.stanford.edu,gme1@stanford.edu",help="one ore more comma-delimited CC addresses.")
parser.add_argument("--subject",help="The subject of the email message.")
parser.add_argument("--add",help="Additional text to add to the top of the message.")
parser.add_argument("--run-name",required=True,help="The name of the sequencing run.")
#parser.add_argument("--sample",required=True,help="The name of the sequenced sample.")
parser.add_argument("--lanes",required=True,nargs="+",help="The lane number(s) to send sequencing results for.")
#parser.add_argument("--name",required=True,help="The first name of the primary recipient to whom the email message will be addressed.")
parser.add_argument("-v","--verbose",action="store_true",help="Make verbose")
parser.add_argument("--signature",required=True,help="A signature key identifying the signature to add to the email.")
args = parser.parse_args()

verbose = args.verbose
sigKey = args.signature
signature = sigs[sigKey].replace("\n","<br>")
htmlFile = os.path.join("/tmp",sys.argv[0].split(".py")[0] + "_" + str(random.random()))
#name = args.name.strip().split()[0]
run = args.run_name.strip()
#sample = args.sample.strip()
subject = args.subject
if subject:
	subject = subject.strip()
lanes = args.lanes
ccs = args.cc
recipients = args.to
recipients = processEmailAddrs(recipients)
if ccs:
	ccs = processEmailAddrs(ccs)
if not subject:
	subject = "Sequencing Results for {run} are ready".format(run=run)
#htmlBody = "<!DOCTYPE html><html><body>"
#htmlBody += "Hello {name},<br><br>Your sequencing and analysis results for sample {sample} from sequencing run {run}".format(name=name,sample=sample,run=run)
#if lane:
#	htmlBody += ", lane {lane},".format(lane=lane)
#htmlBody += " are ready.<br>"


#htmlBody += """Please log into <a href="https://platform.dnanexus.com/login">DNAnexus</a> to accept the pending data transfer within 30 days of this notice.
#Upon 30 days, the data will be sent to archival storage.<br><br>
#The FASTQ files are in <a href="http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2847217/">Sanger format.</a><br><br>

#Have you any questions, please contact me.<br><br>

#Sincerely,<br><br>

#Nathaniel Watson<br>
#Bioinformatics Data Analyst<br>
#Department of Genetics<br>
#Sequencing Center for Personalized Medicine<br>
#540.421.8820<br>
#</body></html>
#"""
htmlCmd = "python composeResultsEmail.py -o {htmlFile} {run}:{lanes} nw".format(htmlFile=htmlFile,run=run,lanes="".join(lanes))
if verbose:
	print(htmlCmd)
subprocess.check_call(htmlCmd,shell=True)
with open(htmlFile,'r') as h:
	htmlBody = [x.strip("\n") for x in h]
	htmlBody = "".join(htmlBody)

htmlBody += "<br><br>{signature}".format(signature=signature)

if verbose:
	print(htmlBody)
mandrill_client = mandrill.Mandrill('GLaCfxVPZNuataEW1fx6RQ')
message = {}
message["from_email"] = "nathankw@stanford.edu"
message["from_name"] = "Nathaniel Watson"
message["track_opens"] = False
message["track_clicks"] = False
message["tags"] = ["scgpm","sequencing results"]
message["to"] = []

for recipient in recipients:
	message["to"].append({"email": recipient,"type":"to"})

if ccs:
	for cc in ccs:
		message["to"].append({"email": cc,"type":"cc"})

message["subject"] = subject
message["html"] = htmlBody
result = mandrill_client.messages.send(message=message, async=False) #
	#note regarding async parameter:
	# Defaults to false for messages with no more than 10 recipients; messages with more than 10 recipients are always sent asynchronously, regardless of the value of async.
