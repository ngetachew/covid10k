"""
This script takes in a TSV file of corporate speaker turns containing core COVID word(s) (e.g. earnings_calls_core_covid_speaker_turns_no_duplicates.tsv),
formatted [doc id] [filename] [speaker turn text], with one row for each speaker turn.
Here, we consider one document to be one speaker turn.

Also takes in a CSV file that is a master dictionary for the Loughran-McDonald financial sentiment lexicon (e.g. Loughran-McDonald_MasterDictionary_1993-2021.csv).

Also takes in a CSV of earnings call transcript metadata that has been merged with Compustat data (e.g. earnings_call_10KQ_metadata_linked_5-16-22.csv).

It outputs a CSV counting tokens for each Loughran-McDonald sentiment category, with one row for each document (each speaker turn),
formatted [document id, transcript filename, document text, token count, negative, positive, uncertainty, litigious, strong_modal, weak_modal, constraining].

Also plots and saves the Loughran-McDonald sentiment categories as stacked barcharts over time, and also over sector.

To run this script:
Enter econtext virtual environment with matplotlib installed 
python3 loughran_mcdonald_sentiment_csv_plots.py
"""

import csv
from MOD_Load_MasterDictionary_v2022_edited import load_masterdictionary
import matplotlib.pyplot as plt

def read_tsv_to_list_of_lists(tsv_path):
    """ Takes tsv_path (the path to a TSV file of speaker turns, where each row corresponds to one speaker turn
        and is formatted [document id]\t[transcript filename]\t[document text]).

        Returns tsv_rows (a list of lists, where each inner list corresponds to one row of the TSV).
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
            print('read_tsv_to_list_of_lists', curr_filename)

    return tsv_rows

def read_csv_to_list_of_lists(csv_path):
    """ Takes csv_path (the path to a CSV file of earnings call metadata, where each row corresponds to one 10K or 10Q file.

        Returns csv_rows (a list of lists, where each inner list corresponds to one row of the CSV).
    """
    csv_rows = []
    with open(csv_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            naics_compustat = row[19]  # sector
            ect_filename = row[24]     # earnings call transcript filename
            ect_date = row[27]         # earnings call date

            if ect_filename != '':
                csv_rows.append([ect_filename, naics_compustat, ect_date])

            # print statement to display progress
            print('read_csv_to_list_of_lists', ect_filename)

    return csv_rows

def write_list_of_lists_to_csv(list_of_lists, csv_path):
    """ Takes in a list of lists, where each inner list corresponds to one speaker turn
        and is [document id, transcript filename, document text, token count, negative, positive, uncertainty, litigious, strong_modal, weak_modal, constraining].

        Creates a csv file at the path specified by csv_path,
        with each csv line formatted as [document id],[transcript filename],[document text],[token count],[negative],[positive],[uncertainty],[litigious],[strong_modal],[weak_modal],[constraining].
    """
    with open(csv_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['document id', 'transcript filename', 'document text', 'token count', 'negative', 'positive', 'uncertainty', 'litigious', 'strong_modal', 'weak_modal', 'constraining'])
        for list in list_of_lists:
            csvwriter.writerow(list)

def count_sentiment_tokens_per_document(speaker_turn_rows, loughran_mcdonald_master_dictionary):
    """ Takes speaker_turn_rows (a list of lists, where each inner list corresponds to one speaker turn
        and is formatted [document id, transcript filename, document text]).
        Also takes in loughran_mcdonald_master_dictionary, a dictionary mapping keys of uppercase word types
        to values of Loughran-McDonald MasterDictionary object (containing sentiment property (e.g. negative, uncertainty),
        which will either have a value of positive year indicating the year the word type was added to the Loughran-McDonald lexicon,
        or a value of negative year indicating the year the word type was removed from the lexicon) for that word type.

        For each document, counts the total number of tokens, as well as the number of tokens in each sentiment category.

        Returns speaker_turn_rows_with_sentiment_counts (a list of lists, where each inner list corresponds to one speaker turn
        and is formatted [document id, transcript filename, document text, token count, negative, positive, uncertainty, litigious, strong_modal, weak_modal, constraining]).
    """
    speaker_turn_rows_with_sentiment_counts = []
    for row in speaker_turn_rows:
        curr_id = row[0]
        curr_filename = row[1]
        curr_speaker_text = row[2]

        # curr_speaker_text string has tokens separated by spaces
        # Create curr_speaker_tokens list of tokens from curr_speaker_text string.
        curr_speaker_tokens = curr_speaker_text.split()

        # Variables to keep track of the token counts for each sentiment category for the current speaker turn.
        negative, positive, uncertainty, litigious, strong_modal, weak_modal, constraining = 0, 0, 0, 0, 0, 0, 0

        num_tokens = 0
        for token in curr_speaker_tokens:
            num_tokens += 1

            token_uppercased = token.upper()
            if token_uppercased in loughran_mcdonald_master_dictionary:
                token_masterdictionary_obj = loughran_mcdonald_master_dictionary[token_uppercased]
                # The sentiment words are flagged with a number indicating the year in which they were added to the list.
                # A year preceded by a negative sign indicates the year/version when the word was removed from the sentiment category.
                if token_masterdictionary_obj.negative > 0:
                    negative += 1
                if token_masterdictionary_obj.positive > 0:
                    positive += 1
                if token_masterdictionary_obj.uncertainty > 0:
                    uncertainty += 1
                if token_masterdictionary_obj.litigious > 0:
                    litigious += 1
                if token_masterdictionary_obj.strong_modal > 0:
                    strong_modal += 1
                if token_masterdictionary_obj.weak_modal > 0:
                    weak_modal += 1
                if token_masterdictionary_obj.constraining > 0:
                    constraining += 1
        
        speaker_turn_rows_with_sentiment_counts.append([curr_id, curr_filename, curr_speaker_text, num_tokens, negative, positive, uncertainty, litigious, strong_modal, weak_modal, constraining])
    
        # print statement to display progress
        print('count_sentiment_tokens_per_document', curr_filename)

    return speaker_turn_rows_with_sentiment_counts

def map_ect_filenames_to_months(earnings_call_metadata_rows):
    """ Takes earnings_call_metadata_rows (a list of lists, where each inner list corresponds to one earning calls transcript
        and is formatted [ect_filename, naics_compustat, ect_date]).

        Returns a dictionary mapping ect_filename key to month-year string value obtained from ect_date.
    """
    filename_to_month_dict = {}
    is_first_row = True
    for row in earnings_call_metadata_rows:
        # Skip first row, which is just the column headers
        if not is_first_row:
            ect_filename, naics_compustat, ect_date = row
            month_str, day_str, year_str = ect_date.split("/")
            filename_to_month_dict[ect_filename] = month_str + "-" + year_str
        is_first_row = False 

    return filename_to_month_dict

def map_ect_filenames_to_naics(earnings_call_metadata_rows):
    """ Takes earnings_call_metadata_rows (a list of lists, where each inner list corresponds to one earning calls transcript
        and is formatted [ect_filename, naics_compustat, ect_date]).

        Returns a dictionary mapping ect_filename key to integer NAICS code value indicating the company's sector.
    """
    filename_to_naics_dict = {}
    is_first_row = True
    for row in earnings_call_metadata_rows:
        # Skip first row, which is just the column headers
        if not is_first_row:
            ect_filename, naics_compustat, ect_date = row
            filename_to_naics_dict[ect_filename] = naics_compustat
        is_first_row = False

    return filename_to_naics_dict

def map_loughran_mcdonald_sentiment_to_month_to_token_count(sentiment_categories, speaker_turn_rows_with_sentiment_counts, ect_filename_to_month_dict):
    """ Takes sentiment_categories, a list of the Loughran McDonald sentiment categories.
        Also takes speaker_turn_rows_with_sentiment_counts (a list of lists, where each inner list corresponds to one speaker turn
        and is formatted [document id, transcript filename, document text, token count, negative, positive, uncertainty, litigious, strong_modal, weak_modal, constraining]).
        Also takes a dictionary mapping transcript filenames to month-year strings.

        Returns a nested dictionary, where the outer dictionary maps each Loughran McDonald sentiment category to an inner dictionary
        mapping month-year string to number of tokens in that sentiment category that were seen in that month of that year.
    """
    # Initialize inner dictionaries to empty dictionaries
    sentiment_to_month_to_token_count_dict = {}
    for sentiment in sentiment_categories:
        sentiment_to_month_to_token_count_dict[sentiment] = {}
    sentiment_to_month_to_token_count_dict['overall'] = {}

    # Initialize token count for each month for each sentiment to 0
    for key in sentiment_to_month_to_token_count_dict:
        months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
        years = ["2019", "2020", "2021"]
        month_year_str_list = []
        for year in years:
            for month in months:
                month_year_str_list.append(month + "-" + year)
        for month_year_str in month_year_str_list:
            sentiment_to_month_to_token_count_dict[key][month_year_str] = 0

    for row in speaker_turn_rows_with_sentiment_counts:
        curr_id, curr_filename, curr_speaker_text, num_tokens, negative, positive, uncertainty, litigious, strong_modal, weak_modal, constraining = row
        # Only include files for which we have Compustat metadata
        if curr_filename in ect_filename_to_month_dict:
            month_year_str = ect_filename_to_month_dict[curr_filename]

            # Keep track of number of tokens for each sentiment in this month of this year
            for sentiment in sentiment_categories:
                sentiment_to_month_to_token_count_dict[sentiment][month_year_str] += eval(sentiment) # eval makes use of the negative, positive, uncertainty, litigious, strong_modal, weak_modal, constraining variables above
        
            # Keep track of total number of tokens in this month of this year
            sentiment_to_month_to_token_count_dict['overall'][month_year_str] += num_tokens

    return sentiment_to_month_to_token_count_dict

def map_loughran_mcdonald_sentiment_to_sector_to_token_count(sentiment_categories, speaker_turn_rows_with_sentiment_counts, ect_filename_to_naics_dict):
    """ Takes sentiment_categories, a list of the Loughran McDonald sentiment categories.
        Also takes speaker_turn_rows_with_sentiment_counts (a list of lists, where each inner list corresponds to one speaker turn
        and is formatted [document id, transcript filename, document text, token count, negative, positive, uncertainty, litigious, strong_modal, weak_modal, constraining]).
        Also takes a dictionary mapping transcript filenames to NAICS codes corresponding to the companies' sectors.

        Returns a nested dictionary, where the outer dictionary maps each Loughran McDonald sentiment category to an inner dictionary
        mapping sector to number of tokens in that sentiment category that were seen for that sector.
    """
    # Initialize inner dictionaries to empty dictionaries
    sentiment_to_sector_to_token_count_dict = {}
    for sentiment in sentiment_categories:
        sentiment_to_sector_to_token_count_dict[sentiment] = {}
    sentiment_to_sector_to_token_count_dict['overall'] = {}

    # Initialize token count for each sector for each sentiment to 0
    for key in sentiment_to_sector_to_token_count_dict:
        sectors = ["agriculture, forestry, fishing and hunting", "mining, quarrying, and oil and gas extraction", "utilities", "construction", "manufacturing", "wholesale trade", "retail trade", "transportation and warehousing", "information", "finance and insurance", "real estate and rental and leasing", "professional, scientific, and technical services", "management of companies and enterprises", "administrative and support and waste management and remediation services", "educational services", "health care and social assistance", "arts, entertainment, and recreation", "accommodation and food services", "other services (except public administration)", "public administration"]
        for sector in sectors:
            sentiment_to_sector_to_token_count_dict[key][sector] = 0

    # Sector number to name mapping from https://www.census.gov/naics/?58967?yearbck=2022
    sector_num_to_name_dict = {11: "agriculture, forestry, fishing and hunting", 21: "mining, quarrying, and oil and gas extraction", 22: "utilities", 23: "construction", 31: "manufacturing", 32: "manufacturing", 33: "manufacturing", 42: "wholesale trade", 44: "retail trade", 45: "retail trade", 48: "transportation and warehousing", 49: "transportation and warehousing", 51: "information", 52: "finance and insurance", 53: "real estate and rental and leasing", 54: "professional, scientific, and technical services", 55: "management of companies and enterprises", 56: "administrative and support and waste management and remediation services", 61: "educational services", 62: "health care and social assistance", 71: "arts, entertainment, and recreation", 72: "accommodation and food services", 81: "other services (except public administration)", 92: "public administration"}

    for row in speaker_turn_rows_with_sentiment_counts:
        curr_id, curr_filename, curr_speaker_text, num_tokens, negative, positive, uncertainty, litigious, strong_modal, weak_modal, constraining = row
        # Only include files for which we have Compustat metadata
        if curr_filename in ect_filename_to_naics_dict:
            naics_code = ect_filename_to_naics_dict[curr_filename]
            # Some files have empty string for NAICS code. Ignore those files.
            if naics_code != '':
                # First two digits of NAICS code represent sector.
                # The first two digits designate the economic sector, the third digit designates the subsector, the fourth digit designates the industry group,
                # the fifth digit designates the NAICS industry, and the sixth digit designates the national industry.
                sector_num = int(naics_code[:2])
                # Ignore files whose sector numbers are not valid 2022 NAICS sector numbers.
                if sector_num in sector_num_to_name_dict:
                    sector_name = sector_num_to_name_dict[sector_num]
                    # Keep track of number of tokens for each sentiment in this sector
                    for sentiment in sentiment_categories:
                        sentiment_to_sector_to_token_count_dict[sentiment][sector_name] += eval(sentiment) # eval makes use of the negative, positive, uncertainty, litigious, strong_modal, weak_modal, constraining variables above
                
                    # Keep track of total number of tokens in this sector
                    sentiment_to_sector_to_token_count_dict['overall'][sector_name] += num_tokens

    return sentiment_to_sector_to_token_count_dict
    
def convert_token_count_dict_to_relative_freq_dict(token_count_dict):
    """ Takes a nested dictionary, where the outer dictionary maps each Loughran McDonald sentiment category to an inner dictionary
        mapping month-year or sector string to number of tokens in that sentiment category that were seen in that month of that year or that sector.

        Uses those token counts to compute relative frequencies.

        Returns a nested dictionary, where the outer dictionary maps each Loughran McDonald sentiment category to an inner dictionary
        mapping month-year or sector string to relative frequency of that sentiment category for that month of that year or that sector.
    """
    # The inner dictionary corresponding to the 'overall' key contains the total number of tokens for each month of each year, or for each sector.
    relative_freq_dict = {}
    for sentiment in token_count_dict:
        if sentiment != 'overall':
            relative_freq_dict[sentiment] = {}
            for month_year_or_sector_str in token_count_dict[sentiment]:
                if token_count_dict['overall'][month_year_or_sector_str] != 0:
                    relative_freq = token_count_dict[sentiment][month_year_or_sector_str] / token_count_dict['overall'][month_year_or_sector_str]
                else:
                    relative_freq = 0
                relative_freq_dict[sentiment][month_year_or_sector_str] = relative_freq
    return relative_freq_dict

def plot_loughran_mcdonald_sentiment_over_time(loughran_mcdonald_sentiment_to_month_to_relative_freq_dict):
    """ Takes a nested dictionary, where the outer dictionary maps each Loughran McDonald sentiment category to an inner dictionary
        mapping month-year string to relative frequency of that sentiment category for that month of that year.

        Saves a stacked barchart of the sentiment category relative frequencies over time.
    """
    # Get a list of all possible month-year combinations from 2019 through 2021.
    months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    years = ["2019", "2020", "2021"]
    month_year_str_list = []
    for year in years:
        for month in months:
            month_year_str_list.append(month + "-" + year)

    labels = month_year_str_list
    width = 0.1                     # width for each bar

    fig, ax = plt.subplots()
    fig.set_size_inches(16, 11)     # increase figure size
    fig.autofmt_xdate()             # make space for and rotate the x-axis tick labels

    prev_bar_heights = []
    for sentiment in loughran_mcdonald_sentiment_to_month_to_relative_freq_dict:
        sentiment_relative_freqs = []

        for month_year_str in month_year_str_list:
            sentiment_relative_freqs.append(loughran_mcdonald_sentiment_to_month_to_relative_freq_dict[sentiment][month_year_str])

        if len(prev_bar_heights) > 0:
            # Use previous sentiment bars' heights as current sentiment's bar bottom starting position
            ax.bar(labels, sentiment_relative_freqs, width, label=sentiment, bottom=prev_bar_heights)
        else:
            # No previous sentiment, so this first sentiment's bar can start at 0
            ax.bar(labels, sentiment_relative_freqs, width, label=sentiment)
        
        if len(prev_bar_heights) == 0:
            # We just plotted our first sentiment, so set previous bar heights to be heights of this first sentiment's bars
            prev_bar_heights = sentiment_relative_freqs
        else:
            # Add current sentiment's bar height to already existing prev_bar_heights
            for i in range(len(prev_bar_heights)):
                prev_bar_heights[i] += sentiment_relative_freqs[i]

    ax.set_ylabel('Relative frequencies')
    ax.set_title('Loughran-McDonald Sentiment of Earnings Calls Over Time')
    ax.legend()

    plt.savefig('loughran_mcdonald_sentiment_over_time.png')

def plot_loughran_mcdonald_sentiment_over_sector(loughran_mcdonald_sentiment_to_sector_to_relative_freq_dict):
    """ Takes a nested dictionary, where the outer dictionary maps each Loughran McDonald sentiment category to an inner dictionary
        mapping sector string to relative frequency of that sentiment category for that sector.

        Saves a stacked barchart of the sentiment category relative frequencies over sector.
    """
    # Get a list of all possible sectors.
    sectors = ["agriculture, forestry, fishing and hunting", "mining, quarrying, and oil and gas extraction", "utilities", "construction", "manufacturing", "wholesale trade", "retail trade", "transportation and warehousing", "information", "finance and insurance", "real estate and rental and leasing", "professional, scientific, and technical services", "management of companies and enterprises", "administrative and support and waste management and remediation services", "educational services", "health care and social assistance", "arts, entertainment, and recreation", "accommodation and food services", "other services (except public administration)", "public administration"]

    labels = sectors
    width = 0.1                     # width for each bar

    fig, ax = plt.subplots()
    fig.set_size_inches(16, 11)     # increase figure size
    fig.autofmt_xdate()             # make space for and rotate the x-axis tick labels

    prev_bar_heights = []
    for sentiment in loughran_mcdonald_sentiment_to_sector_to_relative_freq_dict:
        sentiment_relative_freqs = []

        for sector in sectors:
            sentiment_relative_freqs.append(loughran_mcdonald_sentiment_to_sector_to_relative_freq_dict[sentiment][sector])

        if len(prev_bar_heights) > 0:
            # Use previous sentiment bars' heights as current sentiment's bar bottom starting position
            ax.bar(labels, sentiment_relative_freqs, width, label=sentiment, bottom=prev_bar_heights)
        else:
            # No previous sentiment, so this first sentiment's bar can start at 0
            ax.bar(labels, sentiment_relative_freqs, width, label=sentiment)
        
        if len(prev_bar_heights) == 0:
            # We just plotted our first sentiment, so set previous bar heights to be heights of this first sentiment's bars
            prev_bar_heights = sentiment_relative_freqs
        else:
            # Add current sentiment's bar height to already existing prev_bar_heights
            for i in range(len(prev_bar_heights)):
                prev_bar_heights[i] += sentiment_relative_freqs[i]

    ax.set_ylabel('Relative frequencies')
    ax.set_title('Loughran-McDonald Sentiment of Earnings Calls Over Sector')
    ax.legend()

    plt.savefig('loughran_mcdonald_sentiment_over_sector.png', bbox_inches='tight')   # bbox_inches='tight' is so that the bottom x-axis labels don't get cut off

# to run script:
# Enter econtext virtual environment with matplotlib installed
# python3 loughran_mcdonald_sentiment_csv_plots.py
if __name__ == "__main__":
    ################################################################################################
    #### CREATE CSV COUNTING TOKENS IN EACH SENTIMENT CATEGORY FOR EACH DOCUMENT (SPEAKER TURN) ####
    ################################################################################################
    # Read rows of a TSV file of corporate speaker turns containing core COVID word(s) (formatted [doc id] [filename] [speaker turn text]) into a list of lists.
    # The TSV file has one row for each speaker turn.
    corp_speaker_turns_covid = read_tsv_to_list_of_lists('earnings_calls_core_covid_speaker_turns_no_duplicates.tsv')

    # Load Loughran-McDonald financial sentiment lexicon.
    md = (r'Loughran-McDonald_MasterDictionary_1993-2021.csv')
    master_dictionary, md_header, sentiment_categories, sentiment_dictionaries, stopwords, total_documents = \
        load_masterdictionary(md, True, True)

    # For each speaker turn, count the total number of tokens, as well as the number of tokens in each sentiment category.
    # To produce a list of lists, where each inner list corresponds to one speaker turn
    # and is formatted [document id, transcript filename, document text, token count, negative, positive, uncertainty, litigious, strong_modal, weak_modal, constraining].
    corp_speaker_turns_covid_with_counts = count_sentiment_tokens_per_document(corp_speaker_turns_covid, master_dictionary)

    # Write each inner list of corp_speaker_turns_covid_with_counts as one CSV row.
    write_list_of_lists_to_csv(corp_speaker_turns_covid_with_counts, 'loughran_mcdonald_counts_5_18_22.csv')

    ########################################################
    #### READ TRANSCRIPT METADATA REQUIRED FOR PLOTTING ####
    ########################################################
    # Read CSV of earnings call transcript metadata (that has been merged with Compustat data).
    earnings_call_metadata_rows = read_csv_to_list_of_lists('earnings_call_10KQ_metadata_linked_5-16-22.csv')

    # Obtain two dictionaries: one mapping earnings call transcript filenames to month-year strings,
    # and the other mapping transcript filenames to NAICS codes.
    ect_filename_to_month_dict = map_ect_filenames_to_months(earnings_call_metadata_rows)
    ect_filename_to_naics_dict = map_ect_filenames_to_naics(earnings_call_metadata_rows)

    ####################################################
    #### PLOT LOUGHRAN-MCDONALD SENTIMENT OVER TIME ####
    ####################################################
    # Create a nested dictionary, where the outer dictionary maps each Loughran McDonald sentiment category to an inner dictionary
    # mapping month-year string to number of tokens in that sentiment category that were seen in that month of that year.
    loughran_mcdonald_sentiment_to_month_to_token_count_dict = map_loughran_mcdonald_sentiment_to_month_to_token_count(sentiment_categories, corp_speaker_turns_covid_with_counts, ect_filename_to_month_dict)

    # Uses those token counts to compute relative frequencies.
    # Create a nested dictionary, where the outer dictionary maps each Loughran McDonald sentiment category to an inner dictionary
    # mapping month-year string to relative frequency of that sentiment category for that month of that year.
    loughran_mcdonald_sentiment_to_month_to_relative_freq_dict = convert_token_count_dict_to_relative_freq_dict(loughran_mcdonald_sentiment_to_month_to_token_count_dict)

    # Plot Loughran-McDonald sentiment as stacked barchart over time.
    plot_loughran_mcdonald_sentiment_over_time(loughran_mcdonald_sentiment_to_month_to_relative_freq_dict)

    ######################################################
    #### PLOT LOUGHRAN-MCDONALD SENTIMENT OVER SECTOR ####
    ######################################################
    # Create a nested dictionary, where the outer dictionary maps each Loughran McDonald sentiment category to an inner dictionary
    # mapping sector string to number of tokens in that sentiment category that were seen for that sector.
    loughran_mcdonald_sentiment_to_sector_to_token_count_dict = map_loughran_mcdonald_sentiment_to_sector_to_token_count(sentiment_categories, corp_speaker_turns_covid_with_counts, ect_filename_to_naics_dict)

    # Uses those token counts to compute relative frequencies.
    # Create a nested dictionary, where the outer dictionary maps each Loughran McDonald sentiment category to an inner dictionary
    # mapping sector string to relative frequency of that sentiment category for that sector
    loughran_mcdonald_sentiment_to_sector_to_relative_freq_dict = convert_token_count_dict_to_relative_freq_dict(loughran_mcdonald_sentiment_to_sector_to_token_count_dict)

    # Plot Loughran-McDonald sentiment as stacked barchart over sector.
    plot_loughran_mcdonald_sentiment_over_sector(loughran_mcdonald_sentiment_to_sector_to_relative_freq_dict)