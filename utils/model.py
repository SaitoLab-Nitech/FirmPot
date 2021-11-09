
#------------------------------------------------
# Reference
#------------------------------------------------

# https://www.tensorflow.org/text/tutorials/nmt_with_attention

#------------------------------------------------
# Import
#------------------------------------------------

import tensorflow as tf 

#------------------------------------------------
# Encoder
#------------------------------------------------

class Encoder(tf.keras.Model):

  def __init__(self, vocab_size, embed_dim, enc_units, batch_size, word2vec=None):
    super(Encoder, self).__init__()
    self.batch_size = batch_size
    self.enc_units = enc_units

    if word2vec is None:
      self.embedding = tf.keras.layers.Embedding(vocab_size, embed_dim)
    else:
      self.embedding = tf.keras.layers.Embedding(vocab_size, embed_dim, weights=[word2vec])
    
    self.gru = tf.keras.layers.GRU(self.enc_units,
                                   return_sequences=True,
                                   return_state=True,
                                   recurrent_initializer='glorot_uniform')

  # Input -> Embedding -> GRU -> Output
  def call(self, x, hidden, oov_list=None, moov=None):

    x = self.embedding(x) # x == (batch, input_len, embed_dim)

    # Process OOV
    if oov_list is not None:
      x = x.numpy()
      for oov in oov_list:
        v = moov.query(str(oov[1]))
        x[0, oov[0], :] = v

    x = tf.convert_to_tensor(x)

    output, state = self.gru(x, initial_state = hidden)
    return output, state # enc_output, enc_hidden

  def initialize_hidden_state(self):
    return tf.zeros((self.batch_size, self.enc_units))

#------------------------------------------------
# Atteniton
#------------------------------------------------

class BahdanauAttention(tf.keras.layers.Layer):

  def __init__(self, units):
    super(BahdanauAttention, self).__init__()
    self.W1 = tf.keras.layers.Dense(units)
    self.W2 = tf.keras.layers.Dense(units)
    self.V = tf.keras.layers.Dense(1)

  def call(self, query, values):

    hidden_with_time_axis = tf.expand_dims(query, 1) # shape:(batch_size, 1, hidden size) 

    score = self.V(tf.nn.tanh(
        self.W1(values) + self.W2(hidden_with_time_axis))) # shape:(batch_size, max_length, 1)

    attention_weights = tf.nn.softmax(score, axis=1)

    context_vector = attention_weights * values
    context_vector = tf.reduce_sum(context_vector, axis=1)

    return context_vector, attention_weights

#------------------------------------------------
# Dncoder
#------------------------------------------------

class Decoder(tf.keras.Model):

  def __init__(self, vocab_size, embed_dim, dec_units, batch_size):
    super(Decoder, self).__init__()
    self.batch_size = batch_size
    self.dec_units = dec_units
    self.embedding = tf.keras.layers.Embedding(vocab_size, embed_dim)
    self.gru = tf.keras.layers.GRU(self.dec_units,
                                   return_sequences=True,
                                   return_state=True,
                                   recurrent_initializer='glorot_uniform')
    self.fc = tf.keras.layers.Dense(vocab_size) # full connection

    self.attention = BahdanauAttention(self.dec_units)

  def call(self, x, hidden, enc_output):
    context_vector, attention_weights = self.attention(hidden, enc_output)

    x = self.embedding(x)

    x = tf.concat([tf.expand_dims(context_vector, 1), x], axis=-1)

    output, state = self.gru(x)

    output = tf.reshape(output, (-1, output.shape[2]))

    x = self.fc(output)

    return x, state, attention_weights
