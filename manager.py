

#------------------------------------------------
# Import
#------------------------------------------------

import os
import sys
sys.dont_write_bytecode = True

import time
import argparse
import paramiko

# My program
from utils.utils import *
from utils.params import common_paths

#------------------------------------------------
# Functions
#------------------------------------------------

def prepare_honeypot(local_path):

	if not os.path.exists(local_path):
		run_cmd("mkdir " + local_path)

	# Copy a honeypot.py
	run_cmd("cp ./honeypot.py " + local_path)

	# Copy the response.db
	run_cmd("cp " + common_paths["directory"] + common_paths["response_db"] + " " + local_path) # response_db

	# Copy the checkpoints of model
	run_cmd("mkdir " + local_path + common_paths["checkpoints"])
	with open(common_paths["directory"] + common_paths["checkpoints"] + "checkpoint", 'r') as f:
		lines =  f.readlines()
	ckpt = lines[-1].split(" ")[-1][:-1]
	run_cmd("cp " + common_paths["directory"] + common_paths["checkpoints"] + "checkpoint" + " " + local_path + common_paths["checkpoints"])
	run_cmd("cp " + common_paths["directory"] + common_paths["checkpoints"] + "*" + ckpt + "* " + local_path + common_paths["checkpoints"])

	# Copy the word2vec.bin
	run_cmd("cp " + common_paths["directory"] + common_paths["word2vec"] + " " + local_path)
	run_cmd("mkdir " + local_path + "utils/") # utils
	
	run_cmd("cp utils/oov.py " + local_path + "utils/")
	run_cmd("cp utils/model.py " + local_path + "utils/")
	run_cmd("cp utils/params.py " + local_path + "utils/")
	run_cmd("cp utils/http_headers.py " + local_path + "utils/")

	# Copy the honeypot_setup.sh
	run_cmd("cp ./honeypot_setup.sh " + local_path)

def put_files(sftp, localdir, remotedir):

	for name in os.listdir(localdir):
		localpath = os.path.join(localdir, name)
		remotepath = os.path.join(remotedir, name) 
		
		if os.path.isdir(localpath):
			if not name in sftp.listdir(remotedir):
				sftp.mkdir(remotepath)
			put_files(sftp, localpath, remotepath)
		else:
			print(os.path.join(remotedir, name))
			sftp.put(localpath, remotepath)
		

def put_honeypot(ssh, localdir, remotedir):

	sftp = ssh.open_sftp()

	if not os.path.basename(os.path.dirname(localdir)) in sftp.listdir(remotedir):
		sftp.mkdir(localdir)

	remotedir = os.path.join(remotedir, localdir)

	put_files(sftp, localdir, remotedir)

	sftp.close()

def run_honeypot(ssh, localdir, remotedir, password):

	remotedir = os.path.join(remotedir, localdir)
	#stdin, stdout, stderr = ssh.exec_command("honeypot_setup.sh")
	#stdin, stdout, stderr = ssh.exec_command("cd " + remotedir + " && nohup sudo -S -p '' python3 honeypot.py &")
	stdin, stdout, stderr = ssh.exec_command("cd " + remotedir + " && echo " + password + " | nohup sudo -S python3 honeypot.py &")
	time.sleep(3)
	sys.exit(0)

def get_log(ssh, localdir, remotedir):

	sftp = ssh.open_sftp()

	remotedir = os.path.join(remotedir, localdir + common_paths["logs"])
	sftp.chdir(remotedir)

	sftp.get(remotedir + common_paths["access_log"], localdir + common_paths["access_log"])
	sftp.close()

	run_cmd('mv ' + localdir + common_paths["access_log"] + ' ./log.`date "+%Y%m%d-%H"`')

def stop_honeypot(ssh, localdir, remotedir, password):

	stdin, stdout, stderr = ssh.exec_command("echo " + password + " | sudo -S kill -KILL `ps aux | grep honeypot.py | awk '{print $2}'`")
	print("[*] stdout :", " ".join([out for out in stdout]))
	print("[*] stderr :", " ".join([out for out in stderr]))
	#run_cmd('rm -r ' + set_path + local_path)

def ssh_connect(remote_host, username, password):

	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(remote_host, username=username, password=password, timeout=10)
	
	return ssh 

#------------------------------------------------
# Main
#------------------------------------------------

def main():

	# [1] Prepare a directory for honeypot instance
	if args.create:
		prepare_honeypot(local_path)

	# SSH connection by paramiko
	if args.put or args.run or args.get or args.stop:
		ssh = ssh_connect(remote_host, username, password)

		# [2] push to instance
		if args.put:
			put_honeypot(ssh, local_path, set_path)

		# [3] start honeypot
		if args.run:
			run_honeypot(ssh, local_path, set_path, password)

		# [4] get log
		if args.get:
			get_log(ssh, local_path, set_path)

		# [5] stop honeypot
		if args.stop:
			stop_honeypot(ssh, local_path, set_path, password)

		# Close SSH connection
		ssh.close()

	print("[*] Finish!")


#------------------------------------------------
# if __name__ == '__main__'
#------------------------------------------------

if __name__ == '__main__':

	# Define Arguments
	parser = argparse.ArgumentParser(description='Create and manage the honeypot instance using SSH.')

	parser.add_argument('--create', action='store_true', help='<Flag> Create the honeypot instance.')
	parser.add_argument('--put', action='store_true', help='<Flag> Put the honeypot instance on the remote machine.')
	parser.add_argument('--run', action='store_true', help='<Flag> Run the honeypot on the remote machine.')
	parser.add_argument('--get', action='store_true', help='<Flag> Get the access log of the honeypot.')
	parser.add_argument('--stop', action='store_true', help='<Flag> Stop the honeypot on the remote machine.')

	parser.add_argument('-l', '--local', default=common_paths["instance"], help='Specify the path to the directory of the honeypot instance on the LOCAL machine(default: %s.' % common_paths["instance"])
	parser.add_argument('-r', '--remote', default="~", help='Specify the path to the directory of the honeypot instance will be put on the REMOTE machine. Check the directory permissions.')
	parser.add_argument('-i', '--ip', default="", help='Specify the IP address of the REMOTE machine.')
	parser.add_argument('-u', '--username', default="", help='Specify the username for ssh of the REMOTE machine.')
	parser.add_argument('-p', '--password', default="", help='Specify the password for ssh of the REMOTE machine.')

	args = parser.parse_args()

	# ----- Check Arguments -----

	# Flags
	if not (args.create or args.put or args.run or args.get or args.stop):
		print("[-] Select one or more flags.")
		sys.exit(0)

	# Instance Information
	remote_remote_host = args.ip
	username = args.username
	password = args.password
	if password == "":
		print("[!] No password entered. If you wish, you can hardcode the password.")

	remote_path = args.remote
	local_path = args.local
	if os.path.exists(local_path):
		if len(os.listdir(local_path)) != 0:
			print("[!] There are already files in %s" % local_path)
			print("[?] Do you want to allow overwriting?")
			if not yes_no_input():
				print("[-] Finish")
				sys.exit(0)
	if not local_path.endswith("/"):
		local_path = local_path + "/"

	main()
