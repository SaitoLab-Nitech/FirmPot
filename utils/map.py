
#-----------------------------------------------------------
# Import
#-----------------------------------------------------------

import sqlite3

#-----------------------------------------------------------
# Class 
#-----------------------------------------------------------

class Mapping():

    def __init__(self, db):

        conn = sqlite3.connect(db)
        c = conn.cursor()

        self.mapping = {}
        self.mapping['<PAD>'] = 0
        self.mapping['<END>'] = 1
        self.mapping['<EMP>'] = 2
        self.num = 3

        # Request
        c.execute('select req_method, req_path, req_query, req_headers, req_body from learning_table')
        datas = c.fetchall()
        self.word_split(datas)

        # key:value -> value:key
        self.reverse_mapping = {v : k for k, v in self.mapping.items()}

        c.execute('select max(res_id) from learning_table')
        self.mapping_size = c.fetchall()[0][0] + 1

        if self.mapping_size < len(self.mapping):
            self.mapping_size = len(self.mapping)

        print("[*] train mapping size :", self.mapping_size)

    def word_split(self, datas):

        for data in datas:

            data = list(data)
            
            # Request method
            if data[0] not in self.mapping:
                self.mapping[data[0]] = self.num
                self.num += 1

            # Request path
            if data[1] not in self.mapping:
                self.mapping[data[1]] = self.num
                self.num += 1

            # Request query
            if data[2] not in self.mapping:
                self.mapping[data[2]] = self.num
                self.num += 1

            # Request header
            for header in data[3].split('@@@'):
                if header not in self.mapping:
                    self.mapping[header] = self.num
                    self.num += 1                

            # Request body
            if type(data[4]) == bytes:
                data[4] = data[4].decode()

            if data[4] not in self.mapping:
                self.mapping[data[4]] = self.num
                self.num += 1
            
    # String -> Integer
    def string_to_int(self, linelist):

        char_ids = []

        for line in linelist:
            try:
                if len(line) > 0:                
                    char_ids.append(self.mapping[line])
                else:
                    char_ids.append(self.mapping['<EMP>'])
            except:
                char_ids.append(self.mapping['<UNK>'])

        return char_ids

    # Integer -> String 
    def int_to_string(self, char_ids):
        
        characters = []

        for i in char_ids:
            characters.append(self.reverse_mapping[i])

        return characters


