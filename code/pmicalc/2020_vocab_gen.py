import nltk
from nltk import ngrams
from nltk.corpus import PlaintextCorpusReader, stopwords
from nltk.collocations import BigramCollocationFinder, BigramAssocMeasures
from nltk.tokenize import RegexpTokenizer
import pandas as pd
import string
import os
import math
import regex as re
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import math
import pickle

'''
This file generates a vocabulary to use for analysis and a dictionary that will let
you look up how many times a word occurs.
Takes a few hours to run
'''
os.chdir("/data/2020_SINCE_JUNE/COMBINED")

output_dir = "/data/pmicalc"
file_type = "10KQ"


reg_tokenizer = RegexpTokenizer(r"[A-Za-z]+-[A-Za-z]+-[0-9]|[a-zA-Z0-9]+-[a-zA-Z0-9]+|[a-zA-Z0-9]+")
corpus = PlaintextCorpusReader(folder, '.*txt',word_tokenizer=reg_tokenizer)
print("text loaded, filtering stopwords now")
stop = stopwords.words('english') + list(string.punctuation)
corpus =[i.lower() for i in corpus.words() if (i.lower() not in stop) and not i.isnumeric()]
print('making freq dist')

fdist1 = nltk.FreqDist(corpus)
freq_dist = dict((word, freq) for word, freq in fdist1.items())
print('created freq distribution')

print('filtering by frequency')
corpus = [c for c in corpus if freq_dist[c] >= 250]
c_len = len(corpus)
vocab = list(set(corpus))
print('writing out to files')
del corpus

os.chdir(output_dir)
np.savez('vocab_filtered_'+file_type,vocabulary=vocab)
pickle.dump(freq_dist ,open('freqdist_'+file_type+'.pkl','wb'))


 




