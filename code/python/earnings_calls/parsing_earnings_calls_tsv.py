"""
This script goes through all the parsed transcript JSON files for the years specified in
transcript_years = ['2019', '2020', '2021'] below.

From each JSON file, it determines each transcript's filename.
Then it goes through all the SpeakerTurns in the JSON file,
and outputs only the corporate SpeakerTurns to a TSV file (/data/SCRIPTS/earnings_calls_scripts/earnings_calls.tsv)
where each line corresponds to one corporate SpeakerTurn (indicated by is_corporate_participant flag being True),
and is formatted [id]\t[filename]\t[text with no newlines].

To run this script:
cd /data/SCRIPTS/earnings_calls_scripts
python3 parsing_earnings_calls_tsv.py
"""

import os
import json
import csv

def read_transcript_json_file(transcript_json_filename):
    """ takes in the JSON file for a single earnings call transcript
        returns a list of lists where each inner list corresponds to one corporate SpeakerTurn,
        containing id (which will be filename + "_p_" for presentation or "_qa_" for q&a + the index number of the speaker as noted in the transcript file),
        filename, and text
    """
    f = open(transcript_json_filename) # open JSON file
    transcript_json = json.load(f)     # load JSON into Python dictionary

    # transcript_json["filename"] will look something like /data/TRANSCRIPTS_2019/2019-Feb-12-VNO.N-139861747920-transcript.txt
    # but all we want is the filename without the path
    filename = transcript_json["filename"].split("/")[3]

    curr_transcript_corporate_turns = []
    for turn in transcript_json["presentation"]:
        # we only want corporate participant turns
        if turn["is_corporate_participant"]:
            id = filename + "_" + "p" + "_" + str(turn["index"])
            curr_corporate_turn = [id, filename, turn["text"]]
            curr_transcript_corporate_turns.append(curr_corporate_turn)

    for turn in transcript_json["questions_and_answers"]:
        # we only want corporate participant turns
        if turn["is_corporate_participant"]:
            id = filename + "_" +  "qa" + "_" + str(turn["index"])
            curr_corporate_turn = [id, filename, turn["text"]]
            curr_transcript_corporate_turns.append(curr_corporate_turn)

    return curr_transcript_corporate_turns

def write_list_of_lists_to_tsv(list_of_lists, tsv_path):
    """ takes in a list of lists, where each inner list corresponds to one corporate SpeakerTurn,
        and creates a tsv file at the path specified by tsv_path,
        with each tsv line formatted as [id]\t[filename]\t[text with no newlines]
    """
    with open(tsv_path, 'w', newline='') as tsvfile:
        tsvwriter = csv.writer(tsvfile, delimiter = '\t')
        tsvwriter.writerow(['id', 'filename', 'text'])
        for list in list_of_lists:
            tsvwriter.writerow(list)

# to run script:
# cd /data/SCRIPTS/earnings_calls_scripts
# python3 parsing_earnings_calls_tsv.py
if __name__ == "__main__":
    # go through all parsed transcript JSON files in all 3 transcript folders (ex: /data/SCRIPTS/earnings_calls_scripts/parsed_transcripts/parsed_transcripts_2021)
    # and save corporate SpeakerTurns to transcript_corporate_turns (a list of lists)
    transcript_corporate_turns = []
    transcript_years = ['2019', '2020', '2021']
    for transcript_year in transcript_years:
        transcript_json_folder = '/data/SCRIPTS/earnings_calls_scripts/parsed_transcripts/parsed_transcripts_' + transcript_year
        for transcript_json_filename in os.listdir(transcript_json_folder):
            print(transcript_json_filename)
            curr_transcript_corporate_turns = read_transcript_json_file(transcript_json_folder + '/' + transcript_json_filename)
            transcript_corporate_turns = transcript_corporate_turns + curr_transcript_corporate_turns

    # write transcript_corporate_turns list of lists to csv at /data/SCRIPTS/earnings_calls_scripts/earnings_calls.tsv
    write_list_of_lists_to_tsv(transcript_corporate_turns, '/data/SCRIPTS/earnings_calls_scripts/earnings_calls.tsv')
