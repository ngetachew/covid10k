"""
This script goes through all the parsed transcript JSON files for the years specified in
transcript_years = ['2019', '2020', '2021'] below.

It determines each transcript's filename, ticker (i.e. ULTA.OQ), company, date, quarter, half-year, year, and whether corporate_participants_read_questions.
And writes that company metadata to a CSV file (/data/SCRIPTS/earnings_calls_scripts/earnings_calls_metadata.csv)
where each line corresponds to one earnings call transcript for one company.

To run this script:
cd /data/SCRIPTS/earnings_calls_scripts
python3 parsing_earnings_calls_metadata.py
"""

import os
import json
import csv

def read_transcript_json_file(transcript_json_filename):
    """ takes in the JSON file for a single earnings call transcript
        returns a list of the filename, ticker, company, date, quarter, half_year, year, whether corporate_participants_read_questions for that transcript
    """
    f = open(transcript_json_filename) # open JSON file
    transcript_json = json.load(f)     # load JSON into Python dictionary

    # transcript_json["filename"] will look something like /data/TRANSCRIPTS_2019/2019-Feb-12-VNO.N-139861747920-transcript.txt
    # but all we want is the filename without the path
    filename = transcript_json["filename"].split("/")[3]
    ticker = filename.split("-")[3]
    company = transcript_json["company"]
    date = transcript_json["date"]
    if transcript_json["quarter"]:
        quarter = transcript_json["quarter"]
    else:
        quarter = ""

    if transcript_json["half-year"]:
        half_year = transcript_json["half-year"]
    else:
        half_year = ""
    
    if transcript_json["year"]:
        year = transcript_json["year"]
    else:
        year = ""
    corporate_participants_read_questions = transcript_json["corporate_participants_read_questions"]
    return [filename, ticker, company, date, quarter, half_year, year, corporate_participants_read_questions]

def write_list_of_lists_to_csv(list_of_lists, csv_path):
    """ takes in a list of lists, where each inner list represents the metadata for one earnings call
        and creates a csv file called at the path specified by csv_path with one line for each earnings call,
        formatted as filename, ticker, company, date, quarter, half-year, year, whether corporate_participants_read_questions
    """
    with open(csv_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter = ',')
        csvwriter.writerow(['Filename', 'Ticker', 'Company', 'Date', 'Quarter', 'Half-Year', 'Year', 'Corporate Participants Read Questions'])
        for list in list_of_lists:
            csvwriter.writerow(list)

# to run script:
# cd /data/SCRIPTS/earnings_calls_scripts
# python3 parsing_earnings_calls_metadata.py
if __name__ == "__main__":
    # go through all parsed transcript JSON files in all 3 transcript folders (ex: /data/SCRIPTS/earnings_calls_scripts/parsed_transcripts/parsed_transcripts_2021)
    # and save company metadata to transcript_metadata_lists (a list of lists)
    transcript_metadata_lists = []
    transcript_years = ['2019', '2020', '2021']
    for transcript_year in transcript_years:
        transcript_json_folder = '/data/SCRIPTS/earnings_calls_scripts/parsed_transcripts/parsed_transcripts_' + transcript_year
        for transcript_json_filename in os.listdir(transcript_json_folder):
            print(transcript_json_filename)
            company_info = read_transcript_json_file(transcript_json_folder + '/' + transcript_json_filename)
            transcript_metadata_lists.append(company_info)

    # write transcript_metadata_lists list of lists to csv at /data/SCRIPTS/earnings_calls_scripts/earnings_calls_metadata.csv
    write_list_of_lists_to_csv(transcript_metadata_lists, '/data/SCRIPTS/earnings_calls_scripts/earnings_calls_metadata.csv')