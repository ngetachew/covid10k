"""
This script goes through all the earnings call transcript txt files for the year
specified by the argument passed in when this script is run.

It parses each transcript txt file, and writes the parsed Python dictionary to a JSON file.
The JSON files are saved to the folders
/data/SCRIPTS/earnings_calls_scripts/parsed_transcripts/parsed_transcripts_2019,
/data/SCRIPTS/earnings_calls_scripts/parsed_transcripts/parsed_transcripts_2020,
/data/SCRIPTS/earnings_calls_scripts/parsed_transcripts/parsed_transcripts_2021,
depending on what argument is passed in for the year when the script is run.

To run script:
cd /data/SCRIPTS/earnings_calls_scripts
python3 parsing_earnings_calls.py 2019
python3 parsing_earnings_calls.py 2020
python3 parsing_earnings_calls.py 2021
"""

"""
Schema for JSON files
----------------
filename : string
company : string
quarter : string
half-year : string
year : string
date : string
participants : dict
  corporate_participants : [string]
  conference_call_participants : [string]
presentation : [SpeakerTurn]
questions_and_answers : [SpeakerTurn]
"""
from collections import namedtuple
from nltk.metrics import edit_distance
import json
import re
import sys
import os

SpeakerTurn = namedtuple("SpeakerTurn", ["speaker", "text", "is_operator", "is_corporate_participant", "index"])
Participant = namedtuple("Participant", ["name", "title", "company_division"])

def parse_participants(participant_lines):
    """Parses either the corporate participants section or the conference call participants section"""
    participants = []
    for part_idx in range(0, len(participant_lines), 2):
        if '*' not in participant_lines[part_idx]:
            # make sure this line is start of the lines for one participant
            # the first line for each participant is indicated by a *
            part_idx += 1
        if part_idx < len(participant_lines) - 1:
            part_name = participant_lines[part_idx][3:-1].rstrip(' ;')
            part_desc = participant_lines[part_idx+1].strip()
            if part_desc == "-" or not part_desc:
                if ";" in part_name:
                    # case where part_name, part_company_div, part_title are all on one line
                    # for example: Jeffrey Moore;Burr Oak Capital;Analyst
                    part_info = part_name.split(";")
                    if len(part_info) == 3:
                        part_name, part_company_div, part_title = part_info
                    elif len(part_info) == 2:
                        # assumes that the words following the semicolon describe the participant's title
                        # but there may be cases where it's the participant's company instead
                        part_name, part_title = part_info
                        part_company_div = ""
                    elif len(part_info) == 1:
                        part_name = part_info
                        part_company_div = ""
                        part_title = ""
                    else:
                        part_name = part_name
                        part_company_div = ""
                        part_title = ""
                    participants.append(Participant(part_name, part_title, part_company_div)._asdict())
                else:
                    participants.append(Participant(part_name, "", "")._asdict())
            else:
                # hacky way to make sure we don't count a new line and then
                # =============================================================================
                # as participant
                if len(part_desc.split(" - ", 1)) == 2:
                    part_company_div, part_title = part_desc.split(" - ", 1)
                    participants.append(Participant(part_name, part_title, part_company_div)._asdict())
                elif len(part_desc.split(";", 1)) == 2:
                    part_company_div, part_title = part_desc.split(";", 1)
                    participants.append(Participant(part_name, part_title, part_company_div)._asdict())
    return participants


def split_out_turns(lines, corp_participants_list):
    """Separates lines into a list of speaker turns"""
    turns = []
    seen_line = False
    current_turn = [lines[0]]
    for line in lines[1:]:
        if re.match(r'^-----', line) and line.strip().endswith("-"):
            if seen_line:
                turns.append(parse_speaker_turn(current_turn, corp_participants_list))
                current_turn = []
            seen_line = not(seen_line)
        current_turn.append(line)
    turns.append(parse_speaker_turn(current_turn, corp_participants_list))
    return turns


def parse_speaker_turn(speaker_lines, corp_participants_list):
    """Parse out one speaker turn for one speaker"""
    speaker_name_line_index = 1
    index_regex = r'\[(\d+)\]'
    index_match = re.search(index_regex, speaker_lines[speaker_name_line_index])
    while not index_match and speaker_name_line_index < len(speaker_lines) - 1:
        speaker_name_line_index += 1
        index_match = re.search(index_regex, speaker_lines[speaker_name_line_index])
    if index_match:
        index = int(index_match.group(1))
        if ";" in speaker_lines[speaker_name_line_index]:
            # print(speaker_lines[speaker_name_line_index])
            speaker_info = speaker_lines[speaker_name_line_index].rstrip(" ]123[4567890;,-\n").split(";")
            if len(speaker_info) == 3:
                speaker_name, speaker_company, speaker_title = speaker_info
                speaker = speaker_name + ",  " + speaker_company + " - " + speaker_title
                speaker_text = "".join(l.lstrip() for l in speaker_lines[2+speaker_name_line_index:])
            elif len(speaker_info) == 2:
                speaker_name, speaker_company_or_title = speaker_info
                speaker = speaker_name + " - " + speaker_company_or_title
                speaker_text = "".join(l.lstrip() for l in speaker_lines[2+speaker_name_line_index:])
            elif len(speaker_info) == 1:
                # case where speaker name is on one line, and speaker company and title are on next line, separated by semicolons
                speaker_name = speaker_info
                speaker_company, speaker_title = speaker_lines[speaker_name_line_index + 1].rstrip(" ]123[4567890;,-\n").split(";")
                speaker = speaker_name + ",  " + speaker_company + " - " + speaker_title
                speaker_text = "".join(l.lstrip() for l in speaker_lines[3+speaker_name_line_index:])
            else:
                speaker = ", ".join(speaker_info)
                speaker_text = "".join(l.lstrip() for l in speaker_lines[2+speaker_name_line_index:])
        else:
            speaker = speaker_lines[speaker_name_line_index].rstrip(" ]123[4567890\n")
            speaker_text = "".join(l.lstrip() for l in speaker_lines[2+speaker_name_line_index:])
        
        is_operator = speaker.startswith("Operator")
        is_corporate_participant = in_corporate_participants_list(speaker, corp_participants_list)
        return SpeakerTurn(speaker, speaker_text, is_operator, is_corporate_participant, index)

    return SpeakerTurn("", "", False, False, -1)

def in_corporate_participants_list(speaker, corporate_participants_list):
    """
    Returns True if speaker is a corporate participant (is in the parsed corporate_participants_list);
    Returns False otherwise.
    """
    speaker_name_companyandtitle = speaker.split(",")
    speaker_name = speaker_name_companyandtitle[0]

    speaker_name = speaker_name.strip()
    for corp_participant in corporate_participants_list:
        # use NLTK's edit_distance function to compute Levenshtein Distance
        # between current speaker's name and corporate participant's name
        # if the difference between the two strings is < 3, we'll count them as equivalent
        if edit_distance(speaker_name, corp_participant["name"]) < 3:
            # consider current speaker to be this corporate participant
            return True
    return False

def parse_presentation(presentation_lines, corp_participants_list):
    """
    Parses presentation lines
    """
    return [t._asdict() for t in split_out_turns(presentation_lines, corp_participants_list)]

def parse_q_and_a(q_and_a_lines, corp_participants_list):
    """
    Parses questions and answers section
    """
    if q_and_a_lines == []:
        return []

    q_and_a_turns = split_out_turns(q_and_a_lines, corp_participants_list)
    turn_dict = [turn._asdict() for turn in q_and_a_turns]
    return turn_dict

def did_corp_participants_read_questions(parsed_q_and_a):
    """
    Takes parsed Q&A section as a list of speaker turns
    Returns True if corporate participants read Q&A questions; False otherwise.
    """
    for turn in parsed_q_and_a:
        if not turn["is_operator"] and not turn["is_corporate_participant"]:
            # the speaker of this turn was a conference call participant (a non-corporate participant)
            return False
    return True

def convert_date_to_mm_dd_yyyy(date):
    """
    Takes in a date in the format MONTH DD, YYYY
    Converts it to MM/DD/YYYY format
    """
    month_day, year = date.split(",")
    year = year.strip()
    month, day = month_day.split(" ")
    if month == "JANUARY":
        month = "01"
    elif month == "FEBRUARY":
        month = "02"
    elif month == "MARCH":
        month = "03"
    elif month == "APRIL":
        month = "04"
    elif month == "MAY":
        month = "05"
    elif month == "JUNE":
        month = "06"
    elif month == "JULY":
        month = "07"
    elif month == "AUGUST":
        month = "08"  
    elif month == "SEPTEMBER":
        month = "09"  
    elif month == "OCTOBER":
        month = "10"  
    elif month == "NOVEMBER":
        month = "11"  
    elif month == "DECEMBER":
        month = "12"  
    return month + "/" + day + "/" + year

def parse_transcript(filename):
    """
    Parses a single earnings call transcript.
    """
    with open(filename) as f:
        lines = [line for line in f]
    
    parse_dict = {}
    parse_dict["filename"] = filename

    # Quarter / Full Year / FY / Half Year and/or company are in the header
    call_title_regex_quarter = r"(Q[1-4] 20[12][01289]) (.+) (?:Earnings|Pre-Recorded|Business Update|Post-Earnings|Pre-recorded|Pre Recorded|Year)"
    call_title_regex_year = r"(Full Year 20[12][01289]) (.+) (?:Earnings|Pre-Recorded|Business Update|Post-Earnings|Pre-recorded|Pre Recorded|Year)"
    call_title_regex_company_quarter = r"(.+) (Q[1-4] 20[12][01289]) Financial"
    call_title_regex_company_quarter_year = r"(.+) (Q[1-4] 20[12][01289]) Estimated Results and (FY 20[12][01289]) Outlook Conference Call"
    call_title_regex_half_year = r"(Half Year 20[12][01289]) (.+) (?:Earnings|Pre-Recorded|Business Update|Post-Earnings|Pre-recorded|Pre Recorded|Year)"
    call_title_regex_company_only = r"(.+) (?:Earnings|Pre-Recorded|Business Update|Post-Earnings|Pre-recorded|Pre Recorded|Year)"
    matches_quarter = re.match(call_title_regex_quarter, lines[5])
    matches_year = re.match(call_title_regex_year, lines[5])
    matches_company_quarter = re.match(call_title_regex_company_quarter, lines[5])
    matches_company_quarter_year = re.match(call_title_regex_company_quarter_year, lines[5])
    matches_half_year = re.match(call_title_regex_half_year, lines[5])
    matches_company_only = re.match(call_title_regex_company_only, lines[5])
    if matches_quarter:
        parse_dict["company"] = matches_quarter.group(2)
        parse_dict["quarter"] = matches_quarter.group(1)
        parse_dict["half-year"] = {}
        parse_dict["year"] = {}
    elif matches_year:
        parse_dict["company"] = matches_year.group(2)
        parse_dict["quarter"] = {}
        parse_dict["half-year"] = {}
        parse_dict["year"] = matches_year.group(1)
    elif matches_company_quarter:
        parse_dict["company"] = matches_company_quarter.group(1)
        parse_dict["quarter"] = matches_company_quarter.group(2)
        parse_dict["half-year"] = {}
        parse_dict["year"] = {}
    elif matches_company_quarter_year:
        parse_dict["company"] = matches_company_quarter_year.group(1)
        parse_dict["quarter"] = matches_company_quarter_year.group(2)
        parse_dict["half-year"] = {}
        parse_dict["year"] = matches_company_quarter_year.group(3)
    elif matches_half_year:
        parse_dict["company"] = matches_half_year.group(2)
        parse_dict["quarter"] = {}
        parse_dict["half-year"] = matches_half_year.group(1)
        parse_dict["year"] = {}
    else:
        parse_dict["company"] = matches_company_only.group(1)
        parse_dict["quarter"] = {}
        parse_dict["half-year"] = {}
        parse_dict["year"] = {}

    # Date is in the header, too
    date_time_regex = r"([A-Z]+ [0-9]+, 20[12][019])"
    matches = re.match(date_time_regex, lines[6])
    parse_dict["date"] = convert_date_to_mm_dd_yyyy(matches.group(0))

    # Split lines between presentation and Q&A
    presentation_index = lines.index("Presentation\n")
    try:
        q_and_a_index = lines.index("Questions and Answers\n")
        presentation_lines = lines[presentation_index+1:q_and_a_index-2]
        question_and_answer_lines = lines[q_and_a_index+1:-46]
    except:
        # no Q&A portion
        presentation_lines = lines[presentation_index+1:-46]
        question_and_answer_lines = []

    # Parse some participants
    parse_dict["participants"] = {}
    # some transcripts don't have corporate participants listed
    try:
        corp_participants_index = lines.index("Corporate Participants\n")
    except:
        corp_participants_index = -1

    # some transcripts don't have conference call participants listed
    try:
        # this has a typo in it intentionally, the transcripts seem to do this too
        conf_participants_index = lines.index("Conference Call Participiants\n")
        conf_participants_lines = lines[conf_participants_index+3:presentation_index-2]
        if corp_participants_index != -1:
            corp_participants_lines = lines[corp_participants_index+3:conf_participants_index-2]
        else:
            corp_participants_lines = []
    except:
        # no conference call participants portion
        conf_participants_index = -1
        conf_participants_lines = []
        if corp_participants_index != -1:
            corp_participants_lines = lines[corp_participants_index+3:presentation_index-2]
        else:
            corp_participants_lines = []

    corp_participants_list = parse_participants(corp_participants_lines)
    parse_dict["participants"]["corporate_participants"] = corp_participants_list
    parse_dict["participants"]["conference_call_participants"] = parse_participants(conf_participants_lines)
    parse_dict["presentation"] = parse_presentation(presentation_lines, corp_participants_list)
    parsed_q_and_a = parse_q_and_a(question_and_answer_lines, corp_participants_list)
    parse_dict["questions_and_answers"] = parsed_q_and_a
    parse_dict["corporate_participants_read_questions"] = did_corp_participants_read_questions(parsed_q_and_a)

    return parse_dict

# to run script:
# cd /data/SCRIPTS/earnings_calls_scripts
# python3 parsing_earnings_calls.py 2019
# python3 parsing_earnings_calls.py 2020
# python3 parsing_earnings_calls.py 2021
if __name__ == "__main__":
    # parse all transcripts in folder for given year (ex: /data/TRANSCRIPTS_2021)
    transcript_year = sys.argv[1]
    transcript_folder =  '/data/TRANSCRIPTS_' + transcript_year
    
    for transcript_filename in os.listdir(transcript_folder):
        print(transcript_filename)
        parse_dict = parse_transcript(transcript_folder + '/' + transcript_filename)
        save_filename = '/data/SCRIPTS/earnings_calls_scripts/parsed_transcripts/parsed_transcripts_' + transcript_year + '/' + transcript_filename[:-3] + 'json'

        with open(save_filename, 'w') as wf:
            json.dump(parse_dict, wf, indent=2)