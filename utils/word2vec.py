
#------------------------------------------------
# Import
#------------------------------------------------

import os
import sys
import random
import sqlite3
import argparse
import numpy as np
np.seterr(all='ignore')

# Matplotlib
import matplotlib.cm as cm
import matplotlib.pyplot as plt

# Word2vec
from gensim.models import word2vec
from gensim.models import KeyedVectors

# Dimension reduction
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA

# My program
from oov import MagnitudeOOV
from utils import yes_no_input
from params import common_paths, train_params, word2vec_params

#------------------------------------------------
# Prepare Dataset
#------------------------------------------------

def make_dataset(number, vocab_list):

    vocab_num = len(vocab_list)
    return [vocab_list[random.randrange(0, vocab_num-1)] for _ in range(number)]

#------------------------------------------------
# Prepare Word2Vec and Magnitude
#------------------------------------------------

def get_models(w2v_path, req_data=None):

    if req_data is None:
        model = KeyedVectors.load_word2vec_format(w2v_path, binary=True, unicode_errors='ignore')
        moov = MagnitudeOOV(word2vec=model)

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
            tmp.append("<END>")

            while len(tmp) < train_params["max_input_len"]:
                tmp.append("<PAD>")


            w2v_data.append(tmp)

        model = word2vec.Word2Vec(sentences=w2v_data, size=train_params["embed_size"], window=word2vec_params["window"], min_count=word2vec_params["min_count"], iter=word2vec_params["iter"], workers=word2vec_params["workers"])
        model.wv.save_word2vec_format(w2v_path, binary=True)

        moov = None

    return model, moov

#------------------------------------------------
# Print Similar Words
#------------------------------------------------

def print_word2vec(model, words):

    for word in words:
        try:
            vector = model.wv[word]
            print("[*]", word)
            result = model.most_similar([vector], [], 5)
            
            for r in result:
                print("[*]", r)
            print("")    
        except:
            print("[-] Error :", word)

def print_magnitude(model, moov, oov_words):

    for word in oov_words:
        try:
            print("[*]", word)
            vector = moov.query(word)
            result = model.similar_by_vector(vector)
            for r in result:
                print("[*]", r)
            print("")
        except:
            print("[-] Error :", word)


#------------------------------------------------
# Two-dimensional compression
#------------------------------------------------


def plot_word2vec(model, word_list, w2vplot_path):

    data = tuple([model[w] for w in word_list])
    X = np.vstack(data)

    tsne = TSNE(n_components=2, random_state=0)
    np.set_printoptions(suppress=True)
    tsne.fit_transform(X) 

    #Draw t-SNE with matplotlib
    fig = plt.figure(figsize=(10, 10))
    plt.scatter(tsne.embedding_[0:len(word_list), 0], tsne.embedding_[0:len(word_list), 1])

    for label, x, y in zip(word_list, tsne.embedding_[:, 0], tsne.embedding_[:, 1]):

        plt.annotate(label.replace("#", " "), xy=(x, y), xytext=(0, 0), textcoords='offset points')
    # Save to file
    fig.savefig(w2vplot_path)

def plot_word2vec_pca(model, word_list, w2vplot_path):

    # Existing Words
    data = []
    for word in word_list:
        try:
            data.append(model[word])
        except:
            words.remove(word)

    pca = PCA(n_components=2)
    pca.fit(data)
    data_pca= pca.transform(data)

    length_data = len(data_pca)

    fig=plt.figure(figsize=(20,12),facecolor='w')
    plt.rcParams["font.size"] = 10

    for i in range(len(data_pca)):
        plt.plot(data_pca[i][0], data_pca[i][1], ms=5.0, zorder=2, marker="x", color="red")
        plt.annotate(word_list[i].replace("#", " "), (data_pca[i][0], data_pca[i][1]), size=12)

    # Save to file
    fig.savefig(w2vplot_path)


def plot_magnitude(model, moov, oov_word_list, w2vplot_path):

    oov_data = []
    add_data = []
    add_words = []
    topn = 3

    fig=plt.figure(figsize=(20,12),facecolor='w')
    plt.rcParams["font.size"] = 10

    for word in oov_word_list:
        try:
            oov_data.append(moov.query(word))
        except:
            oov_words.remove(word)
            continue

        vector = moov.query(word)
        result = model.similar_by_vector(vector, topn=topn)

        for r in result:
            add_data.append(model[r[0]])
            add_words.append(r[0])

    pca = PCA(n_components=2)
    colors = cm.rainbow(np.linspace(0, 1, len(oov_data)))

    pca.fit(oov_data)
    data_pca= pca.transform(oov_data)

    for i in range(len(data_pca)):
        plt.plot(data_pca[i][0], data_pca[i][1], ms=5.0, zorder=2, marker="o", color=colors[i])
        plt.annotate(oov_words[i], (data_pca[i][0], data_pca[i][1]), size=12)

    pca.fit(add_data)
    data_pca= pca.transform(add_data)
    
    for i in range(len(data_pca)//topn):
        for j in range(topn):
            plt.plot(data_pca[i*topn+j][0], data_pca[i*topn+j][1], ms=5.0, zorder=2, marker="x", color=colors[i])
            plt.annotate(add_words[i*topn+j], (data_pca[i*topn+j][0], data_pca[i*topn+j][1]), size=12)


    # Save to file
    fig.savefig(w2vplot_path)

#------------------------------------------------
# Main
#------------------------------------------------

def main():

    # Load models
    if db_path == "": # new create
        model, moov = get_models(w2v_path)
    else:
        c_lrn.execute('select req_method, req_path, req_query, req_headers, req_body from learning_table')
        req_data = c_lrn.fetchall()
        model, moov = get_models(w2v_path, req_data)


    vocab_list = model.wv.vocab
    vocab_list = list(vocab_list.keys())

    global word_list, oov_word_list

    if random_num > 0:
        word_list = make_dataset(random_num, vocab_list)

    if len(word_list) > 0:
        print_word2vec(model, word_list)
        plot_word2vec(model, word_list, w2vplot_path)

    if len(oov_word_list) > 0:
        print_magnitude(model, moov, oov_word_list)
        plot_magnitude(model, moov, oov_word_list, w2vplot_path)


#------------------------------------------------
# if __name__ == '__main__'
#------------------------------------------------

if __name__ == '__main__':

    # Define Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--word2vec', default="", help="Specify the word2vec model's file (ex: word2vec.bin). Show the leaning things of word2vec.")
    parser.add_argument('-l', '--leaning', default="", help='Specify the learning table. Create word2vec.bin from the specified table.')
    parser.add_argument('--wordlist', nargs='*', default=[], help='Specify training words separated by spaces.')
    parser.add_argument('--oovlist', nargs='*', default=[], help='Specify OOV words separated by spaces.')
    parser.add_argument('-r', '--random', default=0, type=int, help='Specify int number of training word list')
    args = parser.parse_args()


    # Word2Vec
    w2v_path = args.word2vec

    # Database
    db_path = args.leaning

    if w2v_path == "" and db_path == "": # both are not specified
        print("[-] Specify -w or -l option.")
        sys.exit(0)

    elif w2v_path == "" and db_path != "": # learning table is specified
        if os.path.exists(db_path):
            conn_lrn = sqlite3.connect(db_path)
            c_lrn = conn_lrn.cursor()
        else:
            print("[-] The database path specified in the argument does not exist.")
            sys.exit(0)
        w2v_path = common_paths["directory"] + common_paths["word2vec"]
        print("[*] Create " + w2v_path + " from the learning table")

    elif w2v_path != "" and db_path == "": # word2vec model is specified
        if os.path.exists(w2v_path):
            print("[*] Load", w2v_path)
        else:
            print("[-] The path specified in the argument does not exist.")
            sys.exit(0)
        print("[*] Load " + w2v_path + ".")

    else: # both are specified
        print("[?] Do you want to allow overwriting of", w2v_path)
        if yes_no_input:
            if os.path.exists(db_path):
                conn_lrn = sqlite3.connect(db_path)
                c_lrn = conn_lrn.cursor()
            else:
                print("[-] The database path specified in the argument does not exist.")
                sys.exit(0)
        else:
            sys.exit(0)

    # Word2Vec Plot
    w2vplot_path = common_paths["word2vec_plot"]
    if os.path.exists(w2vplot_path):
        print("[?] Do you want to allow overwriting of", w2vplot_path)
        if not yes_no_input:
            sys.exit(0)

    # Word_list
    word_list = args.wordlist
    oov_word_list = args.oovlist
    
    # Random
    random_num = args.random

    main()
