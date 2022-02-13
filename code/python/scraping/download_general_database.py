import requests
import os
import json
import sys 
"""
Written by Aashita Kesarwani

GENERAL DATABASE that can be used to download 10Qs, 10Ks, 8Ks, etc. for a specific year. 

This script will create a folder that will store text files for each day of the year in which 
a report was filed. Each file contains the following information about each report filed:
CIK|Company Name|Form Type|Date Filed|File Name.

One example:
1000045|NICHOLAS FINANCIAL INC|8-K|20190401|edgar/data/1000045/0001193125-19-093800.txt

This information allows us to name the text files accordingly. More importantly,
the last piece of information can be used to obtain the url for that report in text file
format. 

Notes: 
1. This script needs to be run before the other two.
2. The resulting database will contain information about all the reports, not simply 10Ks or 10Qs, 
for a particular year.
"""


def makeURL(base_url, comp):
    """
    Creates urls

    :param base_url: (str) consisting part of the web address. 
     In our case, https://www.sec.gov/Archives/edgar/daily-index/
    
    :param comp: (lst) a list of strings of url component.
     In our case, the year and the format we want to save
     the information in (JSON because it's the most popular
     and common one)
     
    :return: (str) a url
    """
    url = base_url
    # add each component to the base url
    for r in comp:
        url = '{}/{}'.format(url, r)
    return url

def retrieve_json(url, filename):
    """
    Returns a dictionary containing database extracted from the url and 
    also stoes it as a json file
    :param url: (str) a web address
    :param filename: (str) a filename for storing the json file database
    :return: (dict) a dictionary containing database
    """
    if os.path.exists(filename):
        print("\n {} already exists.".format(filename))
        f = open(filename, 'r')
        data_dict = json.loads(f.read())
    else:
        count = 0
        while count<10:
            encoded_content = requests.get(url)
            if encoded_content:
                data_dict = encoded_content.json()
                with open(filename, 'w') as f: 
                    json.dump(data_dict, f)
                count = 20
                print("\n {} json file downloaded.\n".format(filename))
            else:
                print("Failed download for {} json file; trying again.".format(filename))
                count += 1
        if count<20:
            sys.exit("Failed download for {} json file. Quitting. Try again later".format(filename))
    return data_dict


def get_quarterly_data(year):
    """
    Returns a dictionary with data for all quarters in a year and stores dictionaries corresponding to yearly and individual 
    quarterly databases in json file format
    :param year: (str) a year
    :param yearly_dict: (dict) a dictionary of 
     (This is obtained from the previous function)
    :return: (dict) a dictionary of filename:masterURL pairs with filename specific to the date of reports
    """     
    # First get yearly data
    year_url = makeURL(r'https://www.sec.gov/Archives/edgar/daily-index', [year, 'index.json'])
    year_filename = "yearly_database_{}".format(year)
    yearly_dict = retrieve_json(year_url, year_filename)
    print(" \n Extracted Yearly Data \n")
    """
    The yearly_dict looks like this:
    {'directory': 
        {'item':
            [{'last-modified': '03/29/2019 10:07:33 PM', 'name': 'QTR1', 'type': 'dir', 'href': 'QTR1/', 'size': '20 KB'}, 
            {'last-modified': '06/28/2019 10:06:20 PM', 'name': 'QTR2', 'type': 'dir', 'href': 'QTR2/', 'size': '20 KB'}, 
            {'last-modified': '09/30/2019 10:22:01 PM', 'name': 'QTR3', 'type': 'dir', 'href': 'QTR3/', 'size': '20 KB'}, 
            {'last-modified': '10/01/2019 12:20:09 AM', 'name': 'QTR4', 'type': 'dir', 'href': 'QTR4/', 'size': '4 KB'}],
        'name': 'daily-index/2019/', 
        'parent-dir': '../'}}
    Next, we loop through each quarter using yearly_dict['directory']['item'] and pull quarterly database. 
    """
    quarterly_dict = {}
    # Loop thru each quarter in the year
    for qrt in yearly_dict['directory']['item']:
        qrt_name = qrt['name']
        qrt_url = makeURL(r'https://www.sec.gov/Archives/edgar/daily-index', [year, qrt_name, 'index.json'])
        qrt_filename = "quarterly_database_{}_{}".format(year, qrt_name)
        qdict = retrieve_json(qrt_url, qrt_filename)
        quarterly_dict[qrt_name] = qdict
        """
        Each dictionary for a quarter called qdict looks like this:
        {'directory': 
            {'item': 
                [{'last-modified': '01/04/2021 10:07:15 PM', 
                'name': 'company.20210104.idx', 
                'type': 'file', 
                'href': 'company.20210104.idx', 
                'size': '785 KB'}, 
                {'last-modified': '01/05/2021 10:07:46 PM', 
                'name': 'company.20210105.idx', 
                'type': 'file', 
                'href': 'company.20210105.idx', 
                'size': '1244 KB'}, ....],
            'name': 'daily-index/2021/QTR1/', 
            'parent-dir': '../'}}
        In the next extract_masterURLs function, we loop through each company, 
        pull only the master URLs and  store the urls in a dictionary along with the filename. 
        """
    return quarterly_dict
            
def extract_masterURLs(quarterly_dict, year): 
    """
    Creates a dictionary of filename:masterURL pairs with filename specific to the date of reports
    :param quarterly_dict: (dict) a dictionary of quarterly database
     (This is obtained from the previous function)
    :return: (dict) a dictionary of filename:masterURL pairs with filename specific to the date of reports
    """  
    master_urls = {}
    # creates URL for each master file
    for qrt, qdict in quarterly_dict.items():
        for file in qdict['directory']['item']:
            file_url = makeURL(r'https://www.sec.gov/Archives/edgar/daily-index', [year, qrt, file['name']])
            filename = file['name']
            if 'master' in file_url:
                file_url = file_url.replace('.gz', '')
                master_urls[filename] = file_url
    return master_urls
    """
    Sample output:

    Quarter 1 Master Files:

    {'master.20210104.idx': 'https://www.sec.gov/Archives/edgar/daily-index/2021/QTR1/master.20210104.idx',
     'master.20210105.idx': 'https://www.sec.gov/Archives/edgar/daily-index/2021/QTR1/master.20210105.idx',
     ... etc }

    """


def retrieve_content(master_urls, output_directory):
    """
    Writes content of URLs onto separate text files and also creates an error database 
    for failed attempts
    :param master_urls: (dict) a dictionary of URLs
    (Obtained with the get_quarterly_data function)
    :param output_directory: (str) the name of the folder you want to save text files in
    :return: writes content to text files 
    """
    error_data = {}
    # create a folder to store output
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        
    for filename, url in master_urls.items():
        if filename+".txt" not in os.listdir(output_directory):
            # request content from URL
            content = requests.get(url).content
            if b"Request Rate Threshold Exceeded" in content:
                error_data[filename] = url
                print("{} failed retrieval.".format(filename))
            elif b"Last Data Received" in content: 
                # write content
                with open('{}{}.txt'.format(output_directory, filename), 'wb') as f:
                    # content is in bytes so we have to us 'wb' mode.
                    f.write(content)
                print("{} downloaded.".format(filename))
        else:
            print("{} already exists.".format(filename))
    print("\n Total {} files failed retrieval. \n".format(len(error_data)))           
    with open("error_database_{}".format(str(year)), 'w') as ef: 
        json.dump(error_data, ef)
    return error_data
    """
    Finally we write a function to download the general database which consists of 
    text files containing information about the reports filed (which company, CIK, 
    date, kind of report and the URL of the report) for each reporting day of a year.
    """

def download_general_database(year, output_directory):
    """
    Creates text files for given year
    :param year: (str) a year
    :param output_directory: (str) a directory to store the output e.g './general_database/'
    :return:
    """
    quarterly_dict = get_quarterly_data(year)
    print("\n Extracted Quarterly Data ")
    
    master_urls = extract_masterURLs(quarterly_dict, year)
    print("\n Extracted Master Urls \n")

    error_data = retrieve_content(master_urls, output_directory)
    
    return error_data
    
year = 2021
output_directory = './general_database_{}/'.format(str(year))
error_data = download_general_database(year, output_directory)

while error_data: 
    print(" Retrying failed retrievals \n ")
    
    error_data = retrieve_content(error_data, output_directory)
    
print("Finished Downloading Database Files")
