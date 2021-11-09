
#------------------------------------------------
# Import
#------------------------------------------------

import re

#------------------------------------------------
# Function
#------------------------------------------------

def check_req_header(field):

    for req_field in request_fields:
        if field == req_field:
            return True
    return False

def check_res_header(field):

    for res_field in response_fields:
        if field == res_field:
            return True
    return False

def get_shaped_header(key, value):
    if key in non_value_fields:
        return key
    else:
        return (key + ": " + value)

# Return the textline of the headers to save to the request database.
def shape_req_headers(allheaders):
    
    headers = ""
    for k,v in allheaders.items():
        if check_req_header(k):
            headers += get_shaped_header(k, v) + "@@@" # word2vecに学習させるために，spaceを変換しています

    return headers[:-3]

# Return the textline of the headers to save to the response database.
def shape_res_headers(allheaders):
    
    headers = ""
    for k,v in allheaders.items():
        if "Set-Cookie" in k:
            v = re.sub(r'expires(.+?); ', '', v) # remove expires (=date)
        if check_res_header(k):
            headers += get_shaped_header(k, v) + "@@@" 

    return headers[:-3]


#--------------------------------------
# HTTP header field 
#--------------------------------------

general_fields = [
    "Cache-Control",
    "Connection",
    "Date",
    "Pragma",
    "Trailer",
    "Transfer-Encoding",
    "Upgrade",
    "Via",
    "Warning"
]

entity_fields = [
    "Allow",
    "Content-Encoding",
    "Content-Language",
    "Content-Length",
    "Content-Location",
    "Content-MD5",
    "Content-Range",
    "Content-Type",
    "Expires",
    "Last-Modified",
    "Link",
]

request_fields = [
    "A-IM",
    "Accept",
    "Accept-Charset",
    "Accept-Charset"
    "Accept-Encoding",
    "Accept-Language",
    "Authorization",
    "Cookie",
    "Cookie2",
    "Expect",
    "From",
    "If-Match",
    "If-None-Match",
    "If-Range",
    "If-Modified-Since",
    "If-Unmodified-Since",
    "Max-Forwards",
    "Range",
    "TE",
    "User-Agent",

]

response_fields = [
    "Age",
    "Accept-Ranges",
    "ETag",
    "Location",
    "Keep-Alive",
    "Proxy-Authenticate",
    "Retry-After",
    "Server",
    "Set-Cookie",
    "Vary",
    "WWW-Authenticate",
    "X-Powered-By",
]

non_value_fields = [
    "Age",
    "Authorization",
    "Date",
    "Content-Length",
    "Host",
    "Referer",
    "Origin",
    "Proxy-Authenticate",
    "Proxy-Authorization",
    "User-Agent",
    "WWW-Authenticate",
]

general_fields.extend(entity_fields)
request_fields.extend(general_fields)
response_fields.extend(general_fields)
