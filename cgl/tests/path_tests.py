from core.path import PathObject


filepath = r'F:/FSU-CMPA/COMPANIES/VFX/source/tuesdayTest/assets/Prop/Bucket/mdl/tmiko/008.000/high/bucket.blend'


path_object = PathObject(filepath)
print(path_object.root)
print(path_object.task)
print(path_object.filename)
print(path_object.path)
print(path_object.path_root)
