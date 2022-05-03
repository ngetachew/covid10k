"""
This script takes in a gz file containing the output state from a MALLET topic model,
where each row corresponds to one word type instance and is formatted [doc] [source] [pos] [typeindex] [type] [topic].
The gz file has one row for each word token in each document (which are speaker turns in the case of COVID earnings calls).

Also takes in a doctopics.txt file containing info about the topic composition of documents, generated from a MALLET topic model with the --output-topic-docs flag,
where each row corresponds to one document, and is formatted:
[document number]\t[document id]\t[tab-separated numbers corresponding to the composition of each topic that the document represents]

It outputs a CSV with one row for each word type for each topic, ordered primarily by topic numbers, and then secondarily with the most frequent word types first
(formatted [topic number],[word type],[word typeindex],[word position],[number of occurrences of word type in topic],[document numbers with word type],[document ids with word type],[number of tokens in topic]).

To run this script:
python3 sentiment_per_topic.py
"""

import gzip
import csv
from collections import OrderedDict

def gzip_file_to_list_of_lists(gz_path):
    """ Takes gz_path (the path to a gz file containing the output state from a MALLET topic model,
        where each row corresponds to one word type instance and is formatted [doc] [source] [pos] [typeindex] [type] [topic]).
        The gz file has one row for each word token in each document (which are speaker turns in the case of COVID earnings calls).

        Returns gz_rows (a list of lists, where each inner list corresponds to one row of the tsv).
    """
    gz_rows = []
    with gzip.open(gz_path, 'rt') as gzfile:
        for row in gzfile:
            if row[0] != "#":      # skip the first 3 rows of gz file (which all start with "#")
                doc, source, pos, typeindex, type, topic = row.split(" ")
                doc = int(doc)
                pos = int(pos)
                typeindex = int(typeindex)
                topic = int(topic.rstrip('\n'))
                gz_rows.append([doc, source, pos, typeindex, type, topic])

                # print statement to display progress
                print("gzip_file_to_list_of_lists doc", doc, "topic", topic)

    return gz_rows

def create_doc_nums_to_doc_ids_dict(doctopics_path):
    """ Takes doctopics_path (the path to a doctopics.txt file containing info about the topic composition of documents,
        generated from a MALLET topic model with the --output-topic-docs flag),
        where each row corresponds to one document and is formatted [document number]\t[document id]\t[tab-separated numbers corresponding to the composition of each topic that the document represents].

        Returns a dictionary mapping document numbers to their corresponding document ids.
    """
    doc_num_to_id_dict = {}

    # Read doctopics.txt lines into list of lists
    with open(doctopics_path) as f:
        doctopics_lines = [line.split("\t") for line in f]
    
    # Create mapping from document numbers to corresponding document ids
    for line in doctopics_lines:
        doc_num = int(line[0])
        doc_id = line[1]
        doc_num_to_id_dict[doc_num] = doc_id

    return doc_num_to_id_dict

def count_topic_words(gz_rows, doc_num_to_id_dict):
    """ Takes in gz_rows (a list of lists, where each inner list contains six elements: doc, source, pos, typeindex, type, topic,
                          with one inner list for each word token in each document),
        and doc_num_to_id_dict (a dictionary mapping document numbers to their corresponding document ids).

        Returns a nested ordered dictionary where the outer dictionary has keys of topic number
        and values of inner ordered dictionary with keys of word type to values of
        [word typeindex, word position, number of occurrences of word type in topic, list of document numbers with word type, list of document ids with word type, number of tokens in topic] list.
    """
    # Use a dictionary to count how many times each word type appears in each topic.
    # Will be a nested dictionary where the outer dictionary has keys of topic number
    # and values of inner dictionary with keys of word type to values of
    # [word typeindex, word position, number of occurrences of word type in topic, list of document numbers with word type, list of document ids with word type, number of tokens in topic] list.
    topic_to_word_counts_dict = {}

    for row in gz_rows:
        doc, source, pos, typeindex, type, topic = row

        if topic not in topic_to_word_counts_dict:
            topic_to_word_counts_dict[topic] = {}
        
        if type not in topic_to_word_counts_dict[topic]:
            # Initialize topic_to_word_counts_dict[topic][type] value to [word typeindex, word position, number of occurrences of the type in the topic, set of document numbers with instances of the type]
            topic_to_word_counts_dict[topic][type] = [typeindex, pos, 0, set()]
        
        num_occurrences = topic_to_word_counts_dict[topic][type][2]
        num_occurrences += 1
        doc_nums_set = topic_to_word_counts_dict[topic][type][3]
        doc_nums_set.add(doc)
        topic_to_word_counts_dict[topic][type] = [typeindex, pos, num_occurrences, doc_nums_set]

        # print statement to display progress
        print("count_topic_words doc", doc, "topic", topic)
    
    # For each word type in each topic, sort the document numbers where that type appears for that topic.
    # Also find the document ids corresponding to the document numbers.
    for topic in topic_to_word_counts_dict:
        for type in topic_to_word_counts_dict[topic]:
            # Sort document numbers
            typeindex, pos, num_occurrences, doc_nums_set = topic_to_word_counts_dict[topic][type]
            doc_nums_list_sorted = sorted(list(doc_nums_set))
        
            # Find document ids corresponding to document numbers
            doc_ids_list = []
            for doc_num in doc_nums_list_sorted:
                doc_ids_list.append(doc_num_to_id_dict[doc_num])            

            topic_to_word_counts_dict[topic][type] = [typeindex, pos, num_occurrences, doc_nums_list_sorted, doc_ids_list]

    # Compute total number of tokens in each topic by summing up number of occurrences columns for each topic.
    # Append number of tokens in topic to inner dictionary list value.
    for topic in topic_to_word_counts_dict:
        # Compute total number of tokens in each topic by summing up number of occurrences columns for each topic
        num_tokens_in_topic = 0
        for type in topic_to_word_counts_dict[topic]:
            typeindex, pos, num_occurrences, doc_nums_list, doc_ids_list = topic_to_word_counts_dict[topic][type]
            num_tokens_in_topic += num_occurrences
            
        # Append number of tokens in topic to inner dictionary list value
        for type in topic_to_word_counts_dict[topic]:
            topic_to_word_counts_dict[topic][type] = topic_to_word_counts_dict[topic][type] + [num_tokens_in_topic]

    for topic in topic_to_word_counts_dict:
        # Sort inner dictionary of word types by number of occurrences, descending (which is element at index 2 in the list that is the topic_to_word_counts_dict[topic][type] value).
        topic_to_word_counts_dict[topic] = OrderedDict(sorted(topic_to_word_counts_dict[topic].items(), key=lambda t: t[1][2], reverse=True))

    # Sort outer dictionary by key (which is topic number).
    ordered_topic_to_word_counts_dict = OrderedDict(sorted(topic_to_word_counts_dict.items(), key=lambda t: t[0]))

    return ordered_topic_to_word_counts_dict

def convert_topic_type_dict_to_list_of_lists(topic_type_dict):
    """ Takes in a nested dictionary where the outer dictionary has keys of topic number
        and values of inner dictionary with keys of word type to values of
        [word typeindex, word position, number of occurrences of word type in topic, list of document numbers with word type, list of document ids with word type, number of tokens in topic] list.

        Returns that nested dictionary as a list of lists where there is one inner list for each word type for each topic,
        with the inner list formatted like [topic, type, typeindex, pos, count, doc_nums, doc_ids, num_tokens_in_topic].
    """
    topic_type_list_of_lists = []
    for topic in topic_type_dict:
        for type in topic_type_dict[topic]:
            typeindex, pos, count, doc_nums, doc_ids, num_tokens_in_topic = topic_type_dict[topic][type]
            topic_type_list_of_lists.append([topic, type, typeindex, pos, count, doc_nums, doc_ids, num_tokens_in_topic])
    return topic_type_list_of_lists

def write_list_of_lists_to_csv(list_of_lists, csv_path):
    """ Takes in a list of lists, where each inner list corresponds to one word type in one topic
        and is [topic number, word type, word typeindex, word position, number of occurrences of word type in topic, document numbers with word type, document ids with word type, number of tokens in topic].

        Creates a csv file at the path specified by csv_path,
        with each csv line formatted as [topic number],[word type],[word typeindex],[word position],[number of occurrences of word type in topic],[document numbers with word type],[document ids with word type],[number of tokens in topic].
    """
    with open(csv_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['topic number', 'word type', 'word typeindex', 'word position', 'number of occurrences of word type in topic', 'document numbers with word type', 'document ids with word type', 'number of tokens in topic'])
        for list in list_of_lists:
            csvwriter.writerow(list)

# to run script:
# python3 sentiment_per_topic.py
if __name__ == "__main__":
    # Read rows of a gz file containing the output state from a MALLET topic model (formatted [doc] [source] [pos] [typeindex] [type] [topic]) into a list of lists.
    # The gz file has one row for each word token in each document (which are speaker turns in the case of COVID earnings calls).
    gz_rows = gzip_file_to_list_of_lists("output_5_3_22/covid_earnings_calls_core_covid_only_no_duplicates_5_3_22_pruned-50-9.gz")
    
    # Use doctopics.txt file containing info about the topic composition of documents, generated from a MALLET topic model with the --output-topic-docs flag
    # (formatted [document number]\t[document id]\t[tab-separated numbers corresponding to the composition of each topic that the document represents]),
    # to obtain a dictionary mapping document numbers to their corresponding document ids.
    doc_num_to_id_dict = create_doc_nums_to_doc_ids_dict("output_5_3_22/covid_earnings_calls_core_covid_only_no_duplicates_5_3_22_pruned-50-9.doctopics.txt")

    # Use the topic model output state gz file rows and the document number to document id dictionary to create a nested ordered dictionary
    # where the outer dictionary has keys of topic number and values of inner ordered dictionary with keys of word type to
    # values of [word typeindex, word position, number of occurrences of word type in topic, list of document numbers with word type, list of document ids with word type, number of tokens in topic] list.
    topic_type_dict = count_topic_words(gz_rows, doc_num_to_id_dict)

    # Convert topic_type_dict to list of lists where each inner list is formatted like [topic, type, typeindex, pos, count, doc_nums, doc_ids, num_tokens_in_topic].
    topic_type_list_of_lists = convert_topic_type_dict_to_list_of_lists(topic_type_dict)

    # Write each inner list of topic_type_list_of_lists as one CSV row.
    write_list_of_lists_to_csv(topic_type_list_of_lists, "sentiment_per_topic_5_3_22.csv")