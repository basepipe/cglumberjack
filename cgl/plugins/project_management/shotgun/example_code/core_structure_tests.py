from cgl.core.path import PathObject, CreateProductionData

#######################################
# Tests for Basic Project Creation
#######################################
# path_object = PathObject(r'D:/VFX/FRIDAY_ROOT/cglumberjack')
proj_man = 'shotgun'
# Create a Company
d = {'company': 'doesthiswork'}
path_object = PathObject(d)
# print(1, path_object.path_root
path_object.set_attr(context='source')
path_object.set_attr(project='tomtestAAA')
# print(2, path_object.path_root
print(path_object.path_root)
CreateProductionData(path_object, project_management=proj_man, force_pm_creation=True)
# #####################################
# # Create a Shot
# #####################################
#
# path_object.set_attr(scope='shots')
# path_object.set_attr(seq='010')
# path_object.set_attr(shot='0100')
# # print(3, path_object.path_root
# CreateProductionData(path_object, project_management=proj_man, force_pm_creation=True)
#
# #     # Create a Plate Task
# path_object.set_attr(task='anim')
# # print(4, path_object.path_root
# # CreateProductionData(path_object, project_management=proj_man, force_pm_creation=True)
# path_object.set_attr(user='tmikota')
# path_object.set_attr(version='000.002')
# path_object.set_attr(resolution='high')
# # print(5, path_object.path_root
# # path_object.set_preview_path()
# CreateProductionData(path_object, project_management=proj_man, force_pm_creation=True, status='ip')
# print("How am i handling status in shotgun"