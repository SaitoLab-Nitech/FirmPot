
#------------------------------------------------
# Import
#------------------------------------------------

import os
import sys
import sqlite3
import argparse
import pandas as pd
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# My program
from params import common_paths

#------------------------------------------------
# Main 
#------------------------------------------------

def main():

	# Learning Table
	if lrn_db != "":
		conn = sqlite3.connect(lrn_db)
		c = conn.cursor()

		c.execute('select * from learning_table')
		raws = c.fetchall()

		columns = ["req_method", "req_path", "req_query", "req_headers", "req_body", "res_id"]

		req_method = []
		req_path = []
		req_query = []
		req_headers = []
		req_body = []
		res_id = []
		for raw in raws:
			req_method.append(raw[0])
			req_path.append(raw[1])
			req_query.append(raw[2])
			req_headers.append(raw[3][:10])
			req_body.append(raw[4])
			res_id.append(raw[5])
			
		df = pd.DataFrame(
			data={'req_method': req_method, 'req_path': req_path, 'req_query': req_query, 'req_headers': req_headers, 'req_body': req_body, 'res_id' : res_id},
			columns=columns
		)
		print("--------------------------------------")
		print(" Learning Table ")
		print("--------------------------------------")
		print(df)

		conn.close()

	# Response Table
	if rsp_db != "":
		conn = sqlite3.connect(rsp_db)
		c = conn.cursor()

		c.execute('select * from response_table')
		raws = c.fetchall()

		columns = ["res_id", "res_status", "res_headers", "res_body"]

		res_id = []
		res_status = []
		res_headers = []
		res_body = []
		for raw in raws:
			res_id.append(raw[0])
			res_status.append(raw[1])
			res_headers.append(raw[2])
			res_body.append(raw[3])
			
		df = pd.DataFrame(
			data={'res_id': res_id, 'res_status': res_status, 'res_headers': res_headers, 'res_body': res_body},
			columns=columns
		)
		print("--------------------------------------")
		print(" Response Table ")
		print("--------------------------------------")
		print(df)

		c.execute('select * from mapping_table')
		raws = c.fetchall()

		columns = ["id", "word"]

		id = []
		word = []
		for raw in raws:
			id.append(raw[0])
			word.append(raw[1])
			
		df = pd.DataFrame(
			data={'id': id, 'word': word},
			columns=columns
		)

		print("--------------------------------------")
		print(" Mapping Table ")
		print("--------------------------------------")
		print(df)

		conn.close()


	sys.exit()
"""
#c.execute('select * from mapping_table')
#c.execute('select * from response_table')
raws = c.fetchall()

for raw in raws:
    #print(raw[0], len(raw[3]), raw[1], raw[2])
    print(raw[5], raw[0], raw[1], raw[2], raw[4], raw[3])
	#print("[*] ", type(raw[1]))




# Table "response"
c.execute('select * from response')
raws = c.fetchall()

for raw in raws[:]:
    print(raw[0], len(raw[3]), raw[1])
    print(raw[2])
    print()
    #print(repr(raw[3]))
    print()

print("[*] All response :", len(raws))
conn.close()

#sys.exit()
print()
print("------------------------------------")
print()

db = "../" + firmware_name + "/request.db"
conn = sqlite3.connect(db)
c = conn.cursor()

# Table "request"
c.execute('select * from request')

raws = c.fetchall()

for raw in raws[:]:
    print(raw[5], raw[0], raw[1], raw[2], raw[4], raw[3])
    print()

print("[*] All request :", len(raws))

conn.close()
"""

if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('-l', '--learning', default="", help='(explain)')
	parser.add_argument('-r', '--response', default="", help='(explain)')
	args = parser.parse_args()

	rsp_db = args.response
	if rsp_db != "":
		if not os.path.exists(rsp_db):
			print("[-]")
			rsp_db = ""


	lrn_db = args.learning
	if lrn_db != "":
		if not os.path.exists(lrn_db):
			print("[-]")
			lrn_db = ""

	
	main()

