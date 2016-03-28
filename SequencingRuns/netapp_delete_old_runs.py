#!/usr/bin/env python

import time
import datetime
import sys
import os
import logging
import shutil

COMPLETED_RUNS_PATH = "/seqctr/Runs/Runs_Completed"
ABORTED_RUNS_PATH = "/seqctr/Runs/Runs_Aborted"
DAYS_AGE_LIMIT = 45


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.DEBUG)
#f_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:   %(message)s')
#ch.setFormatter(f_formatter)
logger.addHandler(ch)

completed_runs = [os.path.join(COMPLETED_RUNS_PATH,x) for x in os.listdir(COMPLETED_RUNS_PATH)]
aborted_runs = [os.path.join(ABORTED_RUNS_PATH,x) for x in os.listdir(ABORTED_RUNS_PATH)]

for run_folder in completed_runs + aborted_runs:
  if not os.path.isdir(run_folder):
    continue
  delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(run_folder))
  days = delta.days
  logger.info("Days old: {days}: {run}".format(days=days,run=run_folder))
  if days >= DAYS_AGE_LIMIT:
    #Perorm sanity check - about to remove a directory tree so make sure not in active runs or root.
    # This could occur if someone made the mistake of incorrectly setting COMPLETED_RUNS_PATH or ABORTED_RUNS_PATH.
    dirname = os.path.dirname(run_folder)
    if (dirname == "/") or (dirname == "/seqctr") or (dirname == "/seqctr/Runs"):
      #Abort!
      logger.critical("Can't delete folder in path {dirname} - disallowed. Exiting.".format(dirname=dirname))
      sys.exit(1)

    logger.info("Deleting Data dir in run {run}.".format(run=run_folder))
    dataDir = os.path.join(run_folder,"Data")
    shutil.rmtree(dataDir)
    logger.info("Successfully deleted Data dir in run {run}.".format(run=run_folder))
