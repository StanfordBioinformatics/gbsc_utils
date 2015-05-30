
import dxpy
import os
import subprocess
from argparse import ArgumentParser
import gbsc_utils #module load gbsc_utils
from SequencingRuns import runPaths #module load gbsc_utils

description = ""
parser = ArgumentParser(description=description)

#Note that a user could create a loging token and give that to me instead of user name and password.
# Unfortunately, I don't see a way to login to an account in the background as "dx login" requires the user to select a project, and dxpy doesn't seem to 
# have a login method. Therefore, I'll have to manually authenticate with the user's API token prior to running this script. I'll still have this script
# require their DNAnexus account name so that I can verfiy with "dx whoam" that indeed I am currently logged into their account while this script is running.
parser.add_argument('-a','--account-name',required=True,help="The name of the DNAnexus account to upload the sequencing run to.")
parser.add_argument('-r','--run-name',required=True,help="The name of the sequencing run.")
parser.add_argument('-l','--lane',required=True,help="The lane number on the flow cell.")
parser.add_argument('--compress',action="store_true",help="Presence of this option indicates to not compresses the files before upload (omits call to the --do-not-compress switch to the DNAnexus upload agent).")


args = parser.parse_args()
account_name = args.account_name.lower()
run_name = os.path.basename(args.run_name) #in case a folder path was also supplied
lane = args.lane
compress = args.compress

whoami_cmd = "dx whoami"
stdout,stderr = gbsc_utils.createSubprocess(whoami_cmd)
current_account = stdout.lower().strip()
if current_account != account_name:
	raise Exception("Can't proceed while logged into DNAnexus account '{current_account}' when I should be in the account '{account_name}'!".format(current_account=current_account,account_name=account_name))

run_proj = dxpy.find_one_project(name=run_name,zero_ok=True,more_ok=False,level="VIEW")
print(run_proj)
if run_proj:
	run_proj = run_proj["id"]
else:
	run_proj = dxpy.api.project_new( {"name": run_name} )
	run_proj = run_proj['id']

bams = runPaths.findAllBams(run=run_name,lane=lane)
fastqs = runPaths.findAllFastqs(run=run_name,lane=lane)
#fastqc = runPaths.findAllFastqcs(run=run_name,lane=lane)

upload_cmd_prefix = "ua -p {run_proj} ".format(run_proj=run_proj)
if not compress:
	upload_cmd_prefix+= "--do-not-compress "
	

upload_fastqs_cmd = upload_cmd_prefix + "-f /{lane}/fastq {fastqs}".format(lane=lane,fastqs=" ".join(fastqs))
upload_bams_cmd = upload_cmd_prefix + "-f /{lane}/bam {bams}".format(lane=lane,bams=" ".join(bams))

popens = {}
print("Uploading {len_fastqs} FASTQ files".format(len_fastqs=len(fastqs)))
print(upload_fastqs_cmd)
popen = gbsc_utils.createSubprocess(upload_fastqs_cmd,checkRetcode=False)
#popen = gbsc_utils.createSubprocess("ls",checkRetcode=False) #test line
popens[popen] = upload_fastqs_cmd

if bams:
	print("Uploading {len_bams} BAM files".format(len_bams=len(bams)))
	print(upload_bams_cmd)
	popen = gbsc_utils.createSubprocess(upload_bams_cmd,checkRetcode=False)
	#popen = gbsc_utils.createSubprocess("pwd",checkRetcode=False) #test line
	popens[popen] = upload_bams_cmd

for i in popens:
	retcode = i.wait()
	stdout = i.stdout.read()
	stderr = i.stderr.read()
	if retcode:
		cmd = popens[i]
		raise Exception("Error running command '{cmd}' with returncode {retcode}. stdout = '{stdout}'\n stderr = '{stderr}'\n.".format(cmd=cmd,retcode=retcode,stdout=stdout,stderr=stderr))


