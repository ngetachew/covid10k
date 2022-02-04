import nltk
from nltk import ngrams
from nltk.corpus import PlaintextCorpusReader, stopwords
from nltk.collocations import BigramCollocationFinder, BigramAssocMeasures
import pandas as pd
import string
import os
import math
import regex as re
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import math
import pickle

word_list = ['corona','virus', 'coronavirus','ncov', 'sarscov', 'SARS-CoV-2', 'pandemic' ,'epidemic', 'outbreak','lockdown','sarscov','2019-nCoV']
word_set = set(word_list)
os.chdir("/home/CAMPUS/ngaa2019")
'''
corpus = PlaintextCorpusReader('nltk_data', '.*txt')
print("text loaded, filtering stopwords now")
stop = stopwords.words('english') + list(string.punctuation)
corpus =[i.lower() for i in corpus.words() if (i.lower() not in stop) and (re.match(r'^[A-Za-z0-9-]*$', i)) and not i.isnumeric()]

fdist1 = nltk.FreqDist(corpus)
freq_dist = dict((word, freq) for word, freq in fdist1.items())
print('created freq distribution')

print('filtering by frequency')
corpus = [c for c in corpus if freq_dist[c] >= 30]
c_len = len(corpus)
vocab = list(set(corpus))
num_twenty = c_len-20
print('Saving files')
#Save file
#np.save('filteredcorpus1.npy',np.array(corpus[:c_len // 4],dtype=str))
#np.save('filteredcorpus2.npy',np.array(corpus[c_len // 4 : c_len // 2],dtype=str))
#np.save('filteredcorpus3.npy',np.array(corpus[c_len // 2: 3 * c_len // 4],dtype=str))
#np.save('filteredcorpus4.npy',np.array(corpus[3 * c_len // 4 :],dtype=str))
del corpus
#Load parts of it
print('Loading corpus')
#corp1 = np.load('filteredcorpus1.npy',mmap_mode='r')
#corp2 = np.load('filteredcorpus2.npy',mmap_mode='r')
#corp3 = np.load('filteredcorpus3.npy',mmap_mode='r')
#corp4 = np.load('filteredcorpus4.npy',mmap_mode='r')'''
corpus = PlaintextCorpusReader('nltk_data', '.*txt')
print('text loaded, creating freq dist')
freq_dist = pickle.load(open('freqdist.pkl','rb'))
print(type(freq_dist))
vocab = list(np.load('vocab_filtered.npz')['vocabulary'])
N = len(vocab)
C = sum([freq_dist[w] for w in word_list if w in freq_dist])

def generate_co_occurrence_matrix(v):
	#Get corpus again
	co_occ = np.zeros((len(v),len(v)),dtype=np.int32)
	files = corpus.fileids()
	count = len(files)
	progress = 0
	for f in files:
		print('Twenty grams for ' + f +' : '+ str(progress) + '/' +str(count))
		twenty_grams = [' '.join(w) for w in list(ngrams(corpus.raw(f).split(),20))]
		print('Fitting count vectorizer')
		vectorizer = CountVectorizer(analyzer='word',vocabulary=vocab)
		X = vectorizer.fit_transform(twenty_grams)
		co_occ += (X.T * X)
	np.savez_compressed('co_occ_matrix',co_occurrence=co_occ)
	return co_occ,vectorizer.vocabulary_

def generate_co_occurrence_matrix2(corpus_list,context_set, v):
	vocab_index = {word: i for i, word in enumerate(v)}
	context_words = list(context_set)
	#Initialize co-occurrence matrix
	c = []
	count = 1
	for cp in corpus_list:
		twentys = len(cp)-20
		c += [(w%10000 == 0 and print('File number ' + str(count) + ': '+ str(w)+' / '+str(twentys))) or ' '.join(cp[w:w+20]) for w in range(twentys)]
		count += 1
	vectorizer = CountVectorizer(vocabulary=vocab_index,dtype=np.int32)
	print('Fitting count vectorizer')
	X = vectorizer.fit_transform(c)
	co_occ = (X.T * X)
	return co_occ,vocab_index

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
			pmi = math.log10(c_w) + math.log10(N) - math.log10(C) - math.log10(n_w)
			print('word: {} ,pmi: {}'.format(word,pmi))
			pmi_dict['word'].append(word)
			pmi_dict['pmi'].append(pmi)
			count += 1
	df_out = pd.DataFrame(pmi_dict)
	return df_out.sort_values('pmi',ascending=False).reset_index(drop=True)	

print('Generating co-occ matrix')
X,word2index = generate_co_occurrence_matrix(vocab)
print(len(word2index.keys()))
print(len(vocab))
print(set(freq_dist.items()).intersection(set(vocab)))
print(len( list(set(freq_dist.items()).intersection(set(vocab))) ))
df_pmi = calculate_pmi(X, freq_dist, vocab, word2index)
df_pmi.head(1000).to_csv('test-pmi.csv')
print(X.shape)
print(len(vocab))
