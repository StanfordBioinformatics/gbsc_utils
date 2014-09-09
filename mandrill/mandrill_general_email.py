###
#AUTHOR: Nathaniel Watson
###


import mandrill
import confparse
import os
from argparse import ArgumentParser

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


ATTACHMENT_LIMIT = 25 * 1024**2 #25MB
#As of 9/8/2014, Mandrill sets a limit of 25MB for the entire message content sent

signaturesFile = os.path.join(os.path.dirname(__file__),"signatures.txt")
sigs = confparse.parseSignatures(signaturesFile)


parser = ArgumentParser()
parser.add_argument("--to",required=True,help="One or more comma-delimited recipient email addresses.")
parser.add_argument("--cc",help="one ore more comma-delimited CC addresses.")
parser.add_argument("--subject",required=True,help="The subject of the email message.")
parser.add_argument("--signature",required=True,help="A signature key identifying the signature to add to the email.")
parser.add_argument("--add",help="Additional (non-HTML) text to add to the top of the message.")
parser.add_argument("-i","--infile",help="Input file whose contents are to be added to the email message as plain text.")
parser.add_argument("--attachments",help="Path to file to attach",nargs = "*")
args = parser.parse_args()

attachments = args.attachments
text = ""
if args.add:
	text = args.add
infile = args.infile
sigKey = args.signature
signature = sigs[sigKey]
subject = args.subject.strip()
subject = subject.strip()
ccs = args.cc
recipients = args.to
recipients = processEmailAddrs(recipients)
if ccs:
	ccs = processEmailAddrs(ccs)
#htmlBody = "<!DOCTYPE html><html><body>"
#if add:
#	htmlBody += add
#htmlBody += """

if infile:
	fh = open(infile,'r')
	text += fh.read()
text += "\n\n"
text += signature

mandrill_client = mandrill.Mandrill('GLaCfxVPZNuataEW1fx6RQ')
message = {}
if attachments:
	elements = []
	type = "text/plain"
	for f in attachments:
		if not os.path.exists(f):
			raise OSError("Attachment file '{f}' does not exist!".format(f=f))
		#check each attachment size. Won't allow any attachment to be >= ATTACHMENT_LIMIT. Note that its still possible that the sumnation of attachment sizes + message content will 
		# still surpass Mandrill's message size limit of 25MB.
		fileSize = os.path.getsize(f) #size in bytes
		if fileSize >= ATTACHMENT_LIMIT:
			raise OSError("Attachment file '{f}' is too large. The current maximim attachment size per file is {size}".format(f=f,size=ATTACHMENT_SIZE))
		content = open(f,'r').read()
		name = os.path.basename(f)
		elements.append({"type":type,"name":name,"content":content})
	message["attachments"] = elements

message["text"] = text
message["from_email"] = "nathankw@stanford.edu"
message["from_name"] = "Nathaniel Watson"
message["track_opens"] = False
message["track_clicks"] = False
message["tags"] = ["snap","scoring results","chip"]
message["to"] = []

for recipient in recipients:
	message["to"].append({"email": recipient,"type":"to"})

if ccs:
	for cc in ccs:
		message["to"].append({"email": cc,"type":"cc"})

message["subject"] = subject
#message["html"] = htmlBody
result = mandrill_client.messages.send(message=message, async=False) #
print(result)
	#note regarding async parameter:
	# Defaults to false for messages with no more than 10 recipients; messages with more than 10 recipients are always sent asynchronously, regardless of the value of async.
