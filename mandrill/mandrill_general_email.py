#!/usr/bin/env python
#AUTHOR: Nathaniel Watson
###

import mandrill
from argparse import ArgumentParser
import random
import sys,os
import subprocess
import json

def processEmailAddrs(addresses):
	"""
	Funtion : Given a string of putative email addresses that are comma delimited, strips off whitespace from each address and ensures that each address contains an "@"
            sign, otherwise a ValueError is raised. Creates a set of the addresses so that no address is repeated. 
	Args    : txt - str. Comma-delimited string of email addresses."
	Returns : list
	"""
	for i in addresses:
		if not i:
			continue
		if "@" not in i :
			raise ValueError("Invalid email address '{}'".format(i))
	return addresses


sendersFile = os.path.join(os.path.dirname(__file__),"senders.json")
allSenders = json.load(open(sendersFile,'r'))

parser = ArgumentParser()
parser.add_argument("--body",help="A file that has the contents of the HTML body.")
parser.add_argument("--to",nargs="+",required=True,help="One or more space-delimited recipient email addresses.")
parser.add_argument("--cc",default=[],nargs="+",help="one ore more space-delimited CC addresses.")
parser.add_argument("--subject",required=True,help="The subject of the email message.")
parser.add_argument("--add",help="Additional text to add to the top of the message. Any before and after whitespace will be stripped. Any newlines present will then be converted to HTML line breaks.  Two newline characters will be added to the end before the standard body of the email is appended.")
parser.add_argument("-v","--verbose",action="store_true",help="Make verbose")
parser.add_argument("--sender",required=True,help="A signature key identifying the signature to add to the email (use your SUNet ID as your signature key; update the file ./signatures.txt for adding new signatures).")
parser.add_argument('--dry-run',action="store_true",help="Presence of this option indicates not to send the email, but do everything else. This option implies the -v option.")
args = parser.parse_args()
dryRun = args.dry_run
verbose = args.verbose
addText = args.add
htmlBodyFile = args.body

if dryRun:
	verbose = True

senderKey = args.sender
sender = allSenders[senderKey]
subject = args.subject
if subject:
	subject = subject.strip()
ccs = args.cc
if type(ccs) == str: #happens when default is used
	ccs = [ccs]
ccs = [x for x in ccs if x] #ignore empty elements in the list. For example, if the user specifies --cc "", then that will create a list with an empty string.
ccs = set(ccs)
recipients = args.to
recipients = processEmailAddrs(recipients)
ccs = processEmailAddrs(ccs)

body = ""
if htmlBodyFile:
	fh = open(htmlBodyFile,'r') 
	body = [x.replace("\n","<br />") for x in fh]
	fh.close()
	body = "".join(body)
if addText:
	body = addText.strip() + "<br /><br />" + body
	body = body.replace("\n","<br />")

signature = sender['signature'].replace("\n","<br />")
body += "<br><br>{signature}".format(signature=signature)

if verbose:
	print(body)
mandrill_client = mandrill.Mandrill('GLaCfxVPZNuataEW1fx6RQ')
message = {}
message["from_email"] = sender['email']
message["from_name"] = sender['name']
message["track_opens"] = False
message["track_clicks"] = False
#message["tags"] = ["scgpm","sequencing results"]
message["to"] = []

for recipient in recipients:
	message["to"].append({"email": recipient,"type":"to"})

if ccs:
	for cc in ccs:
		message["to"].append({"email": cc,"type":"cc"})

message["subject"] = subject
message["html"] = body
if not dryRun:
	result = mandrill_client.messages.send(message=message, async=False) #
	#note regarding async parameter:
	# Defaults to false for messages with no more than 10 recipients; messages with more than 10 recipients are always sent asynchronously, regardless of the value of async.
