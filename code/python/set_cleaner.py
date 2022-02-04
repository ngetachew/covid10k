import os
import regex as re
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

files = [f for f in os.listdir('/data/DATA_2019_CLEANED/10Q')]
line_set = set()
with open('all_common.txt') as file:
	lines = file.readlines()
	line_set = set([line.strip() for line in lines])
total = len(files)
count = 0
for f in files:
	if count % 1000 == 0:
		print(f'{count}/{total}')
	out_lines = []
	file1 = open(f'/data/DATA_2019_CLEANED/10Q/{f}', 'r')
	lines = file1.readlines()
	for l in lines:
		stripped = l.strip()
		if stripped not in line_set and not stripped.startswith('us-gaap'):
			out_lines.append(l)
	out_file = open(f'/newdata/10-19_CLEAN_DATA_2019/10Q/{f}','w')
	out_lines = ' '.join([ln+'\n' for ln in out_lines])
	try:
		soup = BeautifulSoup(out_lines,'html.parser')
		out_file.write(soup.get_text())
	except:
		out_file.write(out_lines)
	out_file.close()
	count += 1

