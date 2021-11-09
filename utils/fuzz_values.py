
#------------------------------------------------
# Import 
#------------------------------------------------

import csv
import string
import random

#------------------------------------------------
# Type List 
#------------------------------------------------

with open('./utils/files/character-sets-1.csv', 'r') as f:
    reader = csv.reader(f, delimiter=',')
    charset_list = [row[1] for row in reader]
    charset_list = charset_list[1:]

with open('./utils/files/content-coding.csv', 'r') as f:
    reader = csv.reader(f, delimiter=',')
    coding_list = [row[0] for row in reader]
    coding_list = coding_list[1:]

mimetype_list = []
for csvfile in ['application.csv', 'font.csv', 'message.csv', 'multipart.csv', 'audio.csv', 'image.csv', 'model.csv', 'video.csv', 'text.csv']:
    with open('./utils/files/'+csvfile, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        tmp = [row[1] for row in reader]
        mimetype_list.extend(tmp[1:])

language_list = ['is', 'ga', 'af', 'sq', 'it', 'id', 'uk', 'nl', 'nl-BE', 'ca', 'gl', 'el', 'hr', 'sv', 'gd', 'es', 'es-AR', 'es-CO', 'es-ES', 'es-MX', 'sk', 'sl', 'sr', 'cs', 'da', 'de', 'de-AU', 'de-CH', 'de-DH', 'tr', 'no', 'eu', 'hu', 'fi', 'fo', 'fr', 'fr-CA', 'fr-CH', 'fr-FR', 'fr-BE', 'bg', 'pl', 'pt', 'pt-BR', 'mk', 'ro', 'ru', 'en', 'en-GB', 'en-US', 'ko', 'zh', 'zh-TW', 'zh-CN', 'ja', 'be']

#------------------------------------------------
# Main Function 
#------------------------------------------------

def get_header_values(header):

    if header == 'Accept':
        return get_Accept_header_values()

    if header == 'Accept-Charset':
        return get_AcceptCharset_header_values()

    if header == 'Accept-Encoding':
        return get_AcceptEncoding_header_values()

    if header == 'Accept-Language':
        return get_AcceptLanguage_header_values()

    if header == 'User-Agent':
        return get_UserAgent_header_values()

    if header == 'Connection':
        return get_Connection_header_values()

#------------------------------------------------
# GET Field Function 
#------------------------------------------------

def get_Accept_header_values():

    rand_num = random.randint(0, len(mimetype_list)+1) 
    try:
        return mimetype_list[rand_num]
    except:
        if random.randint(0,1) == 0:
            return "*/*"
        else:
            return ""

def get_AcceptCharset_header_values():

    rand_num = random.randint(0, len(charset_list)+1) 
    try:
        return charset_list[rand_num]
    except:
        if random.randint(0,1) == 0:
            return "*"
        else:
            return ""

def get_AcceptEncoding_header_values():

    rand_num = random.randint(0, len(coding_list)+1) 
    try:
        return coding_list[rand_num]
    except:
        if random.randint(0,1) == 0:
            return "*"
        else:
            return ""

def get_AcceptLanguage_header_values():

    rand_num = random.randint(0, len(language_list)+1) 
    try:
        return language_list[rand_num]
    except:
        if random.randint(0,1) == 0:
            return "*"
        else:
            return ""

def get_UserAgent_header_values():
    
    win_edge = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'
    win_firefox = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/43.0'
    win_chrome = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"
    lin_firefox = 'Mozilla/5.0 (X11; Linux i686; rv:30.0) Gecko/20100101 Firefox/42.0'
    mac_chrome = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.38 Safari/537.36'
    ie = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0)'
    google_bot = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html'
    iphone = 'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
    android = 'Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36'
    curl = 'curl/7.38.0'
    wget = 'Wget/1.17.1 (linux-gnu)'
    masscan = 'masscan/1.0 (https://github.com/robertdavidgraham/masscan)'
    none = ''

    ua_dict = {
        1: win_edge,
        2: win_firefox,
        3: win_chrome,
        4: lin_firefox,
        5: mac_chrome,
        6: ie,
        7: google_bot,
        8: iphone,
        9: android,
        10: curl,
        11: wget,
        12: masscan,
        13: none
    }

    rand_num = random.randint(1, len(ua_dict))
    return ua_dict[rand_num]
 
def get_Connection_header_values():

    if random.randint(0,1) == 0:
        return "keep-alive"
    else:
        return "close"

