import os
import json

"""
Written by Aashita Kesarwani

REPORT DATA that will be used to download a specific kind of report such as 10Ks.
This script will not try to retrive any information from the SEC website. It will only 
extract the information from the GENERAL DATABASE relevant to a particular kind of 
report and return a simple dictionary with key:value pairs consisting of filename:url 
for downloading those reports. 
Notes:
1. You need to run download_general_database.py script before running this.
2. You need to run this script before running download_reports.py.
3. Unlike the other two scripts, this will not fail because of the blocking by 
sec.gov website and will need to run only once so as not to repeat the process.

"""

def create_report_data(form_id, year, database_directory):
    """
    Returns a a dictionary with key:value pair consisting of filename:url and also stores it in json format
    :param form_id: (str) desired form e.g. '10-K'
    :param year: (int) desired form e.g. 2021
    :param directory: (str) directory where intermediate database files are saved
    Ideally in this format: ./dir_name/
    :return: (dict) a dictionary with key:value pairs consisting of filename:url for downloading reports
    """
    try:
        if os.path.exists(database_directory):
            list_of_data = []
            list_of_byte_data = []
            list_of_data_formats = []
            report_data = {}

            # we read every text file and append its content (which is in byte format) onto a list 
            for filename in os.listdir(database_directory):
                if filename.endswith('.txt'): 
                    with open(os.path.join(database_directory, filename), 'rb') as f:
                        byte_data = f.read()
                        list_of_byte_data.append(byte_data)


            # decodes byte data and appends to a new list
            for byte_data in list_of_byte_data:
                data = byte_data.decode('utf-8', errors='ignore').split('--')
                list_of_data.append(data)


            # next, we need to remove the headers since we don't need them     
            for data_instance in list_of_data:
                for index, item in enumerate(data_instance):
                    if "ftp://ftp.sec.gov/edgar/" in item:
                        start_ind = index
                        data_format = data_instance[start_ind + 1:]
                        list_of_data_formats.append(data_format)

            # we need to break the data into sections so we can work with it easier
            for frmt in list_of_data_formats:
                for index, item in enumerate(frmt):
                    if len(item) > 0:
                        clean_item_data = item.replace('\n', '|').split('|')
                        if index == 0:
                            clean_item_data = clean_item_data[8:]


                        for index, row in enumerate(clean_item_data):
                            if '.txt' in row:
                                mini_list = clean_item_data[(index - 4): index + 1]
                                if len(mini_list) != 0:
                                    if mini_list[2] == form_id: ## Added this conditional to filter only required forms
                                        # we need to add this to the URL to get the text file
                                        doc_url = "https://www.sec.gov/Archives/" + mini_list[4]
                                        cik_number = mini_list[0]
                                        date = mini_list[3] 
                                        filename = '{}-{}-{}.txt'.format(cik_number, form_id, date)
                                        report_data[filename] = doc_url
                                        
            with open("reportdata_{}_{}".format(form_id, year), 'w') as f: 
                json.dump(report_data, f)                       
            return report_data
        
    except OSError:
        print('Error: Database directory does not exist. ' + directory)

form_id = '10-K' 
year = 2021
database_directory = './general_database_{}/'.format(year)
report_data = create_report_data(form_id, year, database_directory)
print("The filename and urls for {} {} reports for the year {} are saved as dictionaries in json format in reportdata_{}_{}.".format(len(report_data), form_id, year, form_id, year))
