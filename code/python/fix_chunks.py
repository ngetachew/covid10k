import os
import sys
from random import random

'''
fix_chunks.py [directory_of_chunk_files] [output_file]
'''
def main(d,output):
	directory = os.listdir(d)
	n = len(directory)
	# save 5 % for testing
	num_test = int(0.05 * n)
	test_set = {int((n+1)*random()) for x in range(num_test)} 
	outfile = open(f'{output}.txt','a')
	testfile = open(f'{output}-test.txt','a')
	for i, filename in enumerate(directory):
		if not filename.endswith('.txt'):
			continue
		text = open(os.path.join(d,filename),'r')
		#test = 1 if i % flag == 0 else 0
		for idx, chunk in enumerate(text):
			if i in test_set:
				testfile.write(f'{filename}-{idx}\t{filename}\t{chunk}\n')
			else:
				outfile.write(f'{filename}-{idx}\t{filename}\t{chunk}\n')
		text.close()
	outfile.close()
	testfile.close()

if __name__ == '__main__':
	main(sys.argv[1],sys.argv[2])
