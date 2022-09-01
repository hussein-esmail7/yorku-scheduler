'''
yorku-scheduler.py
Hussein Esmail
Created: 2022 06 09
Description: This program generates a LaTeX calendar file for a location at
    York University based on a given JSON file from
    https://github.com/hussein-esmail7/yorku-class-scraper

Test command:
python3 yorku_scheduler.py -s "F" -j "../yorku-class-scraper/json/2022_fw.json" -r "CLH I"
'''

from datetime import datetime as dt
from datetime import timedelta as td
import configparser     # Used to get configuration file contents
import getopt           # Used to get argument information
import json             # Used to parse JSON data file to program
import os
import sys

# ========= VARIABLES ===========
PATH_POST_SCRIPT    = "" # Optional script to run afterwards, passes tex file
PATH_CONFIG         = "~/.config/yorku-scheduler/config"
PATH_JSON           = ""
DATA                = [] # JSON data will go here
location            = "" # User-inputted location query
LINE_INSERT         = "[CLASSES START]"
LINE_CLASSES_INSERT = "[CLASS LIST START]"
BOOL_PRINT_VERBOSE  = False

# ========= COLOR CODES =========
color_end               = '\033[0m'     # Resets color
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

def valid_sem(semester):
    # Check if the semester input is a valid semester. Return "" otherwise
    valid_semesters = ["Y", "F", "W", "SU", "S1", "S2"]
    if semester in valid_semesters:
        return semester
    else:
        return ""

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


def fb(str1, str2):
    # Fallback string, if str1 is empty, return str2
    # Used in case config args are not given, use defaults
    if len(str1.strip()) == 0:
        return str2.strip()
    return str1.strip()

def get_config(PATH_CONFIG):
    PATH_CONFIG = os.path.expanduser(PATH_CONFIG)
    c = configparser.ConfigParser()
    if not os.path.exists(PATH_CONFIG):
        FOLDER_CONFIG = "/".join(PATH_CONFIG.split("/")[:-1])
        if not os.path.exists(FOLDER_CONFIG):
            # Make the config folder if it does not exist
            os.makedirs(FOLDER_CONFIG)
        open(PATH_CONFIG, 'w').write(c)
        print(f"{strPrefix_info} Your config file does not exist! Wrote to {PATH_CONFIG}")
    c.read(PATH_CONFIG)
    config1 = {
            "item_title": c.get("DEFAULT", "item_title", fallback="{s} {n} {a}"),
            "item_subtitle": c.get("DEFAULT", "item_subtitle", fallback="{t} {s}"),
            "color_bg_lect": c.get("DEFAULT", "color_bg_lect", fallback="pink"),
            "color_bg_else": c.get("DEFAULT", "color_bg_else", fallback="lightgray"),
            "color_fg_lect": c.get("DEFAULT", "color_fg_lect", fallback="black"),
            "color_fg_else": c.get("DEFAULT", "color_fg_else", fallback="black"),
            "path_post_script": os.path.expanduser(c.get("DEFAULT", "path_post_script", fallback="")),
            "path_template": os.path.expanduser(c.get("DEFAULT", "path_template", fallback="./timetable.tex"))
            }
    return config1


def main():
    # ========= VARIABLES ===========
    BOOL_PRINTS     = True
    term_use = "" # Semester choice if there are multiple options
    confirmed_filename = False # True when a safe file name has been set
    bool_location_confirmed = False # True when a building and room is set
    FILENAME_OUTPUT = "test.tex" # LaTeX file name. User changes this later
    PATH_JSON = "" # Path of JSON file will be here
    index_insert = -1 # Index where to put schedule lines in the template file
    index_classes_insert = -1 # Index where to put class list in the template file
    #   The above variable is useful because if there's 0 queries, there's no
    #   point of making a `.tex` file.
    arr_latex_newlines = [] # Lines to insert into the LaTeX file will go here


    # GET CONFIGURATIONS FROM CONFIGURATION FILE
    DATA_CONFIG = get_config(PATH_CONFIG)
    PATH_TEMPLATE = DATA_CONFIG["path_template"]
    PATH_POST_SCRIPT     = os.path.expanduser(DATA_CONFIG["path_post_script"])

    # USER ARGUMENT PARSING
    args = sys.argv
    if len(args) > 1:
        # args[0] = file name, ignore this
        for arg_num, arg in enumerate(args[1:]):
            if arg == "-h" or arg == "--help":
                print("--- yorku-scheduler.py ---")
                print("https://github.com/hussein-esmail7/yorku-scheduler")
                print()
                print("Arguments:")
                print("\t-h, --help\tHelp message and exit program.")
                print("\t-j, --json\tInput the JSON path as a string.")
                print("\t-o, --output\tInput the output file name as a string.")
                print("\t-r, --room\tInput the room as a string.")
                print("\t-s, --sem, --semester\n\t\t\tInput the semester you want as a string.")
                print("\t-q, --quiet\tQuiet mode. Only display text when required.")
                sys.exit()
            elif arg == "-j" or arg == "--json":
                # User inputs the JSON location in the next arg
                PATH_JSON = args[arg_num+2]
                if not os.path.exists(os.path.expanduser(PATH_JSON)):
                    # If JSON not found, reset the variable to ask again later
                    print(f"{str_prefix_err} JSON file not found!")
                    PATH_JSON = ""
            elif arg == "-o" or arg == "--output": # .tex file name
                FILENAME_OUTPUT = args[arg_num+2]
            elif arg == "-r" or arg == "--room":
                # User inputs the room in the next arg
                location = args[arg_num+2].strip().upper()
                if len(location.split(" ")) != 2:
                    # If it is not exactly 2 words
                    print(f"{str_prefix_err} The building and room must be 2 words!")
                else:
                    bool_location_confirmed = True
            elif arg == "-s" or arg == "--sem" or arg == "--semester":
                # User inputs the semester they want in the next arg
                term_use = valid_sem(args[arg_num+2])
            elif arg == "-q" or arg == "--quiet":
                BOOL_PRINTS = False
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
    if BOOL_PRINTS:
        print(f"{str_prefix_info} Loaded JSON file")
    # Ask the user for the building and room
    while not bool_location_confirmed:
        location = input(f"{str_prefix_q} Input the building and room number: ")
        # Format the user input
        location = location.strip().upper() # Capitalize everything
        if len(location.split(" ")) != 2:
            # If it is not exactly 2 words
            print(f"{str_prefix_err} The building and room must be 2 words!")
        else:
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
        for meeting in course["Meetings"]:
            # For all meetings in the course
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
                terms.append(course["Term"])
                queries.append({
                        "Department": course["Department"],
                        "Code": course["Code"],
                        "Num": course["Num"], # 1000, 2030, etc.
                        # "Year": section["Year"], # Actual year # TODO
                        "Section": meeting["Section"],
                        "Type": meeting["Type"],
                        "Num2": meeting["Num"], # The 02 in TUTR 02
                        "Day": meeting["Day"],
                        "Duration": meeting["Duration"],
                        "Time": meeting["Time"],
                        "Location": meeting["Location"],
                        "Term": course["Term"]
                    })
    terms = sorted(list(dict.fromkeys(terms))) # Remove duplicates
    if len(terms) > 1 and term_use == "":
        # If a term has not been specified and requires specification
        print(f"{str_prefix_info} {len(terms)} semester options:")
        for term_num, term in enumerate(terms):
            print(f"\t{term_num+1}. {term}")
        term_use = terms[ask_int(f"Which semester do you want to use?")-1]
    elif len(terms) > 0:
        # Set the term to use as the only available option
        # If there are terms available
        term_use = terms[0]
    elif BOOL_PRINTS and len(queries) == 0 and len(terms) == 0:
        print(f"{str_prefix_err} No items found.")
        sys.exit() # If no terms, no point in continuing program

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
            if query["Type"] == "LECT":
                # LECT has its own colour type.
                # The reason this is separate is to indicate that you could
                # potentially drop in and also listen to this lecture. This is
                # less likely in tutorials (TUTR) and seminars (SEMR)
                latex_newline = "\t\\" + query["Type"].split(" ")[0] + "{" + query['Code'] + " " + query["Num"] + " " + query["Section"] + "}{" + query["Type"] + num + "}{" + weekday_formatted + "}{" + t_2 + "}\n"
            else:
                # Automatically use TUTR if it uses an unknown type
                latex_newline = "\t\\ELSE{" + query['Code'] + " " + query["Num"] + " " + query["Section"] + "}{" + query["Type"] + num + "}{" + weekday_formatted + "}{" + t_2 + "}\n"
            # print(latex_newline, end="")
            # latex_newline = "\t\t\\" + type + "{\\href{" + course['URL'] + "}{" + course['Code'] + " " + course['Num'] + " " + section['Code'] + "}}{" + type + num + "}{" + weekday_formatted + "}{" + t_2 + "}\n" # --> With URL to course page. Useless since you have to restart a session anyway
            arr_latex_newlines.append(latex_newline)
            if BOOL_PRINT_VERBOSE: # If user wants everything printed
                print(latex_newline) # Print the LaTeX line
    if BOOL_PRINTS:
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
            lines_template[line_num] = lines_template[line_num].replace("[FILENAME]", FILENAME_OUTPUT)
            lines_template[line_num] = lines_template[line_num].replace("[DESCRIPTION]", f"Schedule for {location} for {term_use}")
            lines_template[line_num] = lines_template[line_num].replace("[TITLE]", f"Schedule for {location} for {term_use}")
            lines_template[line_num] = lines_template[line_num].replace("[COLOR_BG_LECT]", DATA_CONFIG["color_bg_lect"])
            lines_template[line_num] = lines_template[line_num].replace("[COLOR_BG_ELSE]", DATA_CONFIG["color_bg_else"])
            lines_template[line_num] = lines_template[line_num].replace("[COLOR_FG_LECT]", DATA_CONFIG["color_fg_lect"])
            lines_template[line_num] = lines_template[line_num].replace("[COLOR_FG_ELSE]", DATA_CONFIG["color_fg_else"])
            # TODO: Put this back after "Year" has been added: lines_template[line_num] = lines_template[line_num].replace("[DESCRIPTION]", f"Schedule for {location} in {query['Year']} {term_use}")
            # TODO: Put this back after "Year" lines_template[line_num] = lines_template[line_num].replace("[TITLE]", f"Schedule for {location} in {query['Year']} {term_use}")
        lines_new = lines_template[:index_insert] + arr_latex_newlines + lines_template[index_insert+1:index_class_insert] + class_list + lines_template[index_class_insert+1:]
        # If the user inputted the filename using "-o" or "--output"
        # Check its validity (if it would overwrite a file)
        if len(FILENAME_OUTPUT) != 0:
            if not FILENAME_OUTPUT.endswith(".tex"):
                FILENAME_OUTPUT = FILENAME_OUTPUT + ".tex"
            if os.path.exists(FILENAME_OUTPUT):
                # Make sure you are not overwriting an existing file
                print(f"{str_prefix_err} {FILENAME_OUTPUT} already exists!")
            else:
                # When it is a safe file name
                confirmed_filename = True
        while not confirmed_filename: # If the program still needs a file name
            FILENAME_OUTPUT = input(f"{str_prefix_q} What would you like to name the output `.tex` file: ").strip()
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

        # Write to file
        open(FILENAME_OUTPUT, "w").writelines(lines_new)
        if BOOL_PRINTS:
            print(f"{str_prefix_done} Wrote to '{FILENAME_OUTPUT}'")

        # Run post-script (if there is one)
        if len(PATH_POST_SCRIPT) > 0:
            if BOOL_PRINTS:
                print(f"{str_prefix_info} Detected post-script. Running...")
            os.system(f"{PATH_POST_SCRIPT} \"{FILENAME_OUTPUT}\"")

    sys.exit() # Exit program with no erros


if __name__ == "__main__":
    main()
