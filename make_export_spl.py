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
# Use below python to create the knowledge objects backup SPL.
# Run the genorated SPL on the target server
# then export as JSON  NOT CSV. use the JSON file as an argument
# to this program to process the data into usable files
# for a GIT repository
#
#############################################################

#############################################################
#
# Use the genorated spl to create the knowledge objects backup.
# Run the genorated spl then export as JSON  NOT CSV!
#
#############################################################

mydict = {
    "views": "data/ui/views",
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
    "times": "configs/conf-times",
    "workflowactions": "data/ui/workflow-actions",
    "viewstates": "configs/conf-viewstates",
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

    print(
        '| map maxsearches=100 search="| rest splunk_server=local $uri$ count=0 search=eai:acl.app=$app$  | eval target=$target$"'
    )
    # These fields are just junk/noise that clutter the output with nothing usefull.  Delete them.
    print(
        '| fields - display* auto_* _raw id "eai:digest" qualifiedSearch next_scheduled_time durable* '
    )


if __name__ == "__main__":
    main()
