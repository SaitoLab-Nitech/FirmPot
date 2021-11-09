
#------------------------------------------------
# Reference
#------------------------------------------------

# https://github.com/yagays/oov_magnitude_ja

#------------------------------------------------
# Import
#------------------------------------------------

import xxhash
import neologdn
import numpy as np
from simstring.searcher import Searcher
from simstring.database.dict import DictDatabase
from simstring.measure.cosine import CosineMeasure
from simstring.feature_extractor.character_ngram import CharacterNgramFeatureExtractor

#------------------------------------------------
# Functions
#------------------------------------------------

def seed(s):
    return xxhash.xxh32(s.encode("utf-8")).intdigest()


def ngram(words, n):
    return ["".join(t) for t in list(zip(*(words[i:] for i in range(n))))]


def character_ngram(word, n_begin=3, n_end=5):
    output = []
    n = n_begin
    while n <= n_end:
        output += ngram(word, n)
        n += 1
    return output

#------------------------------------------------
# Class
#------------------------------------------------

class MagnitudeOOV():
    
    def __init__(self, word2vec):
        
        self.w2v = word2vec
        self.embedding_dim = self.w2v.vector_size
        self.vocab = set(self.w2v.vocab.keys())

        self.db = DictDatabase(CharacterNgramFeatureExtractor(2))
        for vocab_word in self.vocab:
            self.db.add(vocab_word)

    def generate_pseudorandom_vector(self, word):
        """calculate PRVG form CGRAM"""
        vectors = []
        ngram_list = character_ngram(word)
        for ngram in ngram_list:
            np.random.seed(seed(ngram))
            vectors.append(np.random.uniform(-1, 1, self.embedding_dim))
        return np.mean(vectors, axis=0)

    def similar_words_top_k(self, query, measure=CosineMeasure(), initial_threshold=0.99, dec_step=0.01, k=3):
        """search similar words by using edit distance"""
        searcher = Searcher(self.db, measure)
        t = initial_threshold
        similar_words = []
        while True:
            similar_words = searcher.search(query, t)

            if len(similar_words) >= k or t <= 0.1:
                break
            t -= dec_step

        if len(similar_words) > 3:
            np.random.choice(42)
            return np.random.choice(similar_words, k, replace=False).tolist()
        else:
            return similar_words

    def generate_similar_words_vector(self, word):
        """calculate MATCH from similar words"""
        vectors = np.mean([self.w2v[w] for w in self.similar_words_top_k(word)], axis=0)
        return vectors

    def out_of_vocab_vector(self, word):
        vector = self.generate_pseudorandom_vector(word) * 0.3 + self.generate_similar_words_vector(word) * 0.7
        final_vector = vector / np.linalg.norm(vector)

        if np.isnan(final_vector).any(axis=0):
            return np.nan_to_num(self.generate_similar_words_vector(word))
        else:
            return final_vector

    def query(self, word):
        normalized_word = neologdn.normalize(word)

        if word in self.vocab:
            return self.w2v[word]
        elif normalized_word in self.vocab:
            return self.w2v[normalized_word]
        else:
            return self.out_of_vocab_vector(normalized_word)
