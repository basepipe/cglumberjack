How to Use the "default files" feature.

Within Magic Browser you can create default files on a per task basis.

When creating a new assignment Magic Browser looks in ../config_/resources/default_files/ for folders
that match task names.

for instance when creating a 'mdl' task if it finds:

../config_/resources/default_files/mdl/default.blnd

it will use that file as a starting point when creating the task.

If it doesn't find a 'mdl' folder it will simply create an empty folder when creating the task.
