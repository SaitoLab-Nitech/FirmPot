
#------------------------------------------------
# Import
#------------------------------------------------

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals 
from __future__ import division

import io
import os
import sys
sys.dont_write_bytecode = True

import time
import sqlite3
import argparse

import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split

# My program
from utils.map import Mapping
from utils.data import Data
from utils.model import Encoder, Decoder
from utils.params import common_paths, train_params, word2vec_params

# Word2Vec
from gensim.models import KeyedVectors
from gensim.models import word2vec

#------------------------------------------------
# GPU Settings
#------------------------------------------------

import logging, warnings

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
# Create Mapping Tables
#------------------------------------------------

def create_mapping_table(dir_path, map_obj):
    """Create a table in the response database that maps words to numbers."""

    # Open the database
    conn = sqlite3.connect(dir_path + common_paths["response_db"])
    c = conn.cursor()

    # Create table
    try:
        c.execute('create table mapping_table(id int, word text, UNIQUE(id, word))')
    except:
        print("[*] The mapping_table is already in the response.db")
        return

    for key, value in map_obj.items():
        try:
            sql = 'insert into mapping_table values(?, ?)'
            c.execute(sql, (value, key))
        except:
            pass

    # Get the max value of response_id
    c.execute('select max(res_id) from response_table')
    max_id = c.fetchall()[0][0]

    if max_id > train_params["max_index"]:
        train_params["max_index"] = max_id

    conn.commit()
    conn.close() 

#------------------------------------------------
# Shape the Word2Vec Matrix for Embedding
#------------------------------------------------

def get_model(word2vec_path, req_data=None):
    """Return the word2vec model."""

    #If <req_data> is not specified, the model is load from <word2vec_path>
    if req_data is None:
        model = KeyedVectors.load_word2vec_format(word2vec_path, binary=True, unicode_errors='ignore')
        return model

    #If <req_data> is specified, the model is created and saved to <word2vec_path>
    else:
        # Prepare data list
        w2v_data = []
        for raw in req_data:

            raw = list(raw)
            tmp = []
            tmp.append(raw[0])
            tmp.append(raw[1])
            tmp.append(raw[2])
            tmp.append(raw[4])

            for header in raw[3].split('@@@'):
                tmp.append(header)

            while len(tmp) < train_params["max_input_len"]:
                tmp.append("<PAD>")

            tmp.append("<END>")

            w2v_data.append(tmp)

        model = word2vec.Word2Vec(sentences=w2v_data, size=train_params["embed_size"], window=word2vec_params["window"], min_count=word2vec_params["min_count"], iter=word2vec_params["iter"], workers=word2vec_params["workers"])
        model.wv.save_word2vec_format(word2vec_path, binary=True)

        return model


def get_embedding_matrix(model, mapping, mapping_size):

    embedding_matrix = np.zeros((mapping_size, model.vector_size), dtype="float32")

    for word, id in mapping.items():
        try:
            embedding_matrix[id] = model.wv[word]
        except KeyError:
            pass

    return embedding_matrix

#------------------------------------------------
# Loss Function
#------------------------------------------------

def loss_function(real, pred):
  mask = tf.math.logical_not(tf.math.equal(real, 0))
  loss_ = loss_object(real, pred)

  mask = tf.cast(mask, dtype=loss_.dtype)
  loss_ *= mask

  return tf.reduce_mean(loss_)

#------------------------------------------------
# Trainer
#------------------------------------------------

@tf.function
def train_step(inputs, targets, enc_hidden):

    loss = 0

    with tf.GradientTape() as tape:

        # Encode
        enc_output, enc_hidden = encoder(inputs, enc_hidden)

        # Prepare decode
        dec_hidden = enc_hidden
        dec_input = tf.expand_dims([0] * train_params["batch_size"], 1) # 開始トークン

        # Predict
        for t in range(0, targets.shape[1]):

            # Decode
            predictions, dec_hidden, _ = decoder(dec_input, dec_hidden, enc_output)

            # Loss
            loss += loss_function(targets[:, t], predictions)

            # Using "Teacher Forcing"
            dec_input = tf.expand_dims(targets[:, t], 1)

    # Batch loss
    batch_loss = (loss / int(targets.shape[1]))

    variables = encoder.trainable_variables + decoder.trainable_variables

    gradients = tape.gradient(loss, variables)

    # Optimize
    optimizer.apply_gradients(zip(gradients, variables))

    return predictions, batch_loss   

#------------------------------------------------
# Predict
#------------------------------------------------

def predict(request):

    inputs = tf.keras.preprocessing.sequence.pad_sequences([request],
                                                           maxlen=train_params["max_input_len"],
                                                           padding='post')
    inputs = tf.convert_to_tensor(inputs)

    result = []

    hidden = [tf.zeros((1, train_params["hidden_size"]))]
    enc_out, enc_hidden = encoder(inputs, hidden)

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
# Evaluate
#------------------------------------------------

def evaluate(req_test, res_test):

    mistake = 0

    for counter, (request, response) in enumerate(zip(req_test, res_test)):
        prediction = predict(request)

        if response != prediction:
            mistake += 1
            print("[-]", response, prediction)
        
    print("[*] Percentage of Collect : {0:.2%}".format((len(req_test)-mistake)/len(req_test)))
    print("[*] Percentage of Mistake : {0:.2%}".format(mistake/len(req_test)))

#------------------------------------------------
# Main
#------------------------------------------------

def main():


    # Training
    print("[*] Start Training")

    # Start timer
    start_time = time.time()

    # Learning parameter
    epochs_num = train_params["epoch_num"]
    steps_num = len(req_data)//train_params["batch_size"]
    
    for epoch in range(epochs_num):
        start = time.time()

        enc_hidden = encoder.initialize_hidden_state()
        total_loss = 0

        for (batch, (inputs, targets)) in enumerate(dataset.take(steps_num)):
            
            predictions, batch_loss = train_step(inputs, targets, enc_hidden)
            total_loss += batch_loss

            # Check
            if batch % 100 == 0:
                print('Epoch {} Batch {} Loss {:.4f}'.format(epoch + 1, batch, batch_loss.numpy()))
                                                                                                        
        # Saving the model every 2 epochs
        if (epoch + 1) % 2 == 0:
            checkpoint.save(file_prefix = checkpoint_prefix)

        print('[*] Epoch {} Loss {:.4f}'.format(epoch + 1, total_loss / epochs_num))
        print('[*] Time taken for 1 epoch {} sec\n'.format(time.time() - start))

    # End timer
    print("[*] Finish :", time.time()-start_time)
        
    # Evaluate
    print("[*] Start Evaluation")
    evaluate(req_test.data, res_test.data)

#------------------------------------------------
# if __name__ == '__main__'
#------------------------------------------------

if __name__ == '__main__':

    # Arguments
    parser = argparse.ArgumentParser(description='Learn the web interaction.')
    parser.add_argument('-d', '--directory', default=common_paths["directory"], help='Specify the directory where the database is stored.')
    parser.add_argument('-w', '--word2vec', default="", help='Specify the path to the word2vec model you want to load.')
    parser.add_argument('-s', '--split', type=float, default='1.0', help='Set the split size of the training data (if the ratio of training to test is 9:1, set 0.9)')
    args = parser.parse_args()

    # ----- Check Arguments -----

    # Directory
    dir_path = args.directory
    if not os.path.exists(dir_path):
        print("[-] The directory path specified in the argument does not exist.")
        sys.exit(0)
    if not dir_path.endswith("/"):
        dir_path = dir_path + "/"

    # Database
    db_path = dir_path + common_paths["learning_db"]
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    map_obj = Mapping(db_path)    
    train_params["mapping"] = map_obj.mapping
    train_params["max_index"] = map_obj.mapping_size

    # Make the mapping table
    create_mapping_table(dir_path, train_params["mapping"])

    # Create checkpoint directory
    train_params["checkpoints"] = "./" + dir_path + common_paths["checkpoints"]
    if not os.path.exists(train_params["checkpoints"]):
        os.makedirs(train_params["checkpoints"])


    # ----- Prepare Training Data ----- 

    # Request
    c.execute('select req_method, req_path, req_query, req_headers, req_body from learning_table')
    req_data = c.fetchall()

    # Response
    c.execute('select res_id from learning_table')
    res_data = c.fetchall()

    # Split data to train
    split_rate = args.split
    if split_rate == 1.0:
        req_train = req_data
        res_train = res_data
        req_test = req_data[:1000]
        res_test = res_data[:1000]
    else:
        req_train, req_test, res_train, res_test = train_test_split(req_data, res_data, train_size=split.rate)

    print("[*] size of train data :", len(req_train))
    print("[*] size of test data :", len(req_test))

    req_train = Data(req_train, map_obj, is_request=True)
    req_test = Data(req_test, map_obj, is_request=True)

    res_train = Data(res_train, map_obj, is_request=False)
    res_test = Data(res_test, map_obj, is_request=False)

    # Make padded numpy's tensor
    req_gen = req_train.padded_numpy_generator() # numpy:[[request1][request2]...]
    res_gen = res_train.padded_numpy_generator()

    # Make dataset of tf.data
    dataset = tf.data.Dataset.from_tensor_slices((req_gen, res_gen)).shuffle(123)
    dataset = dataset.batch(train_params['batch_size'], drop_remainder=True)

    # DB close
    conn.commit()
    conn.close() 

    # ----- Prepare a Word2Vec Model -----

    word2vec_path = args.word2vec

    if word2vec_path == "":
        word2vec_path = dir_path + common_paths["word2vec"]
        print("[*] Create a new word2vec model in", word2vec_path)
        word2vec = get_model(word2vec_path, req_data)
        embedding_matrix = get_embedding_matrix(word2vec, train_params["mapping"], train_params["max_index"])

    elif os.path.exists(word2vec_path):
        print("[*] Load the model from", word2vec_path)
        word2vec = get_model(word2vec_path)
        embedding_matrix = get_embedding_matrix(word2vec, train_params["mapping"], train_params["max_index"])

    else:
        print("[-] Could not find", word2vec_path)
        sys.exit(0)

    # Define Model
    encoder = Encoder(train_params["max_index"], train_params["embed_size"], train_params["hidden_size"], train_params["batch_size"], embedding_matrix)
    decoder = Decoder(train_params["max_index"], train_params["embed_size"], train_params["hidden_size"], train_params["batch_size"])

    # Optimizer
    optimizer = tf.keras.optimizers.Adam()
    loss_object = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True, reduction='none')

    # Checkpoint
    checkpoint_prefix = os.path.join(train_params["checkpoints"], "ckpt")
    checkpoint = tf.train.Checkpoint(optimizer=optimizer,
                                    encoder=encoder,
                                    decoder=decoder)

    # Main
    main()

