#import BeautifulSoup
from bs4 import BeautifulSoup

#import re module for REGEXes
import re

#import pandas
import pandas as pd

#import extractor if all else fails
from sec_api import ExtractorApi

#import OS library
import os

def get_management_from_html(file):

    #open the actual file
    with open(file) as f:
            page = f.read()


    # Regex to find <DOCUMENT> tags
    doc_start_pattern = re.compile(r'<DOCUMENT>')
    doc_end_pattern = re.compile(r'</DOCUMENT>')
    # Regex to find <TYPE> tag prceeding any characters, terminating at new line
    type_pattern = re.compile(r'<TYPE>[^\n]+')


    # Create 3 lists with the span idices for each regex

    ### There are many <Document> Tags in this text file, each as specific exhibit like 10-K, EX-10.17 etc
    ### First filter will give us document tag start <end> and document tag end's <start> 
    ### We will use this to later grab content in between these tags
    doc_start_is = [x.end() for x in doc_start_pattern.finditer(page)]
    doc_end_is = [x.start() for x in doc_end_pattern.finditer(page)]

    ### Type filter is interesting, it looks for <TYPE> with Not flag as new line, ie terminate there, with + sign
    ### to look for any char afterwards until new line \n. This will give us <TYPE> followed Section Name like '10-K'
    ### Once we have have this, it returns String Array, below line will with find content after <TYPE> ie, '10-K' 
    ### as section names
    doc_types = [x[len('<TYPE>'):] for x in type_pattern.findall(page)]

    document = {}

    # Create a loop to go through each section type and save only the 10-K section in the dictionary
    for doc_type, doc_start, doc_end in zip(doc_types, doc_start_is, doc_end_is):
        if doc_type == '10-K':
            document[doc_type] = page[doc_start:doc_end]


    # Write the regex
    regex = re.compile(r'(>Item(\s|&#160;|&nbsp;)(7A|7)\.{0,1})|(ITEM\s(7A|7))')

    # Use finditer to math the regex
    matches = regex.finditer(document['10-K'])

    # Matches
    matches = regex.finditer(document['10-K'])

    # Create the dataframe
    test_df = pd.DataFrame([(x.group(), x.start(), x.end()) for x in matches])

    test_df.columns = ['item', 'start', 'end']
    test_df['item'] = test_df.item.str.lower()

    # Get rid of unnesesary charcters from the dataframe
    test_df.replace('&#160;',' ',regex=True,inplace=True)
    test_df.replace('&nbsp;',' ',regex=True,inplace=True)
    test_df.replace(' ','',regex=True,inplace=True)
    test_df.replace('\.','',regex=True,inplace=True)
    test_df.replace('>','',regex=True,inplace=True)

    if len(test_df.index > 2):
        max_len = 0
        end_index = 0
        start = 0

        for row in test_df.itertuples():
            # if this elt is item7a and the previous elt was item7 (defined by "start" not being 0)
            if row[1] == "item7a" and start != 0:
                # then if the length of this section is the greatest so far
                if (row[3] - start) > max_len:
                    # set this section to be the new max_len
                    max_len = row[3] - start
                    # remember the index of this section
                    end_index = row[0]
            elif row[1] == "item7":
                start = row[2]
            # if the previous elt was a 7a and the current elt is not an item7, then set current start to 0
            else:
                start = 0
        
        # keep only the indices with the greatest distance between start and end
        test_df = test_df.iloc[end_index-1:end_index+1]

    # Drop duplicates
    pos_dat = test_df.sort_values('start', ascending=True).drop_duplicates(subset=['item'], keep='first')

    # Set item as the dataframe index
    pos_dat.set_index('item', inplace=True)

    # Get Item 7
    item_7_raw = document['10-K'][pos_dat['start'].loc['item7']:pos_dat['start'].loc['item7a']]

    ### First convert the raw text we have to exrtacted to BeautifulSoup object 
    item_7_content = BeautifulSoup(item_7_raw, 'lxml')

    item_7_text = item_7_content.get_text("\n\n")

    return item_7_text

def to_txt(file_name, file_output):
    text = get_management_from_html(file_name)

    with open(file_output,"w") as f:
        f.write(text)
    

if __name__ == "__main__":

    counter = 0
    
    starting_dir = "/home/CAMPUS/diaa2019/data/DATA_2019/10-K_2019"

    ending_dir = "/home/CAMPUS/diaa2019/data/MANAGEMENT_DISCUSSION"

    file_names = os.listdir(starting_dir)

    for file in file_names:
        if counter > 10:
            break
        to_txt(os.path.join(starting_dir,file), os.path.join(ending_dir,file))
        counter += 1
        