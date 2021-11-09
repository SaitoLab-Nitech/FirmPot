
#--------------------------------------
# Import
#--------------------------------------

import time

# Requests
import requests
import urllib.parse
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from utils.utils import *
from utils.login import *
from utils.http_headers import shape_req_headers, shape_res_headers

#------------------------------------------------
# Functions
#------------------------------------------------

def find_cmd(wwwpath):

    urllist = []    
    result = run_cmd("find "+ wwwpath + " -type f")

    for url in result:
        try:
            url = url[len(wwwpath):]

            if url.startswith("/"):
                urllist.append(url[1:])
            else:
                urllist.append(url)
        except:
            pass

    return urllist

# Search URLs from web page
def find_urls(driver, ip, atag_list, url_list, crawled_list):

    # <a href=...>
    for a in driver.find_elements_by_tag_name("a"):
        url = a.get_attribute("href")
        
        if not url:
            continue
        
        if url.startswith(ip) and "logout" not in url:
            if url not in crawled_list and url not in url_list:
                    url_list.append(url)
                    atag_list.append(a)

    # Sort
    url_list = list(set(url_list))
    
    return atag_list, url_list, crawled_list 



# Crawling
def crawling(driver, ip, atag_list, url_list, crawled_list, flag=False):

    if flag:

        while len(atag_list) > 0 and len(crawled_list) < 100:

            print("[*] found pages:", len(atag_list), " / crawled pages:", len(crawled_list))

            try:
                atag = atag_list.pop(0)

                driver.set_page_load_timeout(1) # set timeout
                atag.click()
                time.sleep(0.5)
                crawled_list.append(atag.get_attribute("href"))
                print("[*]", crawled_list[-1])
                
                find_urls(driver, ip, atag_list, url_list, crawled_list)
            except Exception as e:
                pass

    else:

        while len(url_list) > 0 and len(crawled_list) < 100:

            print("[*] found pages:", len(url_list), "/ crawled pages:", len(crawled_list))

            try:
                url = url_list.pop(0)

                driver.set_page_load_timeout(1) # set timeout
                driver.get(url)
                time.sleep(0.5)

                crawled_list.append(url)
                find_urls(driver, ip, atag_list, url_list, crawled_list)

            except:
                pass
                
    return atag_list, url_list, crawled_list 
