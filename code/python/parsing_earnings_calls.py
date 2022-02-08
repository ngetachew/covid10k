"""
Schema for files
----------------
filename : string
date : string
quarter : string
company : string
participants : dict
  corporate_participants : [string]
  conference_call_participants : [string]
presentation : [SpeakerTurn]
questions_and_answers : 
  question : SpeakerTurn
  operator_instructions : string
  answers : [SpeakerTurn]
"""
from collections import namedtuple
import json
import re
import sys
import os


SpeakerTurn = namedtuple("SpeakerTurn", ["speaker", "text", "is_operator", "index"])
Participant = namedtuple("Participant", ["name", "title", "company_division"])


def parse_participants(participant_lines):
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


def split_out_turns(lines):
    turns = []
    seen_line = False
    current_turn = [lines[0]]
    for line in lines[1:]:
        if re.match(r'^-----', line) and line.strip().endswith("-"):
            if seen_line:
                turns.append(parse_speaker_turn(current_turn))
                current_turn = []
            seen_line = not(seen_line)
        current_turn.append(line)
    turns.append(parse_speaker_turn(current_turn))
    return turns


# Parse out speaker turns
def parse_speaker_turn(speaker_lines):
    # For each speaker
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
        return SpeakerTurn(speaker, speaker_text, is_operator, index)

    return SpeakerTurn("", "", False, -1)

# Parse presentation lines
def parse_presentation(presentation_lines):
    return [t._asdict() for t in split_out_turns(presentation_lines)]

def parse_q_and_a_round(round_turns, has_operator):
    operator_instructions = round_turns[0]
    operator_instructions_dict = operator_instructions._asdict()
    if not has_operator:
        operator_instructions_dict = {}
        question = round_turns[0]
        answers = round_turns[1:]
        question_dict = question._asdict()
        answers_dict = [a._asdict() for a in answers]
    elif len(round_turns) == 1:
        question_dict = {}
        answers_dict = {}
    else:
        question = round_turns[1]
        answers = round_turns[2:]
        question_dict = question._asdict()
        answers_dict = [a._asdict() for a in answers]
    return {
        "operator_instructions": operator_instructions_dict,
        "question": question_dict,
        "answers": answers_dict
    }


# Parse questions and answers
def parse_q_and_a(q_and_a_lines):
    if q_and_a_lines == []:
        return []

    q_and_a_turns = split_out_turns(q_and_a_lines)
    has_operator = True # assume there's operator for Q&A section
    operator_indices = [i for (i, t) in enumerate(q_and_a_turns) if t.is_operator]
    if operator_indices:
        question_chunks = [q_and_a_turns[operator_indices[i]:operator_indices[i+1]] for i in range(len(operator_indices) - 1)]
    else:
        # case where there's no operator for Q&A section
        has_operator = False
        question_chunks = [q_and_a_turns]
    
    if question_chunks == []:
        # case where the operator did speak during Q&A
        # but may have only given 1 concluding remark
        # we can't use that to determine whether questions were asked
        has_operator = False
        question_chunks = [q_and_a_turns]
        
    return [parse_q_and_a_round(chunk, has_operator) for chunk in question_chunks]


def parse_transcript(filename):
    """Parses a single earnings call transcript."""
    with open(filename) as f:
        lines = [line for line in f]
    
    parse_dict = {}
    parse_dict["filename"] = filename

    # Quarter / Full Year / FY / Half Year and/or company are in the header
    call_title_regex_quarter = r"(Q[1-4] 20[12][0129]) (.+) (?:Earnings|Pre-Recorded|Business Update|Post-Earnings|Pre-recorded|Pre Recorded|Year)"
    call_title_regex_year = r"(Full Year 20[12][0129]) (.+) (?:Earnings|Pre-Recorded|Business Update|Post-Earnings|Pre-recorded|Pre Recorded|Year)"
    call_title_regex_company_quarter = r"(.+) (Q[1-4] 20[12][0129]) Financial"
    call_title_regex_company_quarter_year = r"(.+) (Q[1-4] 20[12][0129]) Estimated Results and (FY 20[12][0129]) Outlook Conference Call"
    call_title_regex_half_year = r"(Half Year 20[12][0129]) (.+) (?:Earnings|Pre-Recorded|Business Update|Post-Earnings|Pre-recorded|Pre Recorded|Year)"
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
    parse_dict["date"] = matches.group(0)

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

    parse_dict["participants"]["corporate_participants"] = parse_participants(corp_participants_lines)
    parse_dict["participants"]["conference_call_participants"] = parse_participants(conf_participants_lines)
    parse_dict["presentation"] = parse_presentation(presentation_lines)
    parse_dict["questions_and_answers"] = parse_q_and_a(question_and_answer_lines)

    return parse_dict

# to run script:
# cd /data/SCRIPTS/earnings_calls_scripts
# python3 parsing_earnings_calls.py 2021
# python3 parsing_earnings_calls.py 2020
# python3 parsing_earnings_calls.py 2019
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