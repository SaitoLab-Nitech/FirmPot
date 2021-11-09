
#------------------------------------------------
# Import
#------------------------------------------------

import os
import sys
sys.dont_write_bytecode = True

import time
import argparse
import subprocess

# My program
from utils.utils import run_cmd
from utils.params import common_paths, docker_config

#------------------------------------------------
# Main
#------------------------------------------------

def main():

    # [1] Booter
    print("[*] Run booter.py")
    subprocess.run(["python3", "booter.py", firmware_path, "-c", str(container_num)])

    # [2] Scanner
    ip_list = []
    for i in range(container_num):
        container_name =  docker_config["container_name"] + str(i)
        cmd = "sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' " + container_name
        result = run_cmd(cmd)

        if len(result) > 0:
            ip_list.append(result[0])
    print("[*] Number of containers successfully launched :", len(ip_list))


    if len(ip_list) > 0:
        print("[*] Run scanner.py")
        subprocess.run(["python3", "scanner.py", "--login-auto", "-i"] + ["http://" + ip for ip in ip_list])
        #subprocess.run(["python3", "scanner.py", "-i"] + ["https://" + ip for ip in ip_list])
    else:
        print("[-] booter.py failed.")
        sys.exit(0)

    # [3] Learner
    print("[*] Run learner.py")
    subprocess.run(["python3", "learner.py"])
 
    # [4] Manager
    print("[*] Run manager.py")
    subprocess.run(["python3", "manager.py", "--create"])

    print("[*] Finish!")


#------------------------------------------------
# if __name__ == '__main__'
#------------------------------------------------

if __name__ == '__main__':

    # Define Arguments
    parser = argparse.ArgumentParser(description='Automatically generate a honeypot.')
    parser.add_argument('firmware', help="Specify the path to the firmware image.")
    parser.add_argument('-c', '--containers', default=1, type=int, help="Specify the number of containers to be launched, or 0 if you don't want to launch any (default: 1).")
    args = parser.parse_args()

    # ----- Check Arguments -----

    # Path to firmware image
    firmware_path = args.firmware
    if not os.path.exists(firmware_path):
        print("[-] The path to the firmware image is incorrect.")
        sys.exit(0)

    # Number of containers to run
    container_num = args.containers

    main()
