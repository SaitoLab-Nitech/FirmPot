
#------------------------------------------------
# Import 
#------------------------------------------------

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals 
from __future__ import division

import os
import sys
sys.dont_write_bytecode = True
import argparse

import traceback
import threading
import socket

import tensorflow as tf
import numpy as np

import sqlite3
import difflib
from gensim.models import KeyedVectors

import logging
import logging.handlers
import warnings

import select
import urllib.parse
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

# My program
from utils.oov import MagnitudeOOV
from utils.model import Encoder, Decoder
from utils.params import common_paths, train_params, hardware_info
from utils.http_headers import check_req_header, get_shaped_header


#------------------------------------------------
# GPU
#------------------------------------------------

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=Warning)
tf.get_logger().setLevel('INFO')
tf.autograph.set_verbosity(0)
tf.get_logger().setLevel(logging.ERROR)

physical_devices = tf.config.experimental.list_physical_devices('GPU')
if len(physical_devices) > 0:
    for k in range(len(physical_devices)):
        tf.config.experimental.set_memory_growth(physical_devices[k], True)
        print("[*] memory growth:", tf.config.experimental.get_memory_growth(physical_devices[k]))
else:
    print("[-] Not enough GPU hardware devices available.")

#------------------------------------------------
# Information
#------------------------------------------------

# Timezone
JST = timezone(timedelta(hours=+9), 'JST')

# Server
ip = "0.0.0.0"
port = 80
honeypot_ip = socket.gethostbyname(socket.gethostname())

# Connection timeout
timeout = 5.0

#------------------------------------------------
# Define Model
#------------------------------------------------

def get_model(word2vec_path=None):

    # Model
    encoder = Encoder(train_params["max_index"], train_params["embed_size"], train_params["hidden_size"], train_params["batch_size"])
    decoder = Decoder(train_params["max_index"], train_params["embed_size"], train_params["hidden_size"], train_params["batch_size"])

    # Optimizer
    optimizer = tf.keras.optimizers.Adam()

    # Checkpoints
    train_params["checkpoints"] = common_paths["checkpoints"]
    checkpoint = tf.train.Checkpoint(optimizer=optimizer,
                                    encoder=encoder,
                                    decoder=decoder)
    # Load checkpoint
    checkpoint.restore(tf.train.latest_checkpoint(train_params['checkpoints']))


    if word2vec_path is None:
        return encoder, decoder
    else:
        model = KeyedVectors.load_word2vec_format(word2vec_path, binary=True, unicode_errors='ignore')
        moov = MagnitudeOOV(word2vec=model)
        return moov, encoder, decoder

#------------------------------------------------
# Prediction Functions
#------------------------------------------------

def get_similar_idx(req):

    simularity = 0
    simular_str = "<EMP>"

    for key in mapping:
        rate = difflib.SequenceMatcher(None, req, key).ratio()    
        if rate > simularity:
            simularity = rate
            simular_str = key

    return mapping[simular_str]

def string_to_int(request_list, is_magnitude=False):

    idx_list = []
    oov_list = []
    
    if is_magnitude:
        for i, req in enumerate(request_list):
            try:
                idx_list.append(mapping[req])
            except:
                idx_list.append(0)
                oov_list.append((i, req))
                
    else:
        for i, req in enumerate(request_list):
            try:
                idx_list.append(mapping[req])
            except:
                idx_list.append(get_similar_idx(req))


    return idx_list, oov_list

def predict(idx_list, oov_list=None, moov=None):

    inputs = tf.keras.preprocessing.sequence.pad_sequences([idx_list],
                                                           maxlen=train_params["max_input_len"],
                                                           padding='post')
    
    inputs = tf.convert_to_tensor(inputs)

    result = []

    hidden = [tf.zeros((1, train_params["hidden_size"]))]
    if oov_list is None:
        enc_out, enc_hidden = encoder(inputs, hidden)
    else:
        enc_out, enc_hidden = encoder(inputs, hidden, oov_list, moov)

    dec_hidden = enc_hidden
    dec_input = tf.expand_dims([0], 0)

    for t in range(1):
        predictions, dec_hidden, attention_weights = decoder(dec_input,
                                                             dec_hidden,
                                                             enc_out)

        predicted_id = tf.argmax(predictions[0]).numpy()

        result.append(predicted_id)

        dec_input = tf.expand_dims([predicted_id], 0)

    return result

#------------------------------------------------
# Replace Function
#------------------------------------------------

def replace_str(string, hardware_info):

    for key, value in hardware_info.items():
        string = string.replace(key, value)

    dt = datetime.now()

    string = string.replace("DATEINFO", dt.strftime('%Y-%m-%d'))
    string = string.replace("TIMEINFO", dt.strftime('%H:%M:%S'))
    string = string.replace("IPINFO", honeypot_ip)

    return string


#------------------------------------------------
# Logging Function
#------------------------------------------------

# Access log
def logging_access(log):
    with open(accesslog, 'a') as f: # to file
        f.write(log)

# Honeypot log
def logging_system(message, is_error, is_exit):

    if not is_error: #CYAN
        print("\u001b[36m[INFO]{0}\u001b[0m".format(message))

        with open(honeypotlog, 'a') as f: # to file
            f.write("[{0}][INFO]{1}\n".format(get_time(), message))

    else: #RED
        print("\u001b[31m[ERROR]{0}\u001b[0m".format(message))
        with open(honeypotlog, 'a') as f: # to file
            f.write("[{0}][ERROR]{1}\n".format(get_time(), message))
        
    if is_exit:
        sys.exit(1)

def get_time():
    return "{0:%Y-%m-%d %H:%M:%S%z}".format(datetime.now(JST))

#------------------------------------------------
# Honeypot Server
#------------------------------------------------

class HoneypotHTTPServer(HTTPServer):

    def server_bind(self):
        HTTPServer.server_bind(self)
        self.socket.settimeout(timeout)

    def finish_request(self, request, client_address):
        request.settimeout(timeout)
        HTTPServer.finish_request(self, request, client_address)

#------------------------------------------------
# Honeypot Request Handler
#------------------------------------------------

class HoneypotRequestHandler(BaseHTTPRequestHandler):
    
    def send_response(self, code, message=None):
        self.log_request(code)
        self.send_response_only(code, message)
        self.error_message_format = "error"
        self.error_content_type = "text/plain"

    def handle_one_request(self):

        # Client IP addr and Port
        clientip = self.client_address[0]
        clientport = self.client_address[1]

        try:
            (r, w, e) = select.select([self.rfile], [], [], timeout)
            
            if len(r) == 0:
                errmsg = "Client({0}) data sending was too late.".format(clientip)
                raise socket.timeout(errmsg)
            else:
                self.raw_requestline = self.rfile.readline(65537) # read request

            # Request is None
            if not self.raw_requestline:
                self.close_connection = True
                return

            # Raw request line
            rrl = str(self.raw_requestline, 'iso-8859-1', errors='ignore')
            rrl = rrl.rstrip('\r\n')

            # Parse
            import re
            parse_request_flag = True
            if re.match("^[A-Z]", rrl) and (rrl.endswith("HTTP/1.0") or rrl.endswith("HTTP/1.1")):
                rrlmethod = rrl[:rrl.index(" ")]
                rrluri = rrl[rrl.index(" ")+1:rrl.rindex(" ")].replace(" ", "%20")
                rrluri = rrluri.replace("\"", "%22")
                rrlversion = rrl[rrl.rindex(" ")+1:]
                rrl2 = rrlmethod + " " + rrluri + " " + rrlversion
                self.raw_requestline = rrl2.encode()
            else:
                parse_request_flag = False

            # Parse failed
            if not self.parse_request() or not parse_request_flag:
                errmsg = "Client({0}) data cannot parse. {1}".format(clientip, str(self.raw_requestline))
                raise ValueError(errmsg)
            
            #------------------------------------
            # Parse a Request
            #------------------------------------
            
            # Request method
            req_method = self.requestline.split(' ')[0]

            # Request path 
            req_path = self.requestline.split(' ')[1].split('?')[0]

            # Request query
            if '?' in self.requestline:
                req_query = self.requestline.split(' ')[1].split('?')[1]
            else:
                req_query = "<EMP>"

            # Request body
            if 'content-length' in self.headers:
                content_len = int(self.headers['content-length'])
                if content_len > 0:
                    post_body = self.rfile.read(content_len)
                    req_body = post_body.decode()
                else:
                    req_body = "<EMP>"
            else:
                req_body = "<EMP>"
            
            #self.protocol_version = "HTTP/1.1"

            # Request list to input to the learinig model
            request_list = []
            request_list.append(req_method)
            request_list.append(req_path)
            request_list.append(req_query)
            request_list.append(req_body)
            
            # Request headers
            req_headers = ""
            for k, v in self.headers.items():
                req_headers += k + ": " + v + "@@@"
                if check_req_header(k):
                    request_list.append(get_shaped_header(k,v.replace(honeypot_ip, '')).replace(" ", "#"))
            req_headers = req_headers[:-3]
 
            # Add <END>
            request_list.append("<END>")
            
            print("[*] Request List :", request_list)

            #------------------------------------
            # Predict Response_id 
            #------------------------------------

            if is_magnitude:
                idx_list, oov_list = string_to_int(request_list, is_magnitude=True)
                print("[*] idx List :", idx_list)
                if len(oov_list) == 0:
                    prediction = predict(idx_list)
                else:
                    prediction = predict(idx_list, oov_list=oov_list, moov=moov)
                res_id = int(prediction[0])    

            else:
                idx_list, _ = string_to_int(request_list)
                print("[*] idx List :", idx_list)
                prediction = predict(idx_list)
                res_id = int(prediction[0])    

            #------------------------------------
            # Parse a Response
            #------------------------------------

            c.execute('select res_status, res_headers, res_body from response_table where res_id = ?', (res_id,))
            response_list = c.fetchall()[0]
    
            res_status = response_list[0]
            res_headers = response_list[1]
            res_body = response_list[2]
    
            # Response status            
            self.send_response(res_status)

            # Response body
            if res_body == "<EMP>":
                res_body = b''
            try:
                if "html" in res_body.decode('utf-8', errors='ignore'):
                    res_body = res_body.decode('utf-8')
                    res_body = replace_str(res_body, hardware_info)
                    res_body = res_body.encode()
            except:
                pass

            # Response headers
            for header in res_headers.split('@@@'):
                key = header.split(': ')[0]
                value = ': '.join(header.split(': ')[1:])

                if len(value) > 0:
                    if key.lower() == "Transfer-Encoding".lower() and "chunked" in value:
                        self.send_header("Content-Length", len(res_body))
                    elif key.lower() == "Content-Encoding".lower():
                        pass
                    else:
                        self.send_header(key, value)
                else:
                    if key.lower() == "Date".lower():
                        self.send_header(key, self.date_time_string())
                    elif key.lower() == "Content-Length".lower():
                        self.send_header(key, len(res_body))

            self.end_headers()
            
            # Response body
            if req_method != "HEAD":
                try:
                    self.wfile.write(res_body)
                except:
                    self.wfile.write(bytes(res_body))

            self.wfile.flush()
            
            # Logging
            logging_access("{n}[{time}]{s}{clientip}{n}{method}{s}{path}{s}{query}{s}{body}{n}{headers}{n}{status_code}{s}{prediction}{n}".format(
                                                                    time=get_time(),
                                                                    clientip=clientip,
                                                                    method=str(req_method),
                                                                    path=repr(req_path),
                                                                    query=repr(req_query),
                                                                    body=repr(req_body),
                                                                    headers=repr(req_headers),
                                                                    status_code=str(res_status),
                                                                    prediction=str(prediction[0]),
                                                                    s=' ',
                                                                    n='\n'
                                                                    ))            

        #----------------------------------------
        # Error
        #----------------------------------------
        
        except socket.timeout as e:
            emsg = "{0}".format(e)
            if emsg == "timed out":
                errmsg = "Session timed out. Client IP: {0}".format(clientip)
            else:
                errmsg = "Request timed out: {0}".format(emsg)
            self.log_error(errmsg)
            self.close_connection = True
            logging_system(errmsg, True, False)

        except Exception as e:
            errmsg = "Request handling Failed: {0} - {1}".format(type(e), e)
            self.close_connection = True
            logging_system(errmsg, True, False)
            return


def main():

    # Honeypot Instanse
    myServer = HoneypotHTTPServer((ip, port), HoneypotRequestHandler)
    myServer.timeout = timeout

    # Logging
    logger = logging.getLogger('SyslogLogger')
    logger.setLevel(logging.INFO)
    logging_system("Honeypot Start. {0}:{1} at {2}".format(ip, port, get_time()), False, False)

    # Start Honeypot Server
    try:
        myServer.serve_forever()
    except KeyboardInterrupt:
        pass

    # Server close
    myServer.server_close()

#------------------------------------------------
# if __name__ == '__main__'
#------------------------------------------------

if __name__ == '__main__':

    # Define Arguments
    parser = argparse.ArgumentParser(description='Honeypot program')
    parser.add_argument('-m', '--magnitude', action='store_true', help='Use the Magnitude Mechanism to Respond.')
    args = parser.parse_args()
    
    # Logfile paths
    if not os.path.exists(common_paths["logs"]):
        os.makedirs(common_paths["logs"])
    accesslog = common_paths["logs"] + common_paths["access_log"]
    honeypotlog = common_paths["logs"] + common_paths["honeypot_log"]

    # Database
    db = common_paths["response_db"]
    conn = sqlite3.connect(db)
    c = conn.cursor()

    # Mapping dictionary
    mapping = {}
    c.execute('select * from mapping_table')
    for m in c.fetchall():
        mapping[m[1]] = m[0]

    # Get the max value of response_id
    c.execute('select max(res_id) from response_table')
    max_id = c.fetchall()[0][0]

    # Set the max index
    if len(mapping) > max_id:
        train_params["max_index"] = len(mapping)
    else:
        train_params["max_index"] = max_id + 1

    # Flag of magnitude
    is_magnitude = args.magnitude
    if is_magnitude:
        word2vec_path = common_paths["word2vec"]
        if not os.path.exists(word2vec_path):
            print("[-] The word2vec path specified in the argument does not exist.")
            sys.exit(0)
        moov, encoder, decoder = get_model(word2vec_path)
    else:
        encoder, decoder = get_model()

    main()




