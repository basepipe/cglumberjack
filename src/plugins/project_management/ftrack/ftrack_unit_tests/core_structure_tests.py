from cglcore.path import PathObject, CreateProductionData

#######################################
# Tests for Basic Project Creation
#######################################

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
path_object.set_attr(seq='010')
path_object.set_attr(shot='0100')
print path_object.path_root
CreateProductionData(path_object, project_management=proj_man)

    # Create a Plate Task
path_object.set_attr(task='plate')
print path_object.path_root
CreateProductionData(path_object, project_management=proj_man)

path_object.set_attr(user='system')
path_object.set_attr(version='000.001')
path_object.set_attr(resolution='high')
print path_object.path_root
#path_object.set_preview_path()
CreateProductionData(path_object, project_management=proj_man)




