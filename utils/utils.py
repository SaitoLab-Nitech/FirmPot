
#------------------------------------------------
# Import
#------------------------------------------------

import subprocess

#------------------------------------------------
# Functions
#------------------------------------------------

def run_cmd(cmd):
    """ Run the shell command specified in <cmd> """
    result = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).stdout.readlines()
    return [x.decode().rstrip("\n") for x in result]

def yes_no_input():
    while True:
        choice = input("Please respond with 'yes' or 'no' [Y/n]: ").lower()
        if choice in ['y', 'ye', 'yes', 'Y', 'YE', 'YES', '']:
            return True
        elif choice in ['n', 'no', 'N', 'NO']:
            return False

