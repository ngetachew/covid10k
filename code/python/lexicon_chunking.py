import nltk
from nltk import ngrams
from nltk.corpus import PlaintextCorpusReader, stopwords
from nltk.tokenize import RegexpTokenizer
import pandas as pd
import string
import os
import math
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import math
import pickle
import csv
import regex as re

'''
1.) Find each sentence with a  lexicon word in each file
2.) Get plus/minus (sent_window) sentences around each sentence found in step 1
3.) Dump them all into a file
'''


#Variables that specify where the data is - Set for antiviral words in 2019
data_dir = '/newdata'
data_folder = '10-19_DATA_CLEAN_2021'
output_dir = '/newdata/2021_Chunked_Files'
file_type = '10KQ'


#Get lexicon and filter the escape chars
lexicon = [item for sublist in list(csv.reader(open('core_lexicon.csv'))) for item in sublist]
lex = set(lexicon)
lex.remove('')
print('lexicon loaded')
print(f'Current lexicon: {lex}')

#Initialize tokenizers and variables for track progress in the console
token_reg = r"[A-Za-z]+-[A-Za-z]+-[0-9]|[a-zA-Z0-9]+-[a-zA-Z0-9]+|[a-zA-Z0-9]+"
regex_tokenizer = RegexpTokenizer(token_reg)
os.chdir(data_dir)
corpus = PlaintextCorpusReader(data_folder, '.*txt',word_tokenizer=regex_tokenizer)
print('corpus loaded')

files = corpus.fileids()
#files = list(pd.read_csv('/data/antiviral_2019_data.csv').File)
count = len(files)
progress = 1


#Scan each file
# OOOOXOXOOXOXOOOOXOO -> OO(OOXOXOOXOXOO)(OOXOO)
os.chdir(output_dir)
sent_window = 2
for f in files[5701:]:
    chunks = []
    print(f'File name: {f} , progress: {progress}/{count}')
    sentences = corpus.sents(f)
    n_sents = len(sentences)
    last_up = 0
    for i,sen in enumerate(sentences):
        for word in sen:
            if word.lower() in lex:
                #Get the window of sentences
                upper = min(i+sent_window+1, n_sents)
                if i <= last_up:
                    lower = last_up
                    chunk = [' '.join(s) for s in sentences[lower:upper]]
                    #Get last chunk and add to end of it
                    chunks[-1] += ''.join(chunk)
                else:
                    lower = max(i-sent_window,0)
                    #Flatten into list of sentence strings
                    chunk = [' '.join(s) for s in sentences[lower:upper]]
                    chunk.append('\n')
                    #Add to chunks but flatten list into 1 string
                    chunks.append('. '.join(chunk))
                last_up = upper
    #Dump the sentence chunks to a file
    chunk_file = open(f[4:-4] + '_chunked.txt','w+')
    #Flatten into one long string with newlines in between each chunk
    chunks = '\n'.join(chunks)
    #Dump to file
    chunk_file.write(chunks)
    chunk_file.close()
    progress += 1




