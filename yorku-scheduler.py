'''
yorku-scheduler.py
Hussein Esmail
Created: 2022 06 09
Updated: 2022 06 09
Description: [DESCRIPTION]
'''

import os
import sys
import json
import datetime

# ========= VARIABLES ===========
PATH_TEMPLATE   = os.path.expanduser("./timetable.tex")
PATH_SCRIPT     = "" # Optional script to run afterwards, passes tex file
PATH_SCRIPT     = os.path.expanduser("~/git/sh/c.sh") # From https://github.com/hussein-esmaily/sh/
PATH_JSON       = ""
DATA            = [] # JSON data will go here
location        = "" # User-inputted location query
LINE_INSERT     = "[CLASSES START]"
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
    FILENAME_OUTPUT = "test.tex"
    index_insert = -1 # Index of where to put formatted LaTeX lines in the template file

    # Check the template file is where it should be before asking user questions
    if not os.path.exists(PATH_TEMPLATE):
        print(f"{str_prefix_err} Template file does not exist at location!")
        sys.exit(1)
    lines_template = open(PATH_TEMPLATE, "r").readlines()
    for line_num, line in enumerate(lines_template):
        if LINE_INSERT in line:
            index_insert = line_num
    if index_insert == -1:
        print(f"{str_prefix_err} No insert line in template file! Expected: '{LINE_INSERT}'")
        sys.exit()
    # Ask for JSON file path
    PATH_JSON = ""
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
    num_meetings_query = 0
    arr_latex_newlines = []
    for course in DATA:
        # For every course
        for section in course["Sections"]:
            # For all sections in the course
            for type in ["LECT", "TUTR", "LAB", "SEMR"]:
                # Iterate through all the lectures, tutorials, labs it may have
                # This loop is not a query loop per se
                for meeting in section[type]:
                    if meeting["Location"] == location:
                        # If this item is in that room
                        num_meetings_query += 1
                        num = ""
                        if type != "LECT" and type != "SEMR":
                            num = " " + meeting["Num"]
                        # print(f"{course['Department']}/{course['Code']} {course['Num']} {section['Code']} - {type} {num}{meeting['Day']} {meeting['Time']} for {meeting['Duration']} minutes.")
                        weekday_formatted = meeting["Day"]
                        if weekday_formatted == "R":
                            weekday_formatted = "Th"
                        # Calculate ending time
                        t_start_hour = meeting["Time"].split(":")[0]
                        t_start_min  = meeting["Time"].split(":")[1]
                        if len(t_start_hour) == 1:
                            t_start_hour = "0" + t_start_hour

                        t_start = datetime.datetime.strptime(t_start_hour + ":" + t_start_min, "%H:%M")
                        t_end = t_start + datetime.timedelta(minutes=int(meeting["Duration"]))
                        time_formatted = meeting["Time"] + "-" + str(int(t_end.strftime("%H"))) + ":" + str(t_end.strftime("%M"))
                        command_string = "\t\\" + type + "{" + course['Code'] + " " + course['Num'] + " " + section['Code'] + "}{" + type + num + "}{" + weekday_formatted + "}{" + time_formatted + "}"
                        arr_latex_newlines.append(command_string + "\n")
                        # command_string = "\t\t\\" + type + "{\\href{" + course['URL'] + "}{" + course['Code'] + " " + course['Num'] + " " + section['Code'] + "}}{" + type + num + "}{" + weekday_formatted + "}{" + time_formatted + "}" # --> With URL to course page. Useless since you have to restart a session anyway
                        if PRINT_VERBOSE:
                            # If the user wants everything printed
                            print(command_string) # Print the LaTeX line
                    # else:
                    #     print(f"{str_prefix_err} {course['Department']}/{course['Code']} {course['Num']} {section['Code']} - {type}")
    print(f"{str_prefix_info} {num_meetings_query} items")
    # If there is at least 1 result
    if num_meetings_query > 0:
        # Make substitutions for things line title, room, etc.
        for line_num, line in enumerate(lines_template):
            if "[FILENAME]" in line:
                lines_template[line_num] = lines_template[line_num].replace("[FILENAME]", FILENAME_OUTPUT)
            if "[DESCRIPTION]" in line:
                lines_template[line_num] = lines_template[line_num].replace("[DESCRIPTION]", f"Schedule for {location}") # TODO: Include the year and semester here later
            if "[TITLE]" in line:
                lines_template[line_num] = lines_template[line_num].replace("[TITLE]", f"Schedule for {location}") # TODO: Include the year and semester here later
        lines_new = lines_template[:index_insert] + arr_latex_newlines + lines_template[index_insert+1:]
        confirmed_filename = False
        while not confirmed_filename:
            FILENAME_OUTPUT = input(f"{str_prefix_q} What would you like to name the output `.tex` file: ")
            if not FILENAME_OUTPUT.endswith(".tex"):
                FILENAME_OUTPUT = FILENAME_OUTPUT + ".tex"
            confirmed_filename = yes_or_no(f"Is '{FILENAME_OUTPUT}' correct? ")
        open(FILENAME_OUTPUT, "w").writelines(lines_new)
        print(f"{str_prefix_done} Wrote to '{FILENAME_OUTPUT}'")
        if len(PATH_SCRIPT) > 0:
            print(f"{str_prefix_info} Detected post-script. Running...")
            os.system(f"{PATH_SCRIPT} \"{FILENAME_OUTPUT}\"")
    sys.exit()


if __name__ == "__main__":
    main()
