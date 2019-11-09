from src.core.path import PathObject, CreateProductionData

#######################################
# Tests for Basic Project Creation
#######################################
path_object = PathObject(r'D:/VFX/testoby/testco/render/cgl_unittestC/shots/010/0200/plate/publish/000.000/high')
proj_man = 's'
# Create a Company
d = {'company': 'testco'}
path_object = PathObject(d)
print path_object.path_root
CreateProductionData(path_object, project_management=proj_man)

# Create A Project
path_object.set_attr(context='render')
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

path_object.set_attr(user='publish')
path_object.set_attr(version='000.001')
path_object.set_attr(resolution='high')
print path_object.path_root
#path_object.set_preview_path()
CreateProductionData(path_object, project_management=proj_man)




