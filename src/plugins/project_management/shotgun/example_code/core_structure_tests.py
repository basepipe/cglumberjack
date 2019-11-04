from cglcore.path import PathObject, CreateProductionData

#######################################
# Tests for Basic Project Creation
#######################################
# path_object = PathObject(r'D:/VFX/FRIDAY_ROOT/cglumberjack')
proj_man = 'shotgun'
# Create a Company
d = {'company': 'fsucmpa'}
path_object = PathObject(d)
print 1, path_object.path_root
path_object.set_attr(context='render')
path_object.set_attr(project='cgl_unittest')
print 2, path_object.path_root
CreateProductionData(path_object, project_management=proj_man)
# #####################################
# # Create a Shot
# #####################################
#
path_object.set_attr(scope='shots')
path_object.set_attr(seq='010')
path_object.set_attr(shot='0100')
print 3, path_object.path_root
CreateProductionData(path_object, project_management=proj_man)

#     # Create a Plate Task
path_object.set_attr(task='plate')
print 4, path_object.path_root
CreateProductionData(path_object, project_management=proj_man)
path_object.set_attr(user='publish')
path_object.set_attr(version='000.001')
path_object.set_attr(resolution='high')
print 5, path_object.path_root
# #path_object.set_preview_path()
CreateProductionData(path_object, project_management=proj_man)
#
#
#
#
