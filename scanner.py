
#------------------------------------------------
# Import
#------------------------------------------------

import os
import sys
sys.dont_write_bytecode = True

import time
import sqlite3
import argparse
import subprocess

# Thread
import threading
from concurrent.futures import ThreadPoolExecutor

# Selenium
from seleniumwire import webdriver

# Requests
import requests
import urllib.parse
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# My program
from utils.http_headers import shape_req_headers, shape_res_headers
from utils.header_fuzzer import *
from utils.login import *
from utils.crawl import *
from utils.mask import mask_str
from utils.params import common_paths, scan_params, boot_params

#------------------------------------------------
# Save to the Database
#------------------------------------------------

def save_to_db(req_method, req_path, req_query, req_headers, req_body, res_status, res_headers, res_body, ip):
    """Save a set of request and response to the database"""

    # Lock start
    lock.acquire()

    global id_counter # response_id

    # Bytes to Strings
    if type(req_query) == bytes:
        req_query = req_query.decode("utf-8")
    if type(req_body) == bytes:
        req_body = req_body.decode("utf-8")

    # Convert space to "#" for training word2vec 
    req_headers = req_headers.replace(" ", "#")
    req_body = req_body.replace(" ", "#")

    try:
        if "html" in res_body.decode('utf-8', errors='ignore'):
            res_body = res_body.decode('utf-8')
            res_body = res_body.replace(ip, "IPINFO")
            res_body = mask_str(res_body)
            res_body = res_body.encode()
    except:
        pass

    try:
        # Is there a matching response in the response table?
        c_rsp.execute('select res_id from response_table where res_status = ? and res_headers = ? and res_body = ?', (res_status, res_headers, res_body))
        res_id = c_rsp.fetchall()[0][0] # If there is a matching response, the response_id is retrieved (if not, go to "except")

        # Save the request to the learning table with the retrieved response_id
        try:
            sql = 'insert into learning_table values(?, ?, ?, ?, ?, ?)'
            c_lrn.execute(sql, (req_method, req_path, req_query, req_headers, req_body, res_id))
        except:
            pass # failed to save

    except:
        try:
            # Save a new response to the response table
            sql = 'insert into response_table values(?, ?, ?, ?)'
            c_rsp.execute(sql, (int(id_counter), int(res_status), res_headers, res_body))

            # Save the request to the learning table with the response_id
            sql = 'insert into learning_table values(?, ?, ?, ?, ?, ?)'
            c_lrn.execute(sql, (req_method, req_path, req_query, req_headers, req_body, int(id_counter)))
            id_counter += 1 # increase response_id
        except:
            pass # failed to save

    # Lock release
    lock.release()

#------------------------------------------------
# Crawling with Selenium
#------------------------------------------------

def crawl_by_selenium(ip, driver, manual_time):
    """Crawling with selenium-wire"""

    # Access to WebUI
    print("[*] Access to web server :", ip)
    driver.get(ip)
    time.sleep(scan_params["timer"])
    
    # Login Operation
    login(driver, scan_params["password"], scan_params["timer"])
    
    atag_list = []
    url_list = []
    crawled_list = []
    
    # Crawling after login
    print("[*] Start crawling by selenium")
    if manual_time == 0:
        time.sleep(scan_params["timer"])
        atag_list, url_list, crawled_list = find_urls(driver, ip, atag_list, url_list, crawled_list)
        atag_list, url_list, crawled_list = crawling(driver, ip, atag_list, url_list, crawled_list, flag=False) # <= If the crawling fails, try setting the flag to True
    else:
        print("[*] Please operate the WebUI for %d seconds" % manual_time)
        time.sleep(manual_time)

    print("[*] Finish Crawling")

    # Capture Traffic
    for request in driver.requests:
    
        if ip in request.url:
            
            # Request
            req_method = request.method # request method
            req_path = request.path # request path
            req_query = request.querystring # request query
            if len(req_query) == 0:
                req_query = "<EMP>"
    
            req_headers = shape_req_headers(request.headers) # request headers
            req_body = request.body.decode('utf-8').replace(ip.split('//')[-1], '') # request body
            if len(req_body) == 0:
                req_body = "<EMP>"
     
            # Response
            try:
                res_status = int(request.response.status_code) # response status
                res_headers = shape_res_headers(request.response.headers) # response headers
                res_body = request.response.body # response body
    
            except: # this will be None if the request has no response
                res_status = 400
                res_headers = ""
                res_body = "Bad Request."

            # Save to DB
            save_to_db(req_method, req_path, req_query, req_headers, req_body, res_status, res_headers, res_body, ip)
    
#------------------------------------------------
# Crawling with Requests
#------------------------------------------------

def crawl_by_requests(ip, urllist):
    """Crawling with the Requests module"""

    for counter, url in enumerate(urllist, 1):
    
        print("[*] Trying", str(counter) + "/" + str(len(urllist)),  "(" + ip + url + ")", "...")
    
        # Request
        req_method = "GET"
        req_headers = "<EMP>"
        req_body = "<EMP>"
    
        # Request path include query
        if "?" in url:
    
            req_path = url.split('?')[0]
            req_query = url.split('?')[-1]
            
            try:
                response = requests.get(ip+req_path, params=dict(urllib.parse.parse_qsl(req_query)), verify=False, timeout=1)
            except Exception as e:
                continue
    
        # Request path don't include query
        else:
    
            req_path = url
            req_query = "<EMP>"
    
            try: # req_query == "<EMP>":
                response = requests.get(ip+req_path, verify=False, timeout=1)
            except Exception as e:
                continue
    
        if not req_path.startswith("/"):
            req_path = "/" + req_path

        # Response
        res_status = int(response.status_code) # status
        res_headers = shape_res_headers(response.headers) # headers
        res_body = response.content # body

        # Save to DB
        save_to_db(req_method, req_path, req_query, req_headers, req_body, res_status, res_headers, res_body, ip)
    
#------------------------------------------------
# Header Fuzzing with Requests
#------------------------------------------------

def header_fuzzing(ip, request_list, cookie):
    """Fuzzing the request headers"""

    for counter in range(scan_params["header_num"]):
    
        # Request headers
        headers = header_fuzzer()
        print("[*] Header Fuzzing (", counter, "/", scan_params["header_num"], ") :", headers, ip)
    
        # Send requests
        for request in request_list:
    
            error_counter = 0
            req_method = request[0] # method
            req_path = request[1] # path
            req_query = request[2] # query
            req_body = request[4] # body
    
            # Avoiding crash of linksys
            """
            if "/cgi-bin/portal.cgi" in req_path:
                continue
            """

            # Cookie
            if "Cookie" in request[3]:
                headers["Cookie"] = cookie
            else:
                if "Cookie" in headers:
                    del headers["Cookie"]
    
            # GET (with query)
            if req_method == "GET" and req_query == "<EMP>":
                try:
                    response = requests.get(ip+req_path, headers=headers, verify=False, timeout=1)
                except Exception as e:
                    continue
    
            # GET (without query)
            if req_method == "GET" and req_query != "<EMP>":
                try:
                    response = requests.get(ip+req_path, params=dict(urllib.parse.parse_qsl(req_query)), headers=headers, verify=False, timeout=1)
                except Exception as e:
                    continue
    
            # POST
            if req_method == "POST":
                try:
                    if req_body != "<EMP>" and req_query != "<EMP>":
                        response = requests.post(ip+req_path, params=dict(urllib.parse.parse_qsl(req_query)), headers=headers, data=dict(urllib.parse.parse_qsl(req_body)), verify=False, timeout=1)
                    elif req_query != "<EMP>":
                        response = requests.post(ip+req_path, params=dict(urllib.parse.parse_qsl(req_query)), headers=headers, verify=False, timeout=1)
                    else:
                        response = requests.post(ip+req_path, headers=headers, verify=False, timeout=1)
                except Exception as e:
                    error_counter += 1
                    continue
    
            # Request headers
            req_headers = shape_req_headers(headers)
    
            # Response
            res_status = int(response.status_code) # status
            res_headers = shape_res_headers(response.headers) # headers
            res_body = response.content # body
    
            # Save to DB
            save_to_db(req_method, req_path, req_query, req_headers, req_body, res_status, res_headers, res_body, ip)
    
#--------------------------------------
# Login Request
#--------------------------------------

def process_login_request():
    """Only login requests are not scanned because it would increase the number of sessions"""

    # Login request
    c_rsp.execute('select res_id from response_table where res_headers like "%Set-Cookie:%"')
    
    try:
        res_id = c_rsp.fetchall()[0][0]
    
        c_lrn.execute('select * from learning_table where res_id == ?', (res_id,))
        requests = c_lrn.fetchall()
    
        for request in requests:
    
            req_method = request[0] # method
            req_path = request[1] # path
            req_query = request[2] # query
            req_body = request[4] # body
            res_id = request[5] # response id
    
            # Bug fixed of GL.iNet
            if dir_path == "glinet":
                c_lrn.execute('update request set res_id = ? where res_id = ?', (res_id + 1, res_id))
                res_id += 1
    
            for req_headers in header_fuzzer_list(scan_params["header_num"]):    
                try:
                    sql = 'insert into request values(?, ?, ?, ?, ?, ?)'
                    c_lrn.execute(sql, (req_method, req_path, req_query, req_headers, req_body, res_id))
                except:
                    pass

    except Exception as e:
        print("[-] Login request is noting.")

#------------------------------------------------
# Main
#------------------------------------------------

def main():

    # Selenium driver
    if is_headless:
        options = webdriver.FirefoxOptions()
        options.headless = True
        driver = webdriver.Firefox(options=options, service_log_path= logpath + common_paths["selenium_log"])
    else:
        options = {
            'suppress_connection_errors': False,
            'connection_timeout': None,
        }
        driver = webdriver.Firefox(seleniumwire_options=options, service_log_path= logpath + common_paths["selenium_log"])

    # ----- Login -----
    if is_login_auto:
        print("[*] Initial Login")
        first_login([ip+login_page for ip in ip_list], driver, scan_params["password"], scan_params["timer"])

    elif is_login_manual:
        print("[*] Initial Login")
        timer = scan_params["timer"]+30
        if yes_no_input():
            print('[!] The login screen is displayed one after another for %d seconds.' % timer)
            print('[!] Please specify "%s" as the password string to complete the password configuration.' % scan_params["password"])
        else:
            print("[-] Canceled.")
            sys.exit(0)

        for ip in ip_list:        
            print("[*] Access to web server :", ip+login_page)
            driver.get(ip+login_page)
            time.sleep(timer) 

    # Timer start
    start_time = time.time()

    # ----- Crawling -----
    print("[*] Start Crawling")

    # Get all files from "www" in the local directory
    urllist = find_cmd(fs_path + scan_params["www_dirname"])
    
    print("[*] The number of all files :", len(urllist))
    
    if container_num == 1:
        crawl_by_selenium(ip_list[0], driver, manual_time)
        #crawl_by_requests(ip_list[0], urllist)
    else: 
        tpe = ThreadPoolExecutor(max_workers=container_num)
        for i in range(container_num):
            if i == 0: 
                tpe.submit(crawl_by_selenium, ip_list[i]+login_page, driver, manual_time)
            else:
                length = len(urllist)//(container_num - 1)
                tpe.submit(crawl_by_requests, ip_list[i], urllist[(i-1)*length : i*length])
    
        # Wait
        tpe.shutdown()

    # Finish
    driver.quit()
    print("[*] Crawling Time :", time.time() - start_time)

    # DB check
    c_rsp.execute('select * from response_table')
    print("[*] All response :", len(c_rsp.fetchall()))
    
    c_lrn.execute('select * from learning_table')
    print("[*] All request :", len(c_lrn.fetchall()))

    # ----- Fuzzing -----
    print("[*] Start Fuzzing")
    
    try:
        c_rsp.execute('select res_id, res_headers from response_table where res_headers like "%Set-Cookie:%"')
        res_id, headers_ = c_rsp.fetchall()[0]
        cookie = [header.split(': ')[1].split(';')[0] for header in headers_.split('@@@') if "Set-Cookie" in header][0]
        
        c_lrn.execute('select * from learning_table where res_id != ?', (res_id,))
        request_list = c_lrn.fetchall()

    except:

        try:
            # Escape login request
            c_lrn.execute('select res_id, req_body from learning_table where req_body not like "<EMP>"')
            tmplist = c_lrn.fetchall()
            res_id = [tmp[0] for tmp in tmplist if '"'+scan_params["password"]+'"' in tmp[1]][0]
            c_lrn.execute('select req_headers from learning_table where req_headers like "%Cookie%"')
            headers_ = c_lrn.fetchall()[0][0]
            cookie = [header.split(':#')[1].split(';')[0] for header in headers_.split('@@@') if "Cookie" in header][0]

            c_lrn.execute('select * from learning_table where res_id != ?', (res_id,))
            request_list = c_lrn.fetchall()

        except:
            cookie = ""
            res_id = 0
            c_lrn.execute('select * from learning_table')
            request_list = c_lrn.fetchall()
    
    print("[*] login res_id", res_id)       
    print("[*] Cookie", cookie)
    
    tpe = ThreadPoolExecutor(max_workers=container_num)
    
    if container_num == 1:
        header_fuzzing(ip_list[0], request_list, cookie)
    else: 
        for i in range(container_num):
            length = len(request_list)//container_num
            tpe.submit(header_fuzzing, ip_list[i], request_list[i*length:(i+1)*length], cookie)

    tpe.shutdown() # wait
    
    # ----- Process Login request -----
    process_login_request()

    # DB check
    c_rsp.execute('select * from response_table')
    print("[*] All response :", len(c_rsp.fetchall()))
    
    c_lrn.execute('select * from learning_table')
    print("[*] All request :", len(c_lrn.fetchall()))
    
    # DB close
    conn_lrn.commit()
    conn_lrn.close() 
    conn_rsp.commit()
    conn_rsp.close() 

    # Timer stop
    print("[*] Finish Time :", time.time() - start_time)
    
#------------------------------------------------
# if __name__ == '__main__':
#------------------------------------------------

if __name__ == '__main__':

    # Define Arguments
    parser = argparse.ArgumentParser(description='Scan the web application.')
    parser.add_argument('-f', '--filesystem', default=boot_params["filesystem"], help="Specify the file system extracted by booter.py.")
    parser.add_argument('-i', '--ipaddress', nargs='*', required=True, help='Specify one or more IP addresses to be used for scanning.It must start with "http://" or "https://".')
    parser.add_argument('-d', '--directory', default=common_paths["directory"], help="Specify the directory where you want to save the database.")
    parser.add_argument('--login-page', default="", help='Specify the login page of the web app. By default, it accesses "http://x.x.x.x/".')
    parser.add_argument('--login-auto', action='store_true', help='The initial login is automatically performed.')
    parser.add_argument('--login-manual', action='store_true', help='The initial login is manually performed.')
    parser.add_argument('--headless', action='store_true', help='Hide the selenuim browser.')
    parser.add_argument('-m', '--manual', type=int, default=0, help='If crawling is to be done manually, specify the number of seconds (default is 0, meaning automatic).')
    args = parser.parse_args()

    # ----- Check Arguments -----

    # Flag
    is_headless = args.headless
    is_login_auto = args.login_auto
    is_login_manual = args.login_manual

    # Time for manual operation in crawling
    manual_time = args.manual
    
    # Login page
    login_page = args.login_page
    if login_page.startswith('/'):
        login_page = login_page[1:]

    # Directory path
    dir_path = args.directory
    if not dir_path.endswith('/'):
        dir_path = dir_path + '/'
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Filesystem
    fs_path = args.filesystem
    if not fs_path.endswith('/'):
        fs_path = fs_path + '/'
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    # IP list
    ip_list = args.ipaddress
    for i, ip in enumerate(ip_list):
        if not ip.endswith('/'):             
            ip_list[i] = ip + '/'
    container_num = len(ip_list)
    print("[*] ip_list", ip_list)

    # Log path
    logpath = dir_path + common_paths["logs"]
    if not os.path.exists(logpath):
        os.makedirs(logpath)

    # Database
    learning_db = dir_path + common_paths["learning_db"]
    conn_lrn = sqlite3.connect(learning_db, check_same_thread = False)
    c_lrn = conn_lrn.cursor()

    response_db = dir_path + common_paths["response_db"]
    conn_rsp = sqlite3.connect(response_db, check_same_thread = False)
    c_rsp = conn_rsp.cursor()

    # Create tables
    try:
        c_lrn.execute('create table learning_table(req_method text, req_path text, req_query text, req_headers text, req_body text, res_id int, UNIQUE(req_method, req_path, req_query, req_headers, req_body))')
        c_rsp.execute('create table response_table(res_id int, res_status int, res_headers text, res_body blob, UNIQUE(res_status, res_headers, res_body))')
    except Exception as e:
        pass

    # Get responne_id and set id_counter (id_counter = response_id)
    try:
        c_lrn.execute('select max(res_id) from learning_table')
        id_counter = c_lrn.fetchall()[0][0] + 1
    except:
        id_counter = 1

    # Thread Exclusion control
    lock = threading.Lock()

    main()
