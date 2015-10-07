import subprocess
import os
import datetime
import time

def createSubprocess(cmd,pipeStdout=False,checkRetcode=True):
	"""
	Function : Creates a subprocess via a call to subprocess.Popen with the argument 'shell=True', and pipes stdout and stderr. Stderr is always  piped, but stdout can be turned off.
             If the argument checkRetcode is True, which it is by defualt, then for any non-zero return code, an Exception is
						 raised that will print out the the command, stdout, stderr, and the returncode when not caught. Otherwise, the Popen instance will be return, in which case the caller must 
					   call the instance's communicate() method (and not it's wait() method!!) in order to get the return code to see if the command was a success. communicate() will return 
						 a tuple containing (stdout, stderr). But at that point, you can then check the return code with Popen instance's 'returncode' attribute.
	Args     : cmd   - str. The command line for the subprocess wrapped in the subprocess.Popen instance. If given, will be printed to stdout when there is an error in the subprocess.
						 pipeStdout - bool. True means to pipe stdout of the subprocess.
						 checkRetcode - bool. See documentation in the description above for specifics.
	Returns  : A two-item tuple containing stdout and stderr, respectively.
	"""
	stdout = None
	if pipeStdout:
		stdout = subprocess.PIPE
		stderr = subprocess.PIPE
	popen = subprocess.Popen(cmd,shell=True,stdout=stdout,stderr=subprocess.PIPE)
	if checkRetcode:
		stdout,stderr = popen.communicate()
		if not stdout: #will be None if not piped
			stdout = ""
		stdout = stdout.strip()
		stderr = stderr.strip()
		retcode = popen.returncode
		if retcode:
			#below, I'd like to raise a subprocess.SubprocessError, but that doens't exist until Python 3.3.
			raise Exception("subprocess command '{cmd}' failed with returncode '{returncode}'.\n\nstdout is: '{stdout}'.\n\nstderr is: '{stderr}'.".format(cmd=cmd,returncode=retcode,stdout=stdout,stderr=stderr))
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

def getCurTime():
	epochTime  = time.time()
	t = datetime.datetime.fromtimestamp(epochTime)
	return "{year}-{month}-{day}.{hour}.{minute}.{second}".format(year=t.year,month=t.month,day=t.day,hour=t.hour,minute=t.minute,second=t.second)
