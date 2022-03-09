"""
This script takes in a TSV of speaker turns, where each row corresponds to one corporate speaker turn
and is formatted [id]\t[filename]\t[text with no newlines].

It outputs an updated TSV of speaker turns (formatted [id]\t[filename]\t[text with no newlines]),
where multiword phrases (ex: "financial reporting") have been combined with underscores (ex: "financial_reporting").
To do so, we perform word tokenization on all the speaker turns in the TSV,
then use a Gensim phrase model to find words that occur unusually frequently next to each other.
Then, we run that model over the tokenized speaker turns in order to combine multiword phrases.

Along the way, this script also outputs a tokenized version of the original TSV,
as well as a pickled version of the Gensim phrase model.

To run this script:
cd /data/SCRIPTS/earnings_calls_scripts
python3 combine_multiword_phrases_tsv.py
"""

import csv

from gensim.utils import simple_preprocess
from gensim.models.phrases import Phrases, ENGLISH_CONNECTOR_WORDS

def read_tsv_and_tokenize_to_list_of_lists(tsv_path):
    """ takes tsv_path (the path to a TSV file of speaker turns, where each row corresponds to one speaker turn
        and is formatted [id]\t[filename]\t[text with no newlines])

        returns tokenized_tsv_rows (a list of lists, where each inner list corresponds to one row of the tsv,
        and the text element (element at index 2) of tokenized_tsv_rows is a list of all the tokens for that speaker turn)
        and speaker_sentences (a list of lists of all the speaker turns in the tsv file - each inner list is a list of tokens in one speaker turn)
    """
    tokenized_tsv_rows = []
    speaker_sentences = []
    with open(tsv_path, 'r', newline='') as tsvfile:
        reader = csv.reader(tsvfile, delimiter = '\t')
        for row in reader:
            curr_id = row[0]
            curr_filename = row[1]
            print("read_tsv_and_tokenize_to_list_of_lists", curr_filename)

            curr_speaker_text = row[2]

            # to obtain curr_speaker_text_tokenized (a list of tokens in the current speaker turn),
            # use gensim's simple_preprocess to perform word tokenization on the speaker turn
            curr_speaker_text_tokenized = simple_preprocess(curr_speaker_text)
            tokenized_tsv_rows.append([curr_id, curr_filename, curr_speaker_text_tokenized])

            speaker_sentences.append(curr_speaker_text_tokenized)

    return tokenized_tsv_rows, speaker_sentences

def combine_multiword_phrases(tokenized_tsv_rows, phrase_model):
    """ takes in tokenized_tsv_rows (a list of lists, where each inner list contains three elements: speaker turn id, filename,
        list of tokens in the speaker turn),
        as well as a Gensim phrase model

        returns an updated list of lists where each inner still has those three elements
        but speaker turn list of lists is now a string where the multiword phrases are combined with underscores
    """
    updated_tsv_rows = []
    for row in tokenized_tsv_rows:
        curr_id = row[0]
        curr_filename = row[1]
        print("combine_multiword_phrases", curr_filename)
        curr_speaker_tokens = row[2]

        # use passed-in Gensim phrase model to combine multiword phrases in current speaker turn
        tokens_multiword_phrases = phrase_model[curr_speaker_tokens]

        # convert from list of tokens back to a single string
        multiword_phrases_str = " ".join(tokens_multiword_phrases)

        updated_tsv_rows.append([curr_id, curr_filename, multiword_phrases_str])

    return updated_tsv_rows

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
# python3 combine_multiword_phrases_tsv.py
if __name__ == "__main__":
    # Read rows of a TSV of corporate speaker turns (formatted [id]\t[filename]\t[text with no newlines]).
    
    # tokenized_tsv_rows: Perform sentence segmentation and word tokenization on each TSV row's speaker text to turn it into a list of lists,
    # with each inner list being a list of tokens in a single sentence.

    # sentences: A list of lists of just the speaker turn text. Each inner list will be a list of tokens in a single sentence.
    tokenized_tsv_rows, sentences = read_tsv_and_tokenize_to_list_of_lists('/data/SCRIPTS/earnings_calls_scripts/earnings_calls.tsv')
    
    # Save a version of the TSV with tokenized speaker turns.
    write_list_of_lists_to_tsv(tokenized_tsv_rows, '/data/SCRIPTS/earnings_calls_scripts/earnings_calls_tokenized.tsv')

    # Train a Gensim phrase model on all the speaker sentences from the TSV.
    phrase_model = Phrases(sentences, min_count=15, threshold=10, connector_words=ENGLISH_CONNECTOR_WORDS)

    # Export the trained Gensim phrase model = use less RAM, faster processing. Model updates no longer possible.
    frozen_model = phrase_model.freeze()

    # Save Gensim phrase model.
    frozen_model.save("earnings_calls_phrase_model.pkl")

    # Load Gensim phrase model.
    # phrase_model_reloaded = Phrases.load("earnings_calls_phrase_model.pkl")

    # Combine multi-word phrases by applying trained Gensim phrase model to each speaker turn.
    tsv_rows_multiword_phrases = combine_multiword_phrases(tokenized_tsv_rows, phrase_model)

    # Write speaker turns with multiword phrases combined to TSV at /data/SCRIPTS/earnings_calls_scripts/earnings_calls_multiword_phrases.tsv.
    write_list_of_lists_to_tsv(tsv_rows_multiword_phrases, '/data/SCRIPTS/earnings_calls_scripts/earnings_calls_multiword_phrases.tsv')
