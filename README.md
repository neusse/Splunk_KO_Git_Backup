# Splunk_KO_Git_Backup
Collect and update Git repository with Splunk KO's 

This is just a dump of some of my git stuff.

I have a dashboard that will execute the KO backup and  has a button to download the results without having to choose the export type of jsaon.
I also have a cleaner version of the python code I will upload in a week or so.

So the process goes:

- create a local git repo on you desktop/laptop
- run the provided SPL on the target SearchHead and modify for the corect app.
- export the results as JSON
- run the python program with the exported json file as its argument
    - it will create a directory tree in the current directory (CWD)
    - It well extract all the KO's by app and then KO type and then the KO's themselves as json files.  no extension though????
- run a git commit and bobs your uncle.  you can merge that to some git repository or just use VS CODE.



All this can be automated if you can execute the SPL from a Remote Rest call and pull the results set remotely.
I currently have not set that up, but it should not be difficult.  

This solves many issues for myself.   I can even use VS Code to compare KO's on different sand alone Splunk search heads.  ie.  staging and prod.



