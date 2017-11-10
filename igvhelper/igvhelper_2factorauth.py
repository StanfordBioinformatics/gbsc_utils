#!/usr/bin/env python

# This script is a replacement version of igvhelper
# to be used with the 2-factor auth system on scg
# if we are ever forced to stop using ssh keys.
# Setup for this version may be slightly easier
# (no keys) but since users are already stable on
# the other version there is no good reason to
# shake things up. Saving this for when/if needed
# in the future.
# Differences with the old version:
# a. New version uses vnc over ssh tunnel
# b. New version uses a "module load vnc; vnc.sh",
#    a script that John Hanks created for launching a
#    VNC server.
# c. No cleanup of vncserver process.
#    In conversations with John he didn't care if we
#    leave things running, and the vnc.sh script
#    prevents creating duplicate server processes.
# d. No ssh keys needed -- just 2 password and 2-factor
#    auth prompts during "setup", none during "start"
# e. No igv.sh link created on desktop. Users can open
#    a terminal and "module load igv; igv.sh". Instructions
#    for this are printed when running "--start"

#........................................
#
# Enter your SUNet ID in the quotes below
# You will also need to run this command:
# chmod +x igvhelper.py
#
#########################################

STANFORD_ID="nhammond"

#########################################


#
# This script is to help start a remote VNCserver
# and create an ssh tunnel to that server.
#
# Launching the vncserver and the ssh tunnel:
#  igvhelper.py --setup
# 
# Launching the desktop:
#   igvhelper.py --start
#

if not STANFORD_ID:
    raise Exception('Edit this file to enter your SUNet ID')

HOST='vnc.scg.stanford.edu'

from argparse import ArgumentParser
import re
import subprocess
import sys

if sys.version_info.major == 3:
  raise Exception("This program requires a Python 2x version. 3x is not supported.")

parser=ArgumentParser(
    description='Start or stop VNC server on a remote server')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--setup', action='store_true')
group.add_argument('--start', action='store_true')
args = parser.parse_args()

SETUP = args.setup
START = args.start

def setup():
    vnc_cmd = "ssh %s@%s -t 'bash -l -c \"module load utils; vnc.sh\"'" % (
        STANFORD_ID,
        HOST,
    )
    p = subprocess.Popen(
        vnc_cmd, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    m = re.search('(ssh.*stanford.edu)', stdout)
    ssh_cmd = m.group()
    subprocess.call(ssh_cmd, shell=True)

def start():
    print 'When the desktop starts'
    print '1) open Applications>System Tools>Terminal'
    print '2) run "module load igv"'
    print '3) run "igv.sh"'
    cmd = 'open vnc://localhost:28589'
    subprocess.Popen(cmd, shell=True)

if SETUP:
    setup()

if START:
    start()
