from cglcore.path import PathObject, CreateProductionData

proj_man = 'ftrack'
# Create a Company
d = {'company': 'testco'}
path_object = PathObject(d)
print path_object.path_root
CreateProductionData(path_object, project_management=proj_man)

# Create A Project
path_object.set_attr(context='source')
path_object.set_attr(project='cgl_unittest')
print path_object.path_root
CreateProductionData(path_object, project_management=proj_man)
#####################################
# Create a Shot
#####################################

path_object.set_attr(scope='shots')
path_object.set_attr(seq='000')
path_object.set_attr(shot='0200')
print path_object.path_root
CreateProductionData(path_object, project_management=proj_man)

    # Create a Plate Task
# TODO - it'd be nice to have some tests in place for when someone doesn't provide necessary info.
# currently when i create a task i have to go through all of the available tasks to find a match.
# this is slow as hell.
path_object.set_attr(task='plate')
path_object.set_attr(user='system')
path_object.set_attr(version='000.000')
path_object.set_attr(resolution='high')
print path_object.path_root
CreateProductionData(path_object, project_management=proj_man)
# download this folder: https://media.xiph.org/tearsofsteel/linear-exr/03_2a/
wget -P C:\\Users\\tmikota\\Downloads\\wget_downloads -r -np -nH https://media.xiph.org/tearsofsteel/linear-exr/03_2a/
# wget -r -np -nH --cut-dirs=3 -R index.html https://media.xiph.org/tearsofsteel/linear-exr/03_2a

# Create a high res proxy of the plate

# Create a hd proxy of the plate

# create a high quality qt of the plate

# create a web qt of the plate

# upload the qt of the plate to ftrack

# upload a thumb of the plate to ftrack

# publish the plate



