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
import scipy.sparse
import csv

'''
This file generates a vocabulary to use for analysis and a dictionary that will let
you look up how many times a word occurs.
Takes a few hours to run
'''
def custom_preprocessor(w):
	if len(w) < 30 and re.match('[a-zA-z]',w):
		return w.strip().lower()
	else:
		return ''
	
#File path to where the folder that the data is in is.
#Folder the data is in
files = ['/newdata/10-19_DATA_CLEAN_2019/10K/' + f for f in os.listdir('/newdata/10-19_DATA_CLEAN_2019/10K')] + ['/newdata/10-19_DATA_CLEAN_2019/10Q/' + f for f in os.listdir('/newdata/10-19_DATA_CLEAN_2019/10Q')] + ['/newdata/10-19_DATA_CLEAN_2020/10K2/' + f for f in os.listdir('/newdata/10-19_DATA_CLEAN_2020/10K2')] + ['/newdata/10-19_DATA_CLEAN_2020/10Q/' + f for f in os.listdir('/newdata/10-19_DATA_CLEAN_2020/10Q')] + ['/newdata/10-19_DATA_CLEAN_2021/10K/' + f for f in os.listdir('/newdata/10-19_DATA_CLEAN_2021/10K')] + ['/newdata/10-19_DATA_CLEAN_2021/10Q/' + f for f in os.listdir('/newdata/10-19_DATA_CLEAN_2021/10Q')]
#Directory where you want the data to be outputted
output_dir = "/newdata"
#Named based on what type of files you're looking a, either 10K's, 10Q's or combined (10KQ).
file_type = '10KQ_11-7'

reg = r"[A-Za-z]+-[A-Za-z]+-[0-9]|[a-zA-Z0-9]+-[a-zA-Z0-9]+|[a-zA-Z0-9]+"
stop = [item for sublist in list(csv.reader(open('stop_list.csv',newline=''))) for item in sublist]
print(stop)  
print('running cv')
cv = CountVectorizer(input = 'filename',token_pattern = reg,stop_words=stop, min_df = 15, dtype = np.int32)
print('count vectorizer')
X = cv.fit_transform(files)
print('files fitted')
print(X.shape)
pickle.dump(cv,open(f'cv_{file_type}.pkl','wb'))


vocab = cv.get_feature_names()
os.chdir(output_dir)
scipy.sparse.save_npz(f'sparse_matrix_{file_type}.npz', X)

vocab = cv.get_feature_names()
print('saving vocab')
np.savez('vocab_filtered_'+file_type,vocabulary=vocab)

#small = X.astype(np.int16)
count_list = X.astype(np.int16).toarray().sum(axis=0)
freq_dist = dict(zip(vocab,count_list))

del vocab
print('Saving freq dist')
pickle.dump(freq_dist ,open('freqdist_'+file_type+'.pkl','wb'))
