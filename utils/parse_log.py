
#------------------------------------------------
# Import
#------------------------------------------------

import re
import os
import sys
import glob
import json
import pygeoip
import pandas as pd

#------------------------------------------------
# Functions
#------------------------------------------------

def get_data(paths):

    columns = ["date", "time", "src_ip", "dst_ip", "req_method", "req_path", "req_query", "req_header", "req_body", "res_id", "res_status"]
    access_df = pd.DataFrame(columns=columns) 

    for path in paths:

        if os.path.isfile(path): # file
            print("[*] Check", path)
            access_df = analyze_log(path, access_df)

        elif os.path.isdir(path): # directory
            logfiles = glob.glob(path + "*log*")
            print("[*] Check", logfiles)
            for logfile in logfiles:
                access_df = analyze_log(logfile, access_df)

    print("[*] access_df", access_df)
    create_json(access_df)


    return access_df

def get_dst_ip(lines):

    reip = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    found_ips = {}

    for i in range(0, len(lines), 5):
        req_header = lines[i+3]
        match = re.findall(reip, req_header)

        if len(match) > 0:
            for m in match:
                if m in found_ips:
                    found_ips[m] += 1
                else:
                    found_ips[m] = 0

    if found_ips:
        return max(found_ips, key=found_ips.get)
    else:
        return 0

def analyze_log(logfile, access_df):

    with open(logfile, 'r') as f:
        lines =  f.readlines()

    dst_ip = get_dst_ip(lines)

    for i in range(0, len(lines), 5):

        # ----- Parse -----

        # Timestamp
        date = lines[i+1].split(' ')[0][1:]
        time = lines[i+1].split(' ')[1][:-1]

        # Src IPaddress
        src_ip = lines[i+1].split(' ')[-1][:-1]

        # Request
        req_method = lines[i+2].split(' ', 3)[0]
        req_path = lines[i+2].split(' ', 3)[1]
        req_query = lines[i+2].split(' ', 3)[2]
        req_body = lines[i+2].split(' ', 3)[3]
        req_body = req_body[2:-1].replace("'", "")
        req_header = lines[i+3]

        # Response
        res_status = lines[i+4].split(' ', 3)[0]
        res_id = lines[i+4].split(' ', 3)[1][:-1]

        access = pd.Series([date, time, src_ip, dst_ip, req_method, req_path, req_query, req_header, req_body, res_id, res_status], index=access_df.columns)
        access_df = access_df.append(access, ignore_index=True)

    return access_df

def create_json(access_df):

    # GeoIP
    gi = pygeoip.GeoIP('./utils/files/GeoLiteCity.dat', pygeoip.const.MEMORY_CACHE)

    ip_df = access_df.loc[:, ["date", "src_ip", "dst_ip"]]
    ip_df = ip_df.drop_duplicates(["date", "src_ip", "dst_ip"])

    # Location
    data = []

    for index, item in ip_df.iterrows():
        try:
            src_loc = gi.record_by_addr(item["src_ip"])
            dst_loc = gi.record_by_addr(item["dst_ip"])
            data.append({
                        'date' : item["date"],
                        'src_ip' : item["src_ip"],
                        'src_lat' : src_loc['latitude'],
                        'src_long' : src_loc['longitude'],
                        'dst_ip' : item["dst_ip"],
                        'dst_lat' : dst_loc['latitude'],
                        'dst_long' : dst_loc['longitude']

                        })
        except:
            pass

    with open('./static/data.json', 'w+') as dataFile:
        dataFile.write("var data = ")
        json.dump(data, dataFile)
