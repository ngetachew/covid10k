"""
This script takes in a TSV of speaker turns, where each row corresponds to one corporate speaker turn
and is formatted [id]\t[filename]\t[text tokens].

It outputs an updated TSV of filtered speaker turns (formatted [id]\t[filename]\t[text tokens]),
where the remaining speaker turns are just the ones that contain COVID lexicon words types.

To run this script:
cd /data/SCRIPTS/earnings_calls_scripts
python3 filter_tsv_for_covid_speaker_turns.py
"""

import csv
from collections import defaultdict

def read_tsv_to_list_of_lists(tsv_path):
    """ takes tsv_path (the path to a TSV file of speaker turns, where each row corresponds to one speaker turn
        and is formatted [id]\t[filename]\t[text with no newlines])

        returns tsv_rows (a list of lists, where each inner list corresponds to one row of the tsv)
    """
    tsv_rows = []
    with open(tsv_path, 'r', newline='') as tsvfile:
        reader = csv.reader(tsvfile, delimiter = '\t')
        for row in reader:
            curr_id = row[0]
            curr_filename = row[1]
            curr_speaker_text = row[2]

            tsv_rows.append([curr_id, curr_filename, curr_speaker_text])

            # print statement to display progress
            print("read_tsv_to_list_of_lists", curr_filename)

    return tsv_rows

def filter_for_covid_speaker_turns(tsv_rows, covid_lexicon):
    """ takes in tsv_rows (a list of lists, where each inner list contains three elements: speaker turn id, filename,
        list of tokens in the speaker turn),
        as well as a list of word types in a COVID lexicon

        returns an updated list of lists where only speaker turns that contain 1+ token(s) in the COVID lexicon are retained
    """
    updated_tsv_rows = []

    # Use a dictionary to count how many times we see each COVID word type as a check that this script is identifying COVID speaker turns correctly.
    covid_word_types_seen = defaultdict(int)

    for row in tsv_rows:
        curr_id = row[0]
        curr_filename = row[1]
        curr_speaker_text = row[2]

        # curr_speaker_text string has tokens (including multiword phrase tokens) separated by spaces
        # Create curr_speaker_tokens list of tokens from curr_speaker_text string.
        curr_speaker_tokens = curr_speaker_text.split()

        # Check if current speaker turn is a COVID speaker turn.
        # For every token in the speaker turn text (where a token might be a multiword phrase combined by underscores)...
        for token in curr_speaker_tokens:
            # For every word type in COVID lexicon, check if that COVID word type is part of any token in the current speaker turns.
            # We do this instead of checking directly for equality (between the COVID word type and the speaker turn token)
            # because combining multiword phrases may have made it so that some COVID words were combined into multiword phrases with underscores,
            # so they won't appear in the speaker tokens exactly how they do in the lexicon.
            is_covid_speaker_turn = False # assume current speaker turn is not COVID speaker turn to begin with
            for covid_word_type in covid_lexicon:
                if covid_word_type in token:
                    print("token:", token)
                    is_covid_speaker_turn = True
                    covid_word_types_seen[covid_word_type] += 1
                    break # just need to see one COVID word type for this to be considered a COVID speaker turn
            
            if is_covid_speaker_turn:
                # Use curr_speaker_text, not curr_speaker_tokens here, so that the speaker turn text will be a complete string, not a list of token strings, in the output TSV file.
                updated_tsv_rows.append([curr_id, curr_filename, curr_speaker_text])
    
        # print statement to display progress
        print("filter_for_covid_speaker_turns", curr_filename)
    
    return updated_tsv_rows, covid_word_types_seen

def write_list_of_lists_to_tsv(list_of_lists, tsv_path):
    """ takes in a list of lists, where each inner list corresponds to one corporate speaker turn,
        and creates a tsv file at the path specified by tsv_path,
        with each tsv line formatted as [id]\t[filename]\t[text with no newlines]
    """
    with open(tsv_path, 'w', newline='') as tsvfile:
        tsvwriter = csv.writer(tsvfile, delimiter = '\t')
        for list in list_of_lists:
            tsvwriter.writerow(list)

# to run script:
# cd /data/SCRIPTS/earnings_calls_scripts
# python3 filter_tsv_for_covid_speaker_turns.py
if __name__ == "__main__":
    # Read rows of a TSV of corporate speaker turns with multiword phrases combined with underscores (formatted [id]\t[filename]\t[text tokens]) into a list of lists.
    tsv_rows = read_tsv_to_list_of_lists('/data/SCRIPTS/earnings_calls_scripts/earnings_calls_multiword_phrases.tsv')
    
    # COVID lexicon word types.
    # Each speaker turn we retain should contain at least one of these types.
    covid_lexicon = ["coronavirus", "epidemic", "pandemicthe", "corona", "pandemicon", "pandemic", "pandemicin", "covid-19the", "covid-19in", "covid-19on", "contentscovid-19", "covid-19", "cov-2", "sars-cov-2", "covid19", "definitioncovid-19", "epidemics", "covid", "pandemics", "pre-pandemic", "coronaviruses", "pandemic-related", "pre-covid", "covid-related"]

    # Filter the TSV rows for COVID speaker turns.
    covid_tsv_rows, covid_word_types_seen_dict = filter_for_covid_speaker_turns(tsv_rows, covid_lexicon)
    # As a check on our filtering, print dictionary to count how many times each COVID word type has been seen.
    print()
    print(len(covid_word_types_seen_dict), "COVID word types seen")
    print(covid_word_types_seen_dict)
    print()

    print("number of speaker turns in TSV of only core COVID corporate speaker turns: ", len(covid_tsv_rows))
    print("number of speaker turns in TSV of all corporate speaker turns: ", len(tsv_rows))
    print("% of speaker turns retained after filtering for COVID words: ", len(covid_tsv_rows) / len(tsv_rows))

    # Save a version of the TSV with only the COVID speaker turns.
    write_list_of_lists_to_tsv(covid_tsv_rows, '/data/SCRIPTS/earnings_calls_scripts/earnings_calls_multiword_phrases_core_covid_speaker_turns.tsv')
