from cglcore.path import PathObject, CreateProductionData

path = r'D:\cgl-fsutests\source\thedogmovie\assets\prop\ball\mdl\tmikota\000.014\high\prop_ball_mdl.mb'

path_object = PathObject(path)
"""
path_object.set_attr(task='rig')
path_object.set_attr(version='000.000')
path_object.set_attr(user='publish')
path_object.set_proper_filename()
"""

path_object = path_object.copy(task='rig', version='000.000', user='publish')
path_object.set_proper_filename()
CreateProductionData(path_object)


