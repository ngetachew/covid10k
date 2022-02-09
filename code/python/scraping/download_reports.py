import requests
import os
import json 
"""
Written by Aashita Kesarwani

FINAL DOWNLOAD for a specific kind of reports such as 10Ks for a particular year. 
"""


def download_reports(data, output_directory, error_filename):
    """
    Downloads all the 10Ks based on the input data and returns the dictionary for failed retrievals
    :param directory: (str) output directory (e.g ./10K_reports/)
    :param data: (lst) a dictionary with key:value pairs consisting of filename:url for download
    :param error_filename: (str) filename for storing dictionary with filename:url for reports that 
    could not be retrieved in json format
    :return: (dict) a dictionary with key:value pair consisting of filename:url for reports that could not be retrieved
    """
    try: 
        f = open(data, 'r')
        data = json.loads(f.read())
        error_data = {}
        count = 0

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        try: 
            for filename, doc_url in data.items():
                path = '{}{}'.format(output_directory, filename)
                count += 1
                if filename not in os.listdir(output_directory):
                    content = requests.get(doc_url).content
                    if b"ACCESSION NUMBER" in content:
                        with open(path, 'wb') as f:
                            f.write(content)
                            print("Count {}: {} written.".format(count, filename))
                    elif b"Request Rate Threshold Exceeded" in content:
                        error_data[filename] = doc_url
                        print("Count {}: {} failed retrieval.".format(count, filename))
                    else:
                        print("Count {}: Something weird just happened while retrieving the content for {} with url {}.".format(count, filename, doc_url)) 

            with open(error_filename, 'w') as ef: 
                json.dump(error_data, ef)
                return error_data
            print("Completed a round of attempting to download the reports!")
            
        except KeyboardInterrupt:
            print("Downloading interrupted.")
            if len(error_data)>0:
                print("Run the script again without deleting any files/folders and it will pick up from where it left.")
                with open(error_filename, 'w') as ef: 
                    json.dump(error_data, ef)
                return error_data
    except OSError:
        print("Json data file with relevant information about downloading the reports does not exist. Please check: Have you run the create_report_data.py before this? Are you sure you did not delete the reportdata json files created by running the above script? Are you right in the right directory where the reportdata json files are stored?".format(data))
    """
    Sample text file name: 1619096-10-Q-202006.txt.
    The CIK number is a 10 digit code, but the information given to us removes the
    leading zeros. If we need the leading zeros, below is a function that can add them
    to the text file names.

    Now we have all reports in text file formats stored in the directory that we created.
    """

form_id = '10-K' 
year = 2021
output_directory = "./{}_{}/".format(form_id, year)
error_filename = "error_reports_{}_{}".format(form_id, year)

# For downloading the files that could not be retrieved in earlier attempt(s) stored in error_data json dump,
# please change the value for data variable as below.
# data = "error_reports_{}_{}".format(form_id, year)  #Please comment data = "reportdata_{}_{}".format(form_id, year) line
data = "reportdata_{}_{}".format(form_id, year)

error_data = download_reports(data, output_directory, error_filename)

while error_data: 
    print(" Retrying failed retrievals \n ")
    error_data = download_reports("error_reports_{}_{}".format(form_id, year), output_directory, error_filename)

