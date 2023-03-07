#import BeautifulSoup
from bs4 import BeautifulSoup

#import re module for REGEXes
import re

#import pandas
import pandas as pd

#import OS library
import os

#import linecache

def get_management_from_html(file):

    #open the actual file
    with open(file) as f:
        page = f.read()

    print(file)

    # UNNECESSARY
    """
    # We want to know what date the thing was filed on
    file_date = ''
    company_name = ''

    file_date = linecache.getline(file,8)
    company_name = linecache.getline(file,14)
    """


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
        if doc_type == '10-Q':
            document[doc_type] = page[doc_start:doc_end]


    # Write the regex
    regex = re.compile(r'(Item(\s+|&#160;|&nbsp;|&#xa0;)(2|3)\.{0,1})|(ITEM(\s+|&#160;|&nbsp;|&#xa0;)(2|3)\.{0,1})')

    # Use finditer to math the regex
    matches = regex.finditer(document['10-Q'])

    print("these are matches: ")
    for match in matches:
        print(match)
    print("this is the end of matches")

    # Matches
    matches = regex.finditer(document['10-Q'])

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
    test_df.replace('\n','',regex=True,inplace=True)

    print("THIS IS THE DATAFRAME OF MATCHES:")
    print(test_df)

    if len(test_df.index > 2):
        max_len = 0
        end_index = 0
        start = 0

        for row in test_df.itertuples():
            # if this elt is item3 and the previous elt was item2 (defined by "start" not being 0)
            if row[1] == "item3" and start != 0:
                # then if the length of this section is the greatest so far
                if (row[3] - start) > max_len:
                    # set this section to be the new max_len
                    max_len = row[3] - start
                    # remember the index of this section
                    end_index = row[0]
                # regardless of if anything is found, set start to 0 again and search for the next possible section
                start = 0
            elif row[1] == "item2":
                start = row[2]
            # if the previous elt was a 3 and the current elt is not an item2, then set current start to 0
            else:
                start = 0
        
        # keep only the indices with the greatest distance between start and end
        test_df = test_df.iloc[end_index-1:end_index+1]

    # Drop duplicates
    pos_dat = test_df.sort_values('start', ascending=True).drop_duplicates(subset=['item'], keep='first')

    # Set item as the dataframe index
    pos_dat.set_index('item', inplace=True)

    # Get Item 2
    item_2_raw = document['10-Q'][pos_dat['start'].loc['item2']:pos_dat['start'].loc['item3']]

    ### First convert the raw text we have to exrtacted to BeautifulSoup object 
    item_2_content = BeautifulSoup(item_2_raw, 'lxml')

    item_2_text = item_2_content.get_text("\n\n")

    #item_2_text = file_date + "\n\n" + company_name + "\n\n" + item_2_text

    #print("This is file_date")
    #print(file_date)

    return item_2_text

def to_txt(file_name, file_output):
    text = get_management_from_html(file_name)

    with open(file_output,"w") as f:
        f.write(text)
    

if __name__ == "__main__":

    counter = 0
    failures = 0
    succeses = 0

    # For 2019:
    starting_dir = "/home/CAMPUS/diaa2019/data/DATA_2019/10-Q_2019"

    ending_dir = "/home/CAMPUS/diaa2019/data/10Q_MANAGEMENT_DISCUSSION_2019"

    # For 2020:
    """
    starting_dir = "/home/CAMPUS/diaa2019/data/DATA_2020/10-Q_2020"

    ending_dir = "/home/CAMPUS/diaa2019/data/10Q_MANAGEMENT_DISCUSSION_2020"
    """

    # For 2021
    """
    starting_dir = "/home/CAMPUS/diaa2019/data/DATA_2021/10-Q_2021"

    ending_dir = "/home/CAMPUS/diaa2019/data/10Q_MANAGEMENT_DISCUSSION_2021"
    """

    file_names = os.listdir(starting_dir)

    failures_list = []

    file = "50172-10-Q-20190426.txt"

    to_txt(os.path.join(starting_dir, file), os.path.join(ending_dir, file))


    """
    for file in file_names:
        # THIS IS HERE FOR TESTING. DO NOT REMOVE, YOU WILL PROBABLY NEED IT AGAIN
        #if counter > 500:
        #    break
        
        #to_txt(os.path.join(starting_dir,file), os.path.join(ending_dir,file))


        counter = counter + 1
        try:
            print(counter)
            print("Before to_txt")
            to_txt(os.path.join(starting_dir,file), os.path.join(ending_dir,file))
            print("After to_txt")
            succeses = succeses + 1
        except:
            failures_list.append(file)
            failures = failures + 1

        
        
    print(failures_list)
    print("Number of failures: " + str(failures))
    print("Number of successes: " + str(succeses))
    print("Success percentage: " + str(succeses/(failures+succeses)))

    df = pd.DataFrame(failures_list, columns = ['doc_name'])

    df.to_csv('/home/CAMPUS/diaa2019/covid10k/code/python/discussion_analysis/10Q_2019_fails.csv')
    #df.to_csv('/home/CAMPUS/diaa2019/covid10k/code/python/discussion_analysis/10Q_2020_fails.csv')
    #df.to_csv('/home/CAMPUS/diaa2019/covid10k/code/python/discussion_analysis/10Q_2021_fails.csv')

    """



