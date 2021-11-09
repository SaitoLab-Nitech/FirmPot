
#------------------------------------------------
# Import
#------------------------------------------------

import sys
sys.dont_write_bytecode = True
import argparse

# My program
from utils import *
from params import docker_config

#------------------------------------------------
# Main
#------------------------------------------------

def run_containers(container_num, docker_config):
    
    for i in range(container_num):

        # Create network
        subnet = docker_config["ip_1st_octet"] + "." + str(int(docker_config["ip_2nd_octet"])+i) + "." + docker_config["ip_3rd_octet"] + "." + docker_config["ip_4th_octet"] + docker_config["subnet_mask"]
        cmd = 'sudo docker network create --driver=bridge --subnet=' + subnet + ' ' + docker_config["network_name"] + str(i)
        run_cmd(cmd)

        # Create container
        cmd = 'sudo docker run -itd --privileged --net=' + docker_config["network_name"] + str(i) + ' --name=' + docker_config["container_name"] + str(i) + " " + docker_config["image_name"]
        print("[*] Run :", cmd)
        run_cmd(cmd)

    success_list = []
    failure_list = []
    ip_list = []
    for i in range(container_num):
        container_name =  docker_config["container_name"] + str(i)
        cmd = "sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' " + container_name
        result = run_cmd(cmd)

        if len(result) > 0:
            success_list.append(container_name)
            ip_list.append(result[0])
        else:
            failure_list.append(container_name)

    print("[*] Finished!")
    if len(success_list) > 0:
        print("[*] Success: ", success_list)
    if len(failure_list) > 0:
        print("[-] Failure: ", failure_list)

    print("[*] List of Accessible IP Address (HTTP)")
    print(' '.join(["http://" + ip for ip in ip_list]))
    print("")
    print("[*] List of Accessible IP Address (HTTPS)")
    print(' '.join(["https://" + ip for ip in ip_list]))
#------------------------------------------------
#  Main
#------------------------------------------------

def main():

    run_containers(container_num, docker_config)



#------------------------------------------------
#  if __name__ == '__main__':
#------------------------------------------------

if __name__ == '__main__':

    # Argument Parser
    parser = argparse.ArgumentParser(description='Delete docker containers, networks, and images created by the booter module.')
    parser.add_argument('-i', '--image', default="", help="Specify the path of the new startup script to be created, or the name of the startup script that exists, if any (default: './startup.sh').")
    parser.add_argument('-c', '--containers', default=1, type=int, help="Specify the number of containers to be launched, or 0 if you don't want to launch any (default: 1).")
    args = parser.parse_args() 

    container_num = args.containers

    main()


