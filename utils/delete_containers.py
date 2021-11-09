

#------------------------------------------------
# Import
#------------------------------------------------

import os
import sys
sys.dont_write_bytecode = True
import argparse

# My program
from params import boot_params, docker_config
from utils import *

#------------------------------------------------
# Main
#------------------------------------------------

def main():

    # ----- Delete containers -----

    # Search the running containers
    container_list = run_cmd("sudo docker ps | grep " + docker_config["container_name"] + " | awk '{print $NF}'")

    if len(container_list) == 0:
        print("[*] Could not find the working containers.")
    else:
        print("[*] There were", len(container_list), "containers running :", container_list)
        print("[?] Do you want to stop and delete them?")
        if yes_no_input(): # user's answer is "yes"
            for container in container_list:
                print("[*] Try to stop and remove :", container)
                run_cmd('sudo docker stop ' + container)
                run_cmd('sudo docker rm ' + container)

    # ----- Delete networks -----

    network_list = run_cmd("sudo docker network ls | grep " + docker_config["network_name"] + " | awk '{print $2}'")
    if len(network_list) == 0:
        print("[*] Could not find the networks.")
    else:
        print("[*] There are", len(network_list), "docker networks :", network_list)
        print("[?] Do you want to delete them?")
        if yes_no_input():
            for network in network_list:
                print("[*] Try to remove :", network)
                run_cmd('sudo docker network rm ' + network)

    # ----- Delete Dockerfile -----

    dockerfile_path = "./Dockerfile"
    if os.path.exists(dockerfile_path):
        print("[?] Do you want to delete the Dockerfile :", dockerfile_path)
        if yes_no_input():
            print("[*] Try to remove :", dockerfile_path)
            run_cmd('rm -f ' + dockerfile_path)


    # ----- Delete filesystem -----

    if os.path.exists(boot_params["filesystem"]):
        print("[?] Do you want to delete the extracted filesystem :", boot_params["filesystem"])
        if yes_no_input():
            print("[*] Try to remove :", boot_params["filesystem"])
            run_cmd('rm -rf '+ boot_params["filesystem"])

    # ----- Delete startup script -----

    if os.path.exists(boot_params["startup"]):
        print("[?] Do you want to delete the startup script :", boot_params["startup"])
        if yes_no_input():
            print("[*] Try to remove :", boot_params["startup"])
            run_cmd('rm '+ boot_params["startup"])

    print("[*] Finished!")

#------------------------------------------------
#  if __name__ == '__main__':
#------------------------------------------------

if __name__ == '__main__':

    # Argument Parser
    parser = argparse.ArgumentParser(description='Delete docker containers, networks, and images created by the booter module.')
    args = parser.parse_args() 
    
    main()

