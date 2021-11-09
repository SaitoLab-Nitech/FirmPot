
#------------------------------------------------
# Path Information
#------------------------------------------------

common_paths = {}
common_paths["directory"] = "./honeypot/"
common_paths["instance"] = "./honeypot_instance/"

common_paths["learning_db"] = "./learning.db"
common_paths["response_db"] = "./response.db"
common_paths["word2vec"] = "./word2vec.bin"
common_paths["word2vec_plot"] = "./word2vec.png"
common_paths["checkpoints"] = "./checkpoints/"

common_paths["logs"] = "./logs/"
common_paths["selenium_log"] = "./selenium.log"
common_paths["access_log"] = "./access.log"
common_paths["honeypot_log"] = "./honeypot.log"

#------------------------------------------------
# Booting Parameters
#------------------------------------------------

boot_params = {}
boot_params["filesystem"] = "./extracted_fs/"
boot_params["startup"] = "./startup.sh"

# Configuration for docker containers
docker_config = {}
docker_config["image_name"] = "booter/image" # Name of the Docker image to be created
docker_config["container_name"] = "container-" # Name of the Docker containers to be created
docker_config["network_name"] = "network-" # Name of the Docker networks to be created
docker_config["ip_1st_octet"] = "172" # 1st octet of the Docker network
docker_config["ip_2nd_octet"] = "20" # 2nd octet of the Docker network <- Change only this part
docker_config["ip_3rd_octet"] = "0" # 3rd octet of the Docker network
docker_config["ip_4th_octet"] = "0" # 4th octet of the Docker network
docker_config["subnet_mask"] = "/16" # subnet of the Docker network

#------------------------------------------------
# Scanning Parameters
#------------------------------------------------

scan_params = {}

scan_params["password"] = "password"
scan_params["www_dirname"] = "./www/"
scan_params["timer"] = 3
scan_params["header_num"] = 50

hardware_info = {
    "KERNELINFO": "(specify spec of kernel)",
    "CPUINFO": "(specify spec of cpu)",
    "GPUINFO": "(specify spec of gpu)",
}

#------------------------------------------------
# Training Parameters
#------------------------------------------------

train_params = {}
train_params["batch_size"] = 512
train_params["embed_size"] = 64
train_params["hidden_size"] = 128
train_params["epoch_num"] = 500
train_params["max_input_len"] = 11 

word2vec_params = {}
word2vec_params["window"] = 10
word2vec_params["min_count"] = 1
word2vec_params["iter"] = 200
word2vec_params["workers"] = 5

