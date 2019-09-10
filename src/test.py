from cglcore.path import PathObject, CreateProductionData

path_ = r'D:/VFX/FRIDAY_ROOT/cglumberjack/source/cgl_testProjectC/shots/SJM/0020/comp/tmikota'
path_object = PathObject(path_)
CreateProductionData(path_object=path_object, project_management='ftrack', force_pm_creation=True)
