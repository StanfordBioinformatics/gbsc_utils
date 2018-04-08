#!/usr/bin/env python

#........................................
#
# Enter your SUNet ID in the quotes below
# You will also need to run this command:
# chmod +x igvhelper.py
#
#########################################

STANFORD_ID=""

#########################################


#
# This script is to help launch and kill
# instances of the TurboVNC server installed
# on a remote server.
#
# It also installs a script for launching
# IGV on your remote desktop.
#
# Setup:
#   igvtools.py --installigv
#
# Launching the desktop:
#   igvtools.py --start
#
# Clean up after yourself each time you finish!
#   igvtools.py --stop
#

if not STANFORD_ID:
    raise Exception('Edit this file to enter your SUNet ID')


# Use fully qualified host name
HOST='vnc.scg.stanford.edu'

#SERVER_CMD='/opt/TurboVNC/bin/vncserver'
#VIEWER_CMD='/opt/TurboVNC/bin/vncviewer'
SERVER_CMD='vncserver'
VIEWER_CMD='vncviewer'

from argparse import ArgumentParser
import re
import subprocess
import sys

if sys.version_info.major == 3:
  raise Exception("This program requires a Python 2x version. 3x is not supported.")

parser=ArgumentParser(
    description='Start or stop TurboVNCserver on a remote machine cluster')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--start', action='store_true')
group.add_argument('--stop', action='store_true')
group.add_argument('--installigvlink', action = 'store_true')
args = parser.parse_args()
START = args.start
STOP = args.stop
INSTALL_IGV=args.installigvlink

def getrunningdisplays(text):
    pattern = ':([0-9]+)'
    match = re.findall(pattern, text)
    xdisplays = []
    for val in match:
        xdisplays.append(int(val))
    return xdisplays

def stop():
    # sample stdout text:
    #
    # X DISPLAY #PROCESS ID
    # :5 30999
    # :6 590
    # :7 1040

    cmd = 'ssh %s@%s %s -list' % (
        STANFORD_ID,
        HOST,
        SERVER_CMD,
    )
    p = subprocess.Popen(
        cmd, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()

    cmd = ''
    displays = getrunningdisplays(stdout)
    for display in displays:
        cmd += 'ssh %s@%s %s -kill :%s; ' % (
            STANFORD_ID,
            HOST,
            SERVER_CMD,
            display
        )
    if cmd:
        print 'One or more displays were running: (:%s) '\
        'Cleaning up now.' \
        % ' :'.join([str(i) for i in displays])
        subprocess.call(cmd, shell=True)

def getstartedxdisplay(text):
    # sample stderr text:
    #
    # Desktop 'TurboVNC: carmack.stanford.edu:1 (nhammond)' \
        # started on display carmack.stanford.edu:1
    # Starting applications specified in /home/nhammond/.vnc/xstartup.turbovnc
    # Log file is /home/nhammond/.vnc/carmack.stanford.edu:1.log

    pattern = r'started on display %s:([0-9]+)' % HOST
    match = re.search(pattern, text)
    if not match:
        raise Exception(
            'Could not parse this text to identify the X Display number: %s' 
            % text)
    return int(match.groups()[0])

def start():
    # First clean up any previous session
    stop()

    # Then start the server
    cmd = 'ssh %s@%s %s' % (
        STANFORD_ID,
        HOST,
        SERVER_CMD,
    )
    p = subprocess.Popen(
        cmd, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    xdisplay = getstartedxdisplay(stderr)

    # And finally launch the viewer locally
    port = 5900 + xdisplay
    cmd = '%s %s:%s' % (
        VIEWER_CMD,
        HOST,
        port)
    print("Running command {cmd}".format(cmd=cmd))
    subprocess.call(cmd, shell=True)

def installigvlink():
    # Write this script on the remote desktop
    # and chmod it to be executable.
    content = """\
#-Xmx4000m indicates 4000 mb of memory, adjust number up or down as needed
#Add the flag -Ddevelopment = true to use features still in development
exec /srv/gsfs0/software/java/jre1.8.0_66/bin/java -Xmx4000m -Dapple.laf.useScreenMenuBar=true -Djava.net.preferIPv4Stack=true -jar /srv/gsfs0/software/igv/IGV_2.3.82/igv.jar \\\"\$@\\\"
"""
    cmd = 'echo "%s" | ssh %s@%s "cat > ~/Desktop/igv.sh; '\
          'chmod +x ~/Desktop/igv.sh"' % (
              content,
              STANFORD_ID,
              HOST,
          )
    subprocess.call(cmd, shell=True)

if INSTALL_IGV:
    installigvlink()

if START:
    start()

if STOP:
    stop()
