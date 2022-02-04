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

#Variables that specify where the data is
data_dir = '/newdata'
data_folder = '10-19_DATA_CLEAN_2021'
output_dir = '/newdata'
file_type = '10KQ_2021'
#Get lexicon and filter the escape chars
lexicon = [item for sublist in list(csv.reader(open('lexicon.csv'))) for item in sublist]
lexicon[0] = 'coronavirus'
lex = set(lexicon)
print(f'lexicon loaded, {lexicon}')
#Get vocab as a set for fast lookup
vocab = set(np.load('vocab_final_11-8.npz')['vocabulary'])
#Initialize tokenizers and variables for track progress in the console

token_reg = r"[A-Za-z]+-[A-Za-z]+-[0-9]|[a-zA-Z0-9]+-[a-zA-Z0-9]+|[a-zA-Z0-9]+" 
regex_tokenizer = RegexpTokenizer(token_reg)
os.chdir(data_dir)
corpus = PlaintextCorpusReader(data_folder, '.*txt',word_tokenizer=regex_tokenizer)
print('corpus loaded')
files = corpus.fileids()
count = len(files)
progress = 0


# Data frame with a column with the file name, the file's word count, total lexicon proportion,
# and the proportion of each word in the lexicon
df_counts = pd.DataFrame(index = files, columns=['CIK', 'TokenCount','TotalProportion'] + lexicon, dtype=np.float32)
df_counts[df_counts != 0] = 0
for f in files:
        print(f'File name: {f} , progress: {progress}/{count}')
        total,token_count = 0,0
        for word in corpus.words(f):
                word_lower = word.lower()
                if word_lower in vocab:
                        token_count += 1
                        if word_lower in lex:
                                df_counts.loc[f, word_lower] += 1
                                total += 1
        if token_count == 0:
                continue
        df_counts.loc[f, 'TotalProportion'] = total
        df_counts.loc[f, ['TokenCount','TotalProportion']+lexicon] = df_counts.loc[f].apply(lambda x: x/token_count)
        df_counts.loc[f, 'TokenCount'] = token_count
        cik = f[4:]
        cik = cik.split('-')[0]
        df_counts.loc[f, 'CIK'] = cik
        progress += 1

os.chdir(output_dir)
print('Finished. Dumping to Lexicon_Proportions.csv in ' + output_dir)
df_counts[['CIK', 'TokenCount','TotalProportion']].to_csv('Lexicon_Proportions_' + file_type +'.csv')
df_counts.to_csv('Lexicon_Proportions_Total_' + file_type +'.csv')
