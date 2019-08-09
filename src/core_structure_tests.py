from cglcore.path import PathObject, CreateProductionData

#######################################
# Tests for Basic Project Creation
#######################################

proj_man = 'lumbermill'
# Create a Company
d = {'company': 'testco'}
path_object = PathObject(d)
print path_object.path_root
CreateProductionData(path_object, project_management=proj_man)

# Create A Project
path_object.set_attr(context='render')
path_object.set_attr(project='cgl_unittest')
CreateProductionData(path_object, project_management=proj_man)
#####################################
# Create a Shot
#####################################

path_object.set_attr(scope='shots')
path_object.set_attr(seq='030')
path_object.set_attr(shot='0400')
CreateProductionData(path_object, project_management=proj_man)

    # Create a Plate Task
path_object.set_attr(task='plate')
CreateProductionData(path_object, project_management=proj_man)

path_object.set_attr(user='tmiko')
path_object.set_attr(version='000.002')
path_object.set_attr(resolution='high')
path_object.set_attr(filename='Capture.PNG')
path_object.set_attr(ext='PNG')
print path_object.preview_path_full
print path_object.path_root
CreateProductionData(path_object, project_management='lumbermill')
CreateProductionData(path_object, project_management='ftrack')



