import pandas as pd
import string
import os
from nltk import ngrams
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import math
import pickle
import itertools        
'''
Generates a co-occurence matrix using the given data, vocabulary and frequency distribution
'''

#File path to where the folder that the data is in is.
files = ['/newdata/10-19_DATA_CLEAN_2019/10K/' + f for f in os.listdir('/newdata/10-19_DATA_CLEAN_2019/10K')] + ['/newdata/10-19_DATA_CLEAN_2019/10Q/' + f for f in os.listdir('/newdata/10-19_DATA_CLEAN_2019/10Q')] + ['/newdata/10-19_DATA_CLEAN_2020/10K2/' + f for f in os.listdir('/newdata/10-19_DATA_CLEAN_2020/10K2')] + ['/newdata/10-19_DATA_CLEAN_2020/10Q/' + f for f in os.listdir('/newdata/10-19_DATA_CLEAN_2020/10Q')] + ['/newdata/10-19_DATA_CLEAN_2021/10K/' + f for f in os.listdir('/newdata/10-19_DATA_CLEAN_2021/10K')] + ['/newdata/10-19_DATA_CLEAN_2021/10Q/' + f for f in os.listdir('/newdata/10-19_DATA_CLEAN_2021/10Q')]
#Directory where you want the data to be outputted, and where you saved the vocab and freq dist from vocab_gen.py
output_dir = "/newdata"
#Named based on what type of files you're looking a, either 10K's, 10Q's or combined (10KQ).
file_type = '10KQ'

'''
Countvectorizer only creates document-word matricies, so this creates the 20-grams we need from each document in tuples,
then creates a list of all the 20-grams flattened into strings. Countvectorizer treats each 20-gram as a document so we
effectively have a word-word matrix 
'''
def generate_co_occurrence_matrix(v):
        co_occ = np.zeros((v.shape[0],v.shape[0]),dtype=np.int32)
        count = len(files)
        word_map = {vocab[i]:i for i in range(vocab.shape[0])}
        progress = 0
        vocab_set = set(v)
        for f in files:
                print('Twenty grams for ' + f +' : '+ str(progress) + '/' +str(count))
                raw_file = open(f,'r')
                #raw_text = ' '.join(raw_file.read().splitlines()) 
                raw_text = raw_file.read().split()
                raw_file.close()
                twenty_grams = [' '.join(raw_text[i:i+20]).strip() for i in range(len(raw_text)-20)]
                X = np.zeros((1,v.shape[0]))
                print('Looping through twenty_grams')
                for tw in twenty_grams:
                    X = np.zeros((1,v.shape[0]))
                    nonz = []
                    for w in tw.split():
                        if w.lower() in vocab_set:
                            #X[0,word_map[w.lower()]] += 1
                            nonz.append(word_map[w.lower()])
                    nz_combo2 = list(itertools.product(nonz,repeat=2))
                    co_occ[[i[0] for i in nz_combo2],[i[1] for i in nz_combo2]] += 1
                # co_occ[i, j]
                # Split file into 20-grams
                #twenty_grams = [' '.join(w) for w in ngrams(raw_text.split(),20)]
                #print('Fitting count vectorizer')
                #vectorizer = CountVectorizer(analyzer='word',vocabulary=vocab)
                #X = vectorizer.fit_transform(twenty_grams)
                #co_occ += np.matmul(X.T,X)
                progress += 1
                print('done')
        np.savez_compressed('co_occ_matrix_10KQ_11-9',co_occurrence=co_occ)
        return co_occ,word_map

def calculate_pmi(com,freqdist,vocabulary,vocab_index):
        pmi_dict = {'word':[],'pmi':[]}
        print('--Calculating pmi--')
        print('N = ' + str(N) + ', C = ' + str(C))
        a = len(vocabulary)
        count = 0
        for word in vocabulary:
                if (count % 500 == 0):
                        print(str(count) + '/' + str(a))
                n_w = freqdist[word]
                c_w = sum([com[vocab_index[word], vocab_index[w]] for w in word_list if (w in freqdist and w in vocab_index)])
                if(c_w != 0):
                        pmi = math.log10((c_w / C) / (n_w / N)) 
                        print('word: {} ,pmi: {}'.format(word,pmi))
                        pmi_dict['word'].append(word)
                        pmi_dict['pmi'].append(pmi)
                        count += 1
        df_out = pd.DataFrame(pmi_dict)
        return df_out.sort_values('pmi',ascending=False).reset_index(drop=True)

#List of words we're starting with
word_list = ['corona','virus', 'coronavirus','ncov', 'sarscov', 'SARS-CoV-2', 'pandemic' ,'epidemic', 'outbreak','lockdown','sarscov','2019-nCoV']

print('text loaded, loading freq dist and vocab')

os.chdir(output_dir)
freq_dist = pickle.load(open('freqdist_10KQ_11-7.pkl','rb'))
print('Frequency distribution loaded, loading vocab')

#Redo calculations
vocab = np.load('vocab_final_11-8.npz')['vocabulary']
print('Loading co-occ matrix')

print('Calculating N and C')
N = sum([freq_dist[t] for t in vocab])
C = sum([freq_dist[w] for w in word_list if w in freq_dist])
print(N)
print(C)

#Generate the co-occurence matrix and the vocab index	
X, v_index = generate_co_occurrence_matrix(vocab)
#Generate the list of word and their pmi's in sorted order
df_pmi = calculate_pmi(X, freq_dist, vocab,v_index)
print('Top 10 PMI values: ')
print(df_pmi.head(10))
#Dump to csv - top 1000
df_pmi.head(1000).to_csv('pmi10K.csv')
