import os
import json
import re
import sys
import time
from datetime import datetime
import subprocess
import threading


'''
#############################################################
 Author: George Neusse
 email: neusse@gmail.com  
 Phone: 909-292-5415
 Created: 4/26/23

 v1.0 - initial release
 v2.0 - much expanded and more reliable
#############################################################
'''

'''
TODO:  Need to fix deleted files looping bug if actually marking files deleted.
TODO:  Add GIT automation so it is automagic.
TODO:  Fix CLI argument handling
TODO:  Intigrate creating backup SPL into the CLI options handling (not a stand alone program)

'''


#############################################################
# Definitions:
#############################################################
LOG_FILE = "KO_file_writes.log"


#############################################################
# this dictionary through a lookup eliminates endless if/else.
#############################################################
myWriter = {
    "data/ui/views":                ("eai:data", "Dashboards"),
    "saved/searches":               ("search", "Searches"),
    "configs/conf-inputs":          ("title", "conf_inputs"),
    "configs/conf-lookups":         ("eai:data", "conf_lookups"),
    "admin/macros":                 ("definition", "macros"),
    "datamodel/model":              ("description", "datamodel"),
    "saved/eventtypes":             ("search", "eventtypes"),
    "configs/conf-tags":            ("title", "conf_tags"),
    "data/ui/panels":               ("eai:data", "panels"),
    "configs/conf-commands":        ("title", "commands"),
    "storage/collections/config":   ("title", "collections_config"),
    "data/ui/nav":                  ("eai:data", "nav"),
    "data/props/calcfields":        ("title", "props_calcfields"),
    "data/props/extractions":       ("title", "props_extractions"),
    "data/props/fieldaliases":      ("value", "props_fieldaliases"),
    "data/props/lookups":           ("title", "props_lookups"),
    "data/props/sourcetype-rename": ("title", "sourcetype_rename"),
    "data/transforms/extractions":  ("title", "transforms_extractions"),
    "data/transforms/lookups":      ("fields_array", "transforms_lookups"),
    "data/transforms/metric-schema": ("title", "metric_schema"),
    "data/transforms/statsdextractions": ("title", "transforms_statsdextractions"),
    'configs/conf-times':           ("title", "conf_times"),
    'data/ui/workflow-actions':     ("title", "workflow_actions"),
    'configs/conf-viewstates':      ("title", "conf_viewstates")
}


#############################################################
# collect_files(wd)
#############################################################
def collect_files(wd):
    # TODO: need to add functionality to ignore files that start with the word deleted
    # or we will start looping and create files deleted_deleted_deletedfile
    # not good.
    file_list = {}
    for root, dirs, files in os.walk(wd):
        for name in files:
            file_path = os.path.join(root, name)
            file_list[file_path] = str(datetime.fromtimestamp(
                os.path.getmtime(file_path)))
    return file_list


#############################################################
# count_chars(string, char)
#############################################################
def count_chars(string, char):
    count = 0
    for c in string:
        if c == char:
            count += 1
    return count

#############################################################
# find_missing_elements(dict1, dict2)
#############################################################


def find_missing_elements(dict1, dict2):
    """
    Find missing elements between two dictionaries of KO files.

    Args:
        dict2 (dict): Dictionary containing the all local KO files enumerated.
        dict1 (dict): Dictionary containing the all backup KO files enumerated.

    Returns:
        missing_elements (dict)
    """
    missing_elements = {}
    for key in dict1.keys():
        # only compare if we are looking in a subdirectory
        if count_chars(key, "\\") > 2:
            if key not in dict2.keys():
                missing_elements[key] = dict1[key]
    return missing_elements


#############################################################
# datetime_to_timestamp(dt)
#############################################################
def datetime_to_timestamp(dt):
    return time.mktime(dt.timetuple()) + dt.microsecond/1e6


#############################################################
# set_file_datetime(file, mytime)
#############################################################
def set_file_datetime(file, mytime):
    # "updated": "2021-06-28T12:06:07-07:00",
    dateObj = datetime.strptime(mytime, "%Y-%m-%dT%H:%M:%S%z")
    os.utime(file, (datetime_to_timestamp(dateObj),
             datetime_to_timestamp(dateObj)))


#############################################################
# cleanup_title(my_object)
#############################################################
def cleanup_title(my_object):
    # Clean up the file name by removing special characters
    title = my_object["title"]
    clean_title = re.sub(r"[^\w\s-]", "", title).strip()
    clean_title = re.sub(r"[-\s]+", "_", clean_title)

    # If the file is private, add "(private)-" to the file name
    sharing = my_object["eai:acl.sharing"]
    if sharing == "user":
        clean_title = f"(private)-{clean_title}"

    return clean_title


#############################################################
# create_directory_and_file(item, target)
#############################################################
def create_directory_and_return_file_path(item, target):
    # Get the current working directory
    cwd = os.getcwd()

    # Create a path to the directory based on the app name and directory target
    app_name = item["eai:acl.app"]
    server = item['splunk_server']
    directory_path = os.path.join(cwd, server, app_name, target)

    # Create the directory if it doesn't already exist
    os.makedirs(directory_path, exist_ok=True)

    # Clean up the file name by removing special characters
    # If the file is private, add "(private)-" to the file name
    clean_title = cleanup_title(item)

    # Create a path to the file based on the directory path and cleaned-up file name
    file_path = os.path.join(directory_path, clean_title)

    return file_path, clean_title

#############################################################
# write_json_file(mypath, item, key_field)
#############################################################
def write_json_file(mypath, item, key_field):
    """
    Write JSON data to a file.

    Args:
        mypath (str): Path to the output file.
        item (dict): Dictionary containing the JSON data.
        key_field (str): The key field that needs special handling.

    Returns:
        None
    """

    # had to add binary write and encode utf-8 because of
    # character errors cuased by splunk JSON output

    with open(mypath, 'wb') as outfile:
        # Start writing the JSON object to the file
        outfile.write("{\n".encode("utf-8"))

        # Loop through each key in the dictionary
        for key, value in item.items():
            if key == key_field:
                # If the key is the special field, save it to print at the end
                special_field_value = value
            else:
                # Otherwise, print the key-value pair like a JSON object
                json_pair = f'\t"{key}": "{value}",\n'
                outfile.write(json_pair.encode("utf-8"))

        # Print the special field at the end of the JSON object
        special_field_pair = f'\t"{key_field}": \n{special_field_value}\n'
        outfile.write(special_field_pair.encode("utf-8"))

        # End the JSON object
        outfile.write("}\n".encode("utf-8"))

    # modify file time stame to match the KO's updated time
    set_file_datetime(mypath, item['updated'])

    # Print a delimiter after writing the file
    print("<<==>>")


##### this could be an alternative for the above code if it preservs the formatting of searches and dashboards.
    # # Create a new dictionary with key_field last
    # reordered_item = {k: v for k, v in item.items() if k != key_field}
    # reordered_item[key_field] = item.get(key_field)

    # with open(mypath, 'w', encoding='utf-8') as outfile:
    #     json.dump(reordered_item, outfile, ensure_ascii=False, indent=4)

    # set_file_datetime(mypath, item['updated'])

    # # Print a delimiter after writing the file
    # print("<<==>>")





#############################################################
# check_update_file(mypath, item)
#############################################################
def check_update_file(mypath, item):
    """
    Check if the KO's last updated matches an existing file.
    If they match, skip it.
    """
    if os.path.isfile(mypath):
        # If the file exists, check its last modified timestamp
        file_modified_timestamp = os.path.getmtime(mypath)
        file_modified_datetime = datetime.fromtimestamp(
            file_modified_timestamp)
        file_modified_timestamp = datetime_to_timestamp(file_modified_datetime)

        # Convert the KO's updated timestamp to a datetime object and then to a timestamp
        ko_updated_datetime = datetime.strptime(
            item['updated'], "%Y-%m-%dT%H:%M:%S%z")
        ko_updated_timestamp = datetime_to_timestamp(ko_updated_datetime)

        # If the timestamps match, return False to skip the file
        if file_modified_timestamp == ko_updated_timestamp:
            return False

    # If the file doesn't exist or the timestamps don't match, return True to create the file
    return True


#############################################################
# item_dump(item, key_field, target)
#############################################################
def item_dump(item, key_field, target):

    mypath, clean_title = create_directory_and_return_file_path(item, target)

    if not check_update_file(mypath, item):
        return False

    # OK we need to write some log stuff
    print(item['splunk_server'], item['eai:acl.app'],
          item['target'], clean_title, item['updated'])
    with open(LOG_FILE, "a") as f:
        f.write(
            f"{item['splunk_server']}, {item['eai:acl.app']}, {item['target']}, {clean_title}, {item['updated']}\n")

    # OK do the actual Dump since we are ready
    write_json_file(mypath, item, key_field)

    return True


#############################################################
# main reads the json backup of knowlede objects from splunk
# and breaks that up and writes it into app object_type directories
# and then place one file each of the individual objects.
# if this is a git directory we can commit changes to git and
# be able to manage a change history.  We wont know the who but we
# will know the what.
#############################################################
def main():

    backup_dict = {}

    # Check if the input file exists
    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        print(f"Usage: {sys.argv[0]} 'some Splunk JSON backup file'.")
        print("See the Python source for SPL that can create the backup.")
        exit(1)

    # Write a timestamp to the log file
    with open(LOG_FILE, "a") as log_file:
        log_file.write("\n++++++++++++++++++++++++++++++++++++++++++++\n")
        log_file.write(f"TimeStamp: {datetime.now()}\n")
        log_file.write("\n++++++++++++++++++++++++++++++++++++++++++++\n")

    # Setup for a summary count report
    count = 0
    ob_count = {item: 0 for item in myWriter.keys()}

    # Open the backup JSON file and split it into individual objects
    with open(input_file, encoding="utf-8") as fp:
        for line in fp:
            # Convert each line of text to a JSON object and filter extra junk
            my_object = json.loads(line)["result"]

            # Clean up the file name by removing special characters
            # If the file is private, add "(private)-" to the file name
            clean_title = cleanup_title(my_object)

            # keep track of what is in the baclup file so we can look for missing KO's that might have been deleted
            backup_dict[f".\\{my_object['splunk_server']}\\{my_object['eai:acl.app']}\\{myWriter[my_object['target']][1]}\\{clean_title}"] = my_object['updated']

            # Call the dumper with the correct information
            wrote = item_dump(my_object, *myWriter[my_object["target"]])

            if wrote:
                # If the object was new or updated, increment the count and add it to the summary report
                count += 1
                ob_count[my_object["target"]] += 1

    # Print the summary report to the console
    print("\n\n++++++++++++++++++++++++++++++++++++++++++++\n")
    print(f"TimeStamp: {datetime.now()}")
    print(f"Total of {count} knowledge objects written!\nALL APPS:")
    print(json.dumps(ob_count, indent=4))
    print()

    localfiles_dict = collect_files(".")
    missing_dict = find_missing_elements(backup_dict, localfiles_dict)
    print("Deleted or missing KO backup files:")
    print(json.dumps(missing_dict, indent=4))

    # Print the summary report to a file
    with open("KO_Objects_summary.txt", "a") as summary_file:
        summary_file.write(
            "\n\n++++++++++++++++++++++++++++++++++++++++++++\n")
        summary_file.write(f"TimeStamp: {datetime.now()}\n")
        summary_file.write(
            f"Total of {count} knowledge objects written!\nALL APPS:\n")
        summary_file.write(json.dumps(ob_count, indent=4))
        summary_file.write("Deleted or missing KO files:")
        summary_file.write(json.dumps(missing_dict, indent=4))

    # need to loop through the missing and rename them to deleted_file.

    # give the user a chance to hic control-c to exit and not commit to git.
    # Get user input with a timeout of 10 seconds
    input("Press any key to continue...")
    print("Input received continuing:")

    # Set the path of the PowerShell script
    script_path = ".\\git_commit.ps1"
    # Use the subprocess module to run the PowerShell script
    subprocess.run([r"c:\windows\system32\\WindowsPowerShell\v1.0\powershell.exe", "-File", script_path],
                   capture_output=True)


'''
powershell script to run to manage git updates

# Check if the current directory is a Git repository
if (!(Test-Path -Path ".git" -PathType Container)) {
    # If it is not a Git repository, initialize a new one
    git init
}

# Stage any new files in subdirectories
git add .

# Commit the changes
git commit -m "Added new files in subdirectories"



'''


if __name__ == "__main__":
    main()


#############################################################
#
# Use below python to create the knowledge objects backup SPL.
# Run the genorated SPL on the target server
# then export as JSON  NOT CSV. use the JSON file as an argument
# to this program to process the data into usable files
# for a GIT repository
#
#############################################################

'''
import os
import sys
import time
from datetime import datetime

#############################################################
# Author: George Neusse
# email: neusse@gmail.com
# Created: 4/29/23
#
# v1.0 - initial release
#
#############################################################


#############################################################
#
# Use the genorated spl to create the knowledge objects backup.
# Run this then export as JSON  NOT CSV.
#
#############################################################

mydict = {
    "views":  "data/ui/views",
    "saved searches": "saved/searches",
    "inputs": "configs/conf-inputs",
    "lookup definitions": "configs/conf-lookups",
    "macros": "admin/macros",
    "datamodels": "datamodel/model",
    "eventtypes": "saved/eventtypes",
    "tags": "configs/conf-tags",
    "panels": "data/ui/panels",
    "commands": "configs/conf-commands",
    "collections": "storage/collections/config",
    "nav": "data/ui/nav",
    "calcfields": "data/props/calcfields",
    "extractions": "data/props/extractions",
    "fieldaliases": "data/props/fieldaliases",
    "props lookups": "data/props/lookups",
    "sourcetype-rename": "data/props/sourcetype-rename",
    "transforms extractions": "data/transforms/extractions",
    "transforms lookups": "data/transforms/lookups",
    "metric-schema": "data/transforms/metric-schema",
    "statsdextractions": "data/transforms/statsdextractions",
    'times': 'configs/conf-times',
    'workflowactions': 'data/ui/workflow-actions',
    'viewstates': 'configs/conf-viewstates'
}

#############################################################
#
#############################################################


def main():

    app_list = []

    # check if we are good to go.
    if not (len(sys.argv) > 1):
        print()
        print(f"usage: {sys.argv[0]} 'list of splunk app directory names'.")
        print(" this creates SPL source to create a backup of KO's for all aps listed")
        print(" once the search is done export the results as JSON. NOT CSV!")
        print()
        exit(1)

    for myarg in sys.argv[1:]:
        app_list.append(myarg)

    print('| makeresults format=csv data="app, target, uri')

    # this will create all the proper rest calls for all apps we are interested in on a server
    for app in app_list:
        for item in mydict.keys():
            print(f"{app}, {mydict[item]}, /servicesNS/-/{app}/{mydict[item]}")

    print('"')
    print('| map maxsearches=100 search="| rest splunk_server=local $uri$ count=0 search=eai:acl.app=$app$  | eval target=$target$"')
    # These fields are just junk/noise that clutter the output with nothing usefull.  Delete them.
    print("| fields - display* auto_* _raw id *digest qualifiedSearch next_scheduled_time durable* ")


if __name__ == "__main__":
    main()

'''
