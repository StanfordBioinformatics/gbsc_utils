import subprocess
import os
import datetime

def createSubprocess(cmd,checkRetcode=True):
	"""
	Function : Creates a subprocess via a call to subprocess.Popen with the argument 'shell=True', and pipes stdout and stderr.
             For any non-zero return code, an Exception is raised along with the command, stdout, stderr, and the returncode.
	Args     : cmd   - str. The command line for the subprocess wrapped in the subprocess.Popen instance. If given, will be printed to stdout when there is an error in the subprocess.
						 checkRetcode - bool.
	Returns  : A two-item tuple containing stdout and stderr, respectively.
	"""
	popen = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	if checkRetcode:
		stdout,stderr = popen.communicate()
		retcode = popen.returncode
		if retcode:
			#below, I'd like to raise a subprocess.SubprocessError, but that doens't exist until Python 3.3.
			raise Exception("subprocess command '{cmd}' failed with returncode '{returncode}'.\nstdout is: {stdout}.\nstderr is: {stderr}.".format(cmd=cmd,returncode=retcode,stdout=stdout,stderr=stderr))
		return stdout,stderr
	else:
		return popen


def getFileAgeMinutes(infile):
	""" 
	Function : Calculates the age of a file in hours. Partial hours are always rounded down a whole number.
					   Raises an IOError of the input file doens't exist.
	"""
	if not os.path.exists(infile):
		raise IOError("Can't check age of non-existant file '{infile}'".format(infile=infile))
	mtime = datetime.datetime.fromtimestamp(os.path.getmtime(infile))
	now = datetime.datetime.now()
	diff = now - mtime
	seconds = diff.total_seconds()
	minutes = seconds/60
	return minutes
