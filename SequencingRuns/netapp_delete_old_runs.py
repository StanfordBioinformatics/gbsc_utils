import time
import os
import logging

COMPLETED_RUNS_PATH = "/seqctr/Runs/Runs_Completed"
ABORTED_RUNS_PATH = "/seqctr/Runs/Runs_Aborted"


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.DEBUG)
f_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:   %(message)s')
ch.setFormatter(f_formatter)
logger.addHandler(ch)

for i in os.path.listdir(COMPLETED_RUNS_PATH):
	if not os.path.isdir(i):
		continue
	seconds_diff = time.time() - os.path.getmtime(i)
	dt = datetime.datetime.fromtimestamp(seconds_diff)
	if dt.month >= 1:
		print("Deleting run {run}.".format(run=i))
	
