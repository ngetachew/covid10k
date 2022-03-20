"""
This script takes in a file about the topic composition of documents, generated from a MALLET topic model with the --output-topic-docs flag.
Basically, the input file is a txt file of documents (which are speaker turns in the case of earnings calls),
where each txt file line corresponds to one document, and is formatted:
[document number]\t[document id]\t[tab-separated numbers corresponding to the composition of each topic that the document represents]

It outputs a CSV file of the top documents for each topic (the documents that contribute to the highest proportions of that topic),
making sure that each company is only represented at most once for each topic.
The output CSV file is formatted:
[topic number corresponding to topics in topic keys file generated with MALLET's --output-topic-keys flag],[document id],[document text]
For COVID earnings calls, the document ids are formatted:
[filename][_p_ for presentation or _qa_ for q&a][the index number of the speaker as noted in the transcript file].

To run this script:
python3 find_top_documents_from_doctopics.py output_3_9_22/covid_earnings_calls_3_9_22_pruned-50-9.doctopics.txt 50 10
for 50 topics and 10 top documents per topic
"""
import sys
import heapq
import csv

def create_doc_proportions_tuple_list(doctopics_lines, topic_num):
    """ takes in a list of lists representing the lines from a MALLET doctopics file generated with the --output-topic-docs flag,
        as well as the current topic number,
        and returns a list of (-1 * document proportion for the topic, document id) tuples for all documents
    """
    # create list of tuples where each tuple corresponds to one document
    # and is formatted (-1 * document proportion, document id)
    topic_doc_proportions = []
    for i in range(0, len(doctopics_lines)):
        doc_id = doctopics_lines[i][1]
        doc_proportion = float(doctopics_lines[i][topic_num + 2])

        # the heapq heap is a min heap by default
        # so we want to multiply doc_proportion by -1 to make it a max heap
        topic_doc_proportions.append((-1 * doc_proportion, doc_id))
    return topic_doc_proportions

def get_top_doc_ids(num_top_docs, topic_doc_proportions_heap):
    """ takes in num_top_docs to find,
        and a heap of (-1 * document topic proportion, document id) tuples for one topic,
        and returns a list of the document ids of the num_top_docs top documents for that topic
    """
    # while we haven't yet gotten num_top_docs top documents for the current topic,
    # pop document with the current highest proportion off the heap,
    # making sure to only include each company at most once per topic
    top_doc_ids = []
    companies_seen = set()
    while topic_doc_proportions_heap and len(top_doc_ids) < num_top_docs:
        top_doc_tuple = heapq.heappop(topic_doc_proportions_heap)
        top_doc_id = top_doc_tuple[1]
        company_ticker = top_doc_id.split("-")[3].split(".")[0]
        if company_ticker not in companies_seen:
            top_doc_ids.append(top_doc_id)
            companies_seen.add(company_ticker)
    return top_doc_ids

def find_document_text(top_doc_ids, top_doc_list_of_lists, tsv_path):
    """ takes in a list of the ids for the num_top_docs top documents for a topic,
                 a list of [topic number, document id, document text] lists for all the topics,
                 and the path to a TSV file where the document text can be found (with each line formatted [document id]\t[filename]\t[document text])
        returns an updated version of the list of [topic number, document id, document text] lists for all the topics
    """
    # find document text for top documents from TSV file by matching on doc_id and TSV's id column
    # update top_doc_list_of_lists (a list of [topic number, document id, document text] lists),
    # ordered primarily from topic 0 to topic (num_topics - 1) and secondarily from documents with highest proportion to documents with lowest proportion for each topic
    for top_doc_id in top_doc_ids:
        tsv_file = open(tsv_path, 'r') 
        tsv_rows = csv.reader(tsv_file, delimiter='\t') 
        for row in tsv_rows:
            tsv_doc_id = row[0]           # id is in first column of TSV
            if tsv_doc_id == top_doc_id:
                doc_text = row[2]         # text is in third column of TSV
                top_doc_list_of_lists.append([topic_num, top_doc_id, doc_text])
                break
    return top_doc_list_of_lists

def write_list_of_lists_to_csv(list_of_lists, csv_path):
    """ takes in a list of lists, where each inner list corresponds to one document and is [topic number, document id, document text],
        and creates a csv file at the path specified by csv_path,
        with each csv line formatted as [topic number],[document id],[document text]
    """
    with open(csv_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['topic number', 'document id', 'document text'])
        for list in list_of_lists:
            csvwriter.writerow(list)

# to run script:
# python3 find_top_documents_from_doctopics.py output_3_9_22/covid_earnings_calls_3_9_22_pruned-50-9.doctopics.txt 50 10
# for 50 topics and 10 top documents per topic
if __name__ == "__main__":
    doctopics_filename = sys.argv[1]
    num_topics = int(sys.argv[2])
    num_top_docs = int(sys.argv[3])

    # read doctopics.txt lines into list of lists
    with open(doctopics_filename) as f:
        doctopics_lines = [line.split("\t") for line in f]
    
    # create a list of top documents (ordered from highest to lowest proportion for each topic) for all topics
    # each inner list represents one document and is [topic number, document id, document text]
    top_doc_list_of_lists = []

    # for each topic...
    for topic_num in range(0, num_topics):
        # create list of tuples where each tuple corresponds to one document
        # and is formatted (-1 * document proportion for the topic, document id)
        # the heapq heap is a min heap by default
        # so we want to multiply document proportion by -1 to make it a max heap
        topic_doc_proportions = create_doc_proportions_tuple_list(doctopics_lines, topic_num)
        
        # convert list of tuples to heap in order to find top documents for the current topic
        heapq.heapify(topic_doc_proportions)

        # use the current topic's heap to find the num_top_docs top documents for the topic,
        # making sure to only include each company at most once per topic
        top_doc_ids = get_top_doc_ids(num_top_docs, topic_doc_proportions)

        # find document text for this topic's top documents from multiword phrases TSV file by matching on doc_id and TSV's id column
        # create list of [topic number, document id, document text] lists,
        # ordered primarily from topic 0 to topic (num_topics - 1) and secondarily from documents with highest proportion to documents with lowest proportion for each topic
        top_doc_list_of_lists = find_document_text(top_doc_ids, top_doc_list_of_lists, 'earnings_calls_multiword_phrases.tsv')

    # write top documents for all topics to csv file,
    # with each csv line formatted as [topic number],[document id],[document text]
    write_list_of_lists_to_csv(top_doc_list_of_lists, 'covid_earnings_calls_top_docs.csv')  