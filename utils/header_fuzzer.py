
#------------------------------------------------
# Import 
#------------------------------------------------

import sys
import random

# Requests
import requests
import urllib.parse
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# My program
from utils.fuzz_values import *
from utils.http_headers import shape_req_headers, shape_res_headers

#------------------------------------------------
# Header List
#------------------------------------------------

header_keys = [
    "Accept",
    "Accept-Charset",
    "Accept-Encoding",
    "Accept-Language",
    "User-Agent", 
    "Connection"  
]

#------------------------------------------------
# Functions
#------------------------------------------------

def header_fuzzer_list(number):

    headers_list = []

    for _ in range(number):

        headers = ""

        # Select keys of header
        header_num = random.randint(1,6)
        header_list = random.sample(header_keys, header_num)

        for header in header_list:
            headers += header + ": " +  get_header_values(header) + "@@@"
        headers = headers[:-3]

        headers_list.append(headers)
    
    return headers_list

def header_fuzzer():

    headers = {}

    # Select keys of header
    header_num = random.randint(1,6)
    header_list = random.sample(header_keys, header_num)

    for header in header_list:
        headers[header] = get_header_values(header)

    return headers

#------------------------------------------------
# Main
#------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage : python3 header_fuzzer.py [number]")
        sys.exit()

    number = int(sys.argv[1])

    headers_list = header_fuzzer(number)

    for header in headers_list:
        print(header)