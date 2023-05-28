import os
import json
import re
import sys
import time
from datetime import datetime


#############################################################
# Author: George Neusse
# email: neusse@gmail.com
# Phone: 909-292-5415
# Created: 4/26/23
#
# v1.0 - initial release
#
#############################################################


# i have a newer version I will post soon that only writes to changed KO's so the commits only commit changes.
# not every single KO for every commit.



LOG_FILE = "KO_file_writes.log"

#############################################################
# datetime_to_timestamp(dt)
#############################################################


def datetime_to_timestamp(dt):
    return time.mktime(dt.timetuple()) + dt.microsecond / 1e6


#############################################################
# set_file_datetime(file, mytime)
#############################################################
def set_file_datetime(file, mytime):
    # "updated": "2021-06-28T12:06:07-07:00",
    dateObj = datetime.strptime(mytime, "%Y-%m-%dT%H:%M:%S%z")
    os.utime(file, (datetime_to_timestamp(dateObj), datetime_to_timestamp(dateObj)))


#############################################################
# item_dump(item, key_field, type)
#############################################################
def item_dump(item, key_field, type):
    # do some pathing stuff to make dirs and files
    cwd = os.getcwd()  # where are we?
    mypath = os.path.join(f"{cwd}\\{item['eai:acl.app']}", type)
    os.makedirs(mypath, exist_ok=True)
    file = re.sub("\s|\:|\-", "_", item["title"])  # remove junk from filename
    mypath = os.path.join(mypath, file)

    # check if the KO's last updated matches an existing file
    # if they match skip it
    if os.path.isfile(mypath):  # if file exists check timestamp
        x = os.path.getmtime(mypath)
        myctime = datetime_to_timestamp(
            datetime.strptime(time.ctime(x), "%a %b %d %H:%M:%S %Y")
        )
        dateObj = datetime_to_timestamp(
            datetime.strptime(item["updated"], "%Y-%m-%dT%H:%M:%S%z")
        )
        # if the timestamps match dont do anything
        if dateObj == myctime:
            return False

    # OK we need to write the file
    print(item["target"], item["title"], item["eai:acl.app"], item["updated"])
    with open(LOG_FILE, "a") as f:
        f.write(
            f"{item['target']}, {item['title']},  {item['eai:acl.app']}, {item['updated']}\n"
        )

    with open(mypath, "w") as outfile:
        x = ""  # need to keep this in scope
        print("{", file=outfile)  # make it look like json

        for key in item.keys():
            if key == key_field:
                # this needs special handling. So we save it to print it at the end
                x = item[key_field]
            else:
                y = f'\t"{key}": "{item[key]}",'  # print json key data pairs
                print(y.encode("utf8").decode("ascii", "ignore"), file=outfile)

        y = f'\t"{key_field}": \n{x}'
        print(y.encode("utf8").decode("ascii", "ignore"), file=outfile)

        print("}", file=outfile)

    print("<<==>>")
    set_file_datetime(mypath, item["updated"])

    return True


#############################################################
# this dictionary is used to call the processing target
# indirectly throgh a lookup.  It eliminates endless
# if/else.
#############################################################
myWriter = {
    "data/ui/views": ("eai:data", "Dashboards"),
    "saved/searches": ("search", "Searches"),
    "configs/conf-inputs": ("title", "conf_inputs"),
    "configs/conf-lookups": ("eai:data", "conf_lookups"),
    "admin/macros": ("definition", "macros"),
    "datamodel/model": ("description", "datamodel"),
    "saved/eventtypes": ("search", "eventtypes"),
    "configs/conf-tags": ("title", "conf_tags"),
    "data/ui/panels": ("eai:data", "panels"),
    "configs/conf-commands": ("title", "commands"),
    "storage/collections/config": ("title", "collections_config"),
    "data/ui/nav": ("eai:data", "nav"),
    "data/props/calcfields": ("title", "props_calcfields"),
    "data/props/extractions": ("title", "props_extractions"),
    "data/props/fieldaliases": ("value", "props_fieldaliases"),
    "data/props/lookups": ("title", "props_lookups"),
    "data/props/sourcetype-rename": ("title", "sourcetype_rename"),
    "data/transforms/extractions": ("title", "transforms_extractions"),
    "data/transforms/lookups": ("fields_array", "transforms_lookups"),
    "data/transforms/metric-schema": ("title", "metric_schema"),
    "data/transforms/statsdextractions": ("title", "transforms_statsdextractions"),
    "configs/conf-times": ("title", "conf_times"),
    "data/ui/workflow-actions": ("title", "workflow_actions"),
    "configs/conf-viewstates": ("title", "conf_viewstates"),
}


#############################################################
# is_git_repo(path)
#############################################################
# def is_git_repo(path):
#     try:
#         _ = git.Repo(path).git_dir
#         return True
#     except git.exc.InvalidGitRepositoryError:
#         return False


#############################################################
# main reads the json backup of knowlede objects from splunk
# and breaks that up and writes it into app object_type directories
# and then place one file each of the individual objects.
# if this is a git directory we can commit changes to git and
# be able to manage a change history.  We wont know the who but we
# will know the what.
#############################################################
def main():
    # check if we are good to go.
    if not os.path.isfile(sys.argv[1]):
        print()
        print(f"usage: {sys.argv[0]} 'some Splunk json backup file'.")
        print(" see the python source for SPL that can create the backup")
        print(" once the search is done export the results as JSON.")
        print()
        exit(1)

    with open(LOG_FILE, "a") as f:
        f.write("\n\n++++++++++++++++++++++++++++++++++++++++++++\n")
        f.write(f"TimeStamp: {datetime.now()}\n")
        f.write("\n\n++++++++++++++++++++++++++++++++++++++++++++\n")

    # check if GIT is active in our directory
    cwd = os.getcwd()  # where are we?
    # if not is_git_repo(cwd):
    #     # if not make it so
    #     repository = git.init(cwd)

    # setup for a summary count report
    count = 0
    ob_count_itam = {}
    ob_count_stage = {}
    for item in myWriter.keys():
        ob_count_itam.setdefault(item, 0)
        ob_count_stage.setdefault(item, 0)

    # open the backup json file and split it up into the individual files
    with open(sys.argv[1], encoding="utf-8") as fp:
        myjson = fp.readlines()  # read the whole thing
        jo = json.loads(json.dumps(myjson))  # convert text to python object

        for item in jo:  # walk the json object
            item = item.encode("utf-8")
            # myobject = json.loads(item)  # not sure why item needs this???
            # myobject['result']  # drop some fat we want the meat.
            myobject = item["result"]

            # call the dumper with correct info
            wrote = item_dump(
                myobject,
                myWriter[myobject["target"]][0],
                myWriter[myobject["target"]][1],
            )

            if wrote:  # if it was new or updated count it.
                # add to the summary report
                count += 1
                if myobject["eai:acl.app"] == "itam":
                    ob_count_itam[myobject["target"]] += 1
                else:
                    ob_count_stage[myobject["target"]] += 1

        # print the summary report.  We will append to the report forever.
        with open("KO_Objects_summary.txt", "a") as f:
            print("\n\n++++++++++++++++++++++++++++++++++++++++++++\n", file=f)
            print(f"TimeStamp: {datetime.now()}", file=f)
            print(f"Total fo {count} knowledge objects written!\nITAM:", file=f)
            print(json.dumps(ob_count_itam, indent=4), file=f)
            print("IRS_ITAM_INVENTORY:", file=f)
            print(json.dumps(ob_count_stage, indent=4), file=f)

        # Print the summary on the screen as well
        print()
        print("\n\n++++++++++++++++++++++++++++++++++++++++++++\n")
        print(f"TimeStamp: {datetime.now()}")
        print(f"Total fo {count} knowledge objects written!\nITAM:")
        print(json.dumps(ob_count_itam, indent=4))
        print("IRS_ITAM_INVENTORY:")
        print(json.dumps(ob_count_stage, indent=4))
        print()

        # git.add("--all")  # to add all the working files.
        # git.commit(
        #     "-m",
        #     f"commited: {datetime.now()}\n by: {sys.argv[0]}\n",
        #     author="george@neusse.com",
        # )


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

"""
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

    print('| map maxsearches=100 search="| rest splunk_server=local $uri$ count=0 search=eai:acl.app=$app$  | eval target=$target$"')
    # These fields are just junk/noise that clutter the output with nothing usefull.  Delete them.
    print("| fields - display* auto_* _raw id 'eai:digest' qualifiedSearch next_scheduled_time durable* ")


if __name__ == "__main__":
    main()

"""
