from core.path import PathObject


filepath = r'Z:\Projects\VFX\render\16BTH_2020_Arena\shots\010\0400\lite\tmikota\001.000\high\masterLayer\cam010_0400_cam010_0400\beauty\my_render_file.0001.exr'


path_object = PathObject(filepath)
print path_object.render_pass
print path_object.camera
print path_object.aov
print path_object.filename
print path_object.path_root