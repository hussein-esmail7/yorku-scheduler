'''
yorku-scheduler.py
Hussein Esmail
Created: 2022 06 09
Updated: 2022 06 13
Description: [DESCRIPTION]
'''

import os
import sys
import json
from datetime import datetime as dt
from datetime import timedelta as td

# ========= VARIABLES ===========
PATH_TEMPLATE   = os.path.expanduser("./timetable.tex")
PATH_SCRIPT     = "" # Optional script to run afterwards, passes tex file
PATH_SCRIPT     = os.path.expanduser("~/git/sh/c.sh") # From https://github.com/hussein-esmaily/sh/
PATH_JSON       = ""
DATA            = [] # JSON data will go here
location        = "" # User-inputted location query
LINE_INSERT     = "[CLASSES START]"
LINE_CLASSES_INSERT     = "[CLASS LIST START]"
PRINT_VERBOSE   = False

# ========= COLOR CODES =========
color_end               = '\033[0m'
color_darkgrey          = '\033[90m'
color_red               = '\033[91m'
color_green             = '\033[92m'
color_yellow            = '\033[93m'
color_blue              = '\033[94m'
color_pink              = '\033[95m'
color_cyan              = '\033[96m'
color_white             = '\033[97m'
color_grey              = '\033[98m'

# ========= COLORED STRINGS =========
str_prefix_q            = f"[{color_pink}Q{color_end}]\t "
str_prefix_y_n          = f"[{color_pink}y/n{color_end}]"
str_prefix_err          = f"[{color_red}ERROR{color_end}]\t "
str_prefix_info         = f"[{color_cyan}INFO{color_end}]\t "
str_prefix_done         = f"[{color_green}DONE{color_end}]\t "

# TODO: If user picked to display SU semester, display 2 tables, one for S1,
#       one for S2

def semesters_accepted(current_sem):
    # In a school year, one semester doesn't happen at one time, multiple
    # happen at once. During F term, Y courses are going on, S1 happens during
    # SU, etc.
    if current_sem == "Y":
        return ["Y", "F", "W"]
    elif current_sem == "F":
        return ["Y", "F"]
    elif current_sem == "W":
        return ["Y", "W"]
    elif current_sem == "SU":
        return ["SU", "S1", "S2"]
    elif current_sem == "S1":
        return ["SU", "S1"]
    elif current_sem == "S2":
        return ["SU", "S2"]
    else:
        return [current_sem]

def ask_int(question):
    bool_continue_asking_q = True
    ans = ""
    while bool_continue_asking_q:
        ans = input(f"{str_prefix_q} {question} ")
        try:
            ans = int(ans.strip())
            if ans < 1:
                print(f"{str_prefix_err} Must be a positive number!")
            else:
                bool_continue_asking_q = False
        except:
            print(f"{str_prefix_err} Input a number and no other characters!")
    return ans


def yes_or_no(str_ask):
    while True:
        y_n = input(f"{str_prefix_q} {str_prefix_y_n} {str_ask}").lower()
        if len(y_n) == 0: # Add these 2 lines to template
            return True
        if y_n[0] == "y":
            return True
        elif y_n[0] == "n":
            return False
        if y_n[0] == "q":
            sys.exit()
        else:
            print(f"{str_prefix_err} {error_neither_y_n}")


def main():
    # ========= VARIABLES ===========
    FILENAME_OUTPUT = "test.tex" # LaTeX file name. User changes this later
    PATH_JSON = "" # Path of JSON file will be here
    index_insert = -1 # Index where to put schedule lines in the template file
    index_classes_insert = -1 # Index where to put class list in the template file
    #   The above variable is useful because if there's 0 queries, there's no
    #   point of making a `.tex` file.
    arr_latex_newlines = [] # Lines to insert into the LaTeX file will go here

    # Check the template file location is correct before asking user questions
    if not os.path.exists(PATH_TEMPLATE):
        print(f"{str_prefix_err} Template file does not exist at location!")
        sys.exit(1)
    lines_template = open(PATH_TEMPLATE, "r").readlines()
    for line_num, line in enumerate(lines_template):
        if LINE_INSERT in line:
            index_insert = line_num
        if LINE_CLASSES_INSERT in line:
            index_class_insert = line_num
    if index_insert == -1:
        print(f"{str_prefix_err} No insert line in template file! Expected: '{LINE_INSERT}'")
        sys.exit()
    # Ask for JSON file path
    while not os.path.exists(os.path.expanduser(PATH_JSON)):
        # Keep asking for a path until it gets a valid one
        PATH_JSON = input(f"{str_prefix_q} Path of the JSON file: ")
        if PATH_JSON.lower() == "exit" or PATH_JSON.lower() == "quit":
            # If the user types "quit" or "exit" instead of an actual file path
            sys.exit()
    f = open(PATH_JSON)
    DATA = json.load(f)
    f.close()
    print(f"{str_prefix_info} Loaded JSON file")
    # Ask the user for the building and room
    bool_location_confirmed = False
    while not bool_location_confirmed:
        location = input(f"{str_prefix_q} Input the building and room number: ")
        # Format the user input
        # location = ''.join(location.split()) # Remove duplicate spaces
        location = location.upper() # Capitalize everything
        bool_location_confirmed = yes_or_no(f"Is '{location}' correct? ")

    # Iterate the JSON and return the matching items
    queries = [] # Semesters of the returned queries. Only matters if found more than 1 type
    # Dict format of `queries`:
    # {
    #   "Department" -> LE, AP, GS, ...
    #   "Code" -> EECS/ADMS/EN/ENG/...
    #   "Num" -> 1000, 1001, 2001, etc.
    #   "Section" -> A, B, C, ...
    #   "Type" -> LECT, TUTR, SEMR, LAB, ...
    #   "Day" -> MTWRF
    #   "Duration" -> String of a number in minutes
    #   "Time" -> 14:00, 9:30, ...
    #   "Location" -> Building and room number
    #   "Term" -> F, W, SU, S1, S2, etc.
    # }
    terms = []
    for course in DATA:
        # For every course
        for section in course["Sections"]:
            # For all sections in the course
            for type in ["LECT", "TUTR", "LAB", "SEMR"]:
                # Iterate through all the lectures, tutorials, labs it may have
                for meeting in section[type]:
                    if meeting["Location"] == location:
                        # If this item is in that room, add it to `queries`
                        # The reason this is not processed into the file is
                        # because there may be multiple terms in the JSON file.
                        # Even an SU vs S1 could be an issue (especially if
                        # there's an S2 course at the same time)
                        num = ""
                        if type != "LECT" and type != "SEMR": # Error handling
                            # Since LECT and SEMR doesn't have this value
                            num = meeting["Num"]
                        terms.append(section["Term"])
                        queries.append({
                                "Department": course["Department"],
                                "Code": course["Code"],
                                "Num": course["Num"], # 1000, 2030, etc.
                                "Year": section["Year"], # Actual year
                                "Section": section["Code"],
                                "Type": type,
                                "Num2": num, # The 02 in TUTR 02
                                "Day": meeting["Day"],
                                "Duration": meeting["Duration"],
                                "Time": meeting["Time"],
                                "Location": meeting["Location"],
                                "Term": section["Term"]
                            })
    terms = sorted(list(dict.fromkeys(terms))) # Remove duplicates
    term_use = terms[0]
    if len(terms) > 1:
        print(f"{str_prefix_info} {len(terms)} semester options:")
        for term_num, term in enumerate(terms):
            print(f"\t{term_num+1}. {term}")
        term_use = terms[ask_int(f"Which semester do you want to use?")-1]

    for query in queries:
        if query["Term"] == term_use or query["Term"] in semesters_accepted(term_use):
            # If it is the same term as the query, or if the user chose SU,
            # Still include S1 and S2 classes since it happens at the same time
            num = ""  # "02" from "TUTR 02". Only used in labs and tutorials
            if query["Type"] == "TUTR" or query["Type"] == "LAB":
                num = " " + query["Num2"]
            # print(f"{course['Department']}/{course['Code']} {course['Num']} {section['Code']} - {type} {num}{meeting['Day']} {meeting['Time']} for {meeting['Duration']} minutes.")
            weekday_formatted = query["Day"]
            if weekday_formatted == "R":
                weekday_formatted = "Th"
            # Calculate ending time
            t_1_h = query["Time"].split(":")[0] # Hour, 0-23
            t_1_m = query["Time"].split(":")[1] # Min,  00-59
            t_1 = dt.strptime(t_1_h + ":" + t_1_m, "%H:%M")
            t_2 = t_1 + td(minutes=int(query["Duration"]))
            t_2 = query["Time"] + "-" + str(int(t_2.strftime("%H"))) + ":" + str(t_2.strftime("%M"))
            if term_use != query["Term"]:
                # If the selected term is not the same as this class's term.
                # Only options are S1 or S2 because otherwise it would have
                # been stopped before it reaches this point.
                num += f" ({query['Term']})"
            latex_newline = "\t\\" + query["Type"].split(" ")[0] + "{" + query['Code'] + " " + query["Num"] + " " + query["Section"] + "}{" + query["Type"] + num + "}{" + weekday_formatted + "}{" + t_2 + "}\n"
            # print(latex_newline, end="")
            # latex_newline = "\t\t\\" + type + "{\\href{" + course['URL'] + "}{" + course['Code'] + " " + course['Num'] + " " + section['Code'] + "}}{" + type + num + "}{" + weekday_formatted + "}{" + t_2 + "}\n" # --> With URL to course page. Useless since you have to restart a session anyway
            arr_latex_newlines.append(latex_newline)
            if PRINT_VERBOSE: # If user wants everything printed
                print(latex_newline) # Print the LaTeX line
    print(f"{str_prefix_info} {len(queries)} items")

    class_list = []
    if len(semesters_accepted(term_use)) > 2:
        # len(semesters_accepted(term_use)) > 2 explanation:
        # Only SU and Y terms qualify this. The issue is that the schedule
        # library in LaTeX does not show multiple events at once, so it takes
        # the most recent like of the conflicting ones. This means that it may
        # skip classes. So that there's no data loss, display a list of all the
        # classes and times normally along with what term it actually is
        for query in queries:
            num = ""
            if query["Type"] == "TUTR" or query["Type"] == "LAB":
                num = " " + query["Num2"]
            if term_use != query["Term"]:
                num += f" ({query['Term']})"
            class_list.append("\t\\item " + query['Code'] + " " + query["Num"] + " " + query["Section"] + " " + query["Type"] + num + " " + weekday_formatted + " " + t_2 + "\n")
        class_list = ["All classes in this semester\\footnote{When displaying Y or SU term, there may be conflicts between F/W or S1/S2}\n", "\\begin{itemize*}\n"] + class_list + ["\\end{itemize*}\n"]



    if len(queries) > 0:
        # If there is at least 1 result
        # Make substitutions for things line title, room, etc.
        for line_num, line in enumerate(lines_template):
            if "[FILENAME]" in line:
                lines_template[line_num] = lines_template[line_num].replace("[FILENAME]", FILENAME_OUTPUT)
            if "[DESCRIPTION]" in line:
                lines_template[line_num] = lines_template[line_num].replace("[DESCRIPTION]", f"Schedule for {location} in {query['Year']} {term_use}")
            if "[TITLE]" in line:
                lines_template[line_num] = lines_template[line_num].replace("[TITLE]", f"Schedule for {location} in {query['Year']} {term_use}")
        lines_new = lines_template[:index_insert] + arr_latex_newlines + lines_template[index_insert+1:index_class_insert] + class_list + lines_template[index_class_insert+1:]
        confirmed_filename = False
        while not confirmed_filename:
            FILENAME_OUTPUT = input(f"{str_prefix_q} What would you like to name the output `.tex` file: ")
            if len(FILENAME_OUTPUT) == 0:
                # If the user didn't type anything, give a error + keep asking
                print(f"{str_prefix_err} You must input a file name!")
            else:
                # If the user has inputted a file name, check its validity
                if not FILENAME_OUTPUT.endswith(".tex"):
                    FILENAME_OUTPUT = FILENAME_OUTPUT + ".tex"
                if os.path.exists(FILENAME_OUTPUT):
                    # Make sure you are not overwriting an existing file
                    print(f"{str_prefix_err} {FILENAME_OUTPUT} already exists! Please pick a different file name.")
                else:
                    confirmed_filename = yes_or_no(f"Is '{FILENAME_OUTPUT}' correct? ")
        open(FILENAME_OUTPUT, "w").writelines(lines_new)
        print(f"{str_prefix_done} Wrote to '{FILENAME_OUTPUT}'")
        if len(PATH_SCRIPT) > 0:
            print(f"{str_prefix_info} Detected post-script. Running...")
            os.system(f"{PATH_SCRIPT} \"{FILENAME_OUTPUT}\"")
    sys.exit()


if __name__ == "__main__":
    main()
