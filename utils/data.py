
#----------------------------------------------------
# Import
#----------------------------------------------------

from __future__ import print_function
import random
import numpy as np
import tensorflow as tf
import os, sys

from sklearn.model_selection import train_test_split

#----------------------------------------------------
# Class
#----------------------------------------------------

class Data(object):

    # Creates an object that gets data from a file
    def __init__(self, data, map_obj, is_request=False, predict=False):
 
        self.map = map_obj

        # Read Data
        if is_request:
            strdata = self._read_reqdata(data) # strdata : [[request1], [request2], ...]
            map_result = list(map(self._convert_to_num, strdata))
        else:
            strdata = self._read_resdata(data) # strdata : [[request1], [request2], ...]
            map_result = strdata
                    
        self.data = [x[0] for x in map_result] # data
        self.lengths = [x[1] for x in map_result] # length
        assert len(self.data) == len(self.lengths) # check

    #----------------------------------------------------
    # Function
    #----------------------------------------------------

    # Read one request
    def _read_reqdata(self, lines):

        dataset = [] # [[request1], [request2], ...]

        for line in lines:

            line = list(line)

            oneline = []
            #oneline.append("<GO>")                
            oneline.append(line[0]) # method               
            oneline.append(line[1]) # path
            oneline.append(line[2]) # query

            # body
            if type(line[4]) == bytes:
                line[4] = line[4].decode()
            oneline.append(line[4]) # body
            
            # Request header
            for header in line[3].split('@@@'):
                oneline.append(header)
            
            oneline.append("<END>")

            dataset.append(oneline)

        return dataset
    
    # Read one response
    def _read_resdata(self, lines):

        dataset = [] # [[request1], [request2], ...]
        
        for line in lines:

            dataset.append(([line[0]], 1)) # ( [<GO>, id], size )
            #dataset.append(([2, line[0], 3], 1)) # ( [<GO>, id], size )

        return dataset

    # Convert String to Number
    def _convert_to_num(self, strdata):

        seq = self.map.string_to_int(strdata)
        l = len(seq)

        return seq, l

    # Pads sequences to max sequence length in a batch.
    def batch_padding(self, inputs, lengths):

        max_len = np.max(lengths)
        padded = []
        for sample in inputs:
            padded.append(
                sample + ([self.map.mapping['<PAD>']] * (max_len - len(sample))))
        return padded

    def padded_numpy_generator(self):

        inputs = self.data
        tensor = tf.keras.preprocessing.sequence.pad_sequences(inputs, padding='post')

        return tensor


