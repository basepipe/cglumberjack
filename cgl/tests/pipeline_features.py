from cgl.core.path import PathObject, CreateProductionData

# if it matches the render output
filepath = r'Z:\Projects\VFX\render\16BTH_2020_Arena\shots\010\0400\lite\tmikota\001.000\high\masterLayer\cam010_0400_cam010_0400\beauty\my_render_file.0001.exr'
# if it's a folder that matches the default template
filepath2 = r'Z:\Projects\VFX\render\16BTH_2020_Arena\shots\010\0400\lite\tmikota\001.000\high\masterLayer'
# if it's a folder inbetweeen default template and render template
filepath3 = r'Z:\Projects\VFX\render\16BTH_2020_Arena\shots\010\0400\lite\tmikota\001.000\high\masterLayer\cam010_0400_cam010_0400'
filepath4 = r'Z:\Projects\VFX\render\16BTH_2020_Arena\shots\010\0400\lite\tmikota\001.000\high\masterLayer\cam010_0400_cam010_0400\beauty'

# if it's the default template
filepath5 = r'Z:/Projects/VFX/render/16BTH_2020_Arena/shots/020/0600/comp/tmikota/000.000/high/filename.txt'
filepath6 = r'Z:/Projects/VFX/render/16BTH_2020_Arena/shots/020/0600/comp/tmikota/000.000'
filepath7 = r'Z:/Projects/VFX/render/16BTH_2020_Arena/shots/020/0600/comp/tmikota'
filepath8 = r'Z:/Projects/VFX/render/16BTH_2020_Arena/shots/020/0600/comp'
filepath9 = r'Z:/Projects/VFX/render/16BTH_2020_Arena/shots/020/0600'
filepath10 = r'Z:/Projects/VFX/render/16BTH_2020_Arena/shots/020'
filepath11 = r'Z:/Projects/VFX/render/16BTH_2020_Arena/shots'
filepath12 = r'Z:/Projects/VFX/render/16BTH_2020_Arena'
filepath13 = r'Z:/Projects/VFX/render'
filepath14 = r'Z:/Projects/VFX'
filepath15 = r'Z:/Projects'

# filepath = r'Z:/Projects/VFX/render/16BTH_2020_Arena/shots/020/0600/comp/tmikota/000.000/high/filename.txt'
# TODO need a way on path to figure out if i'm given a folder that's part of a longer thing.
path_object = PathObject(filepath)
print path_object.render_pass, path_object.camera, path_object.aov, path_object.filename
print path_object.path_root
# path_object2 = PathObject(filepath2)
# print path_object2.camera, path_object.render_pass, path_object.aov, path_object.filename
# print path_object2.path_root
# path_object3 = PathObject(filepath3)
# print path_object3.camera, path_object.render_pass, path_object.aov, path_object.filename
# print path_object3.path_root
# path_object4 = PathObject(filepath4)
# print path_object4.camera, path_object.render_pass, path_object.aov, path_object.filename
# print path_object4.path_root
# path_object5 = PathObject(filepath5)
# print path_object5.camera, path_object.render_pass, path_object.aov, path_object.filename
# print path_object5.path_root
# path_object.set_attr(filename='test_folder')

# print path_object.path_root
# print path_object.filename
# print path_object.ext
# print path_object.project
# print path_object.scope
# print path_object.company
# print path_object.context
# print path_object.seq
# print path_object.shot
# print path_object.task
# print path_object.user
# print path_object.version
# print path_object.resolution
# print path_object.filename
# print path_object.next_minor_version_number()
# print path_object.next_major_version_number()

# next_version_object = path_object.next_major_version() # returns a pathObject reflecting the next version globally.
# print next_version_object.path_root
# # you can use set_attr to change any attribute, and you can do it with multiple attrs.
# path_object.set_attr(project='bob', resolution='low')
# print path_object.path_root
# pathObjectCopy = next_version_object.copy(project='bob')  # use "copy" when you don't want to do anything to the original path object.
# print pathObjectCopy.path_root

# path_object.make_preview()  # attempts to make a preview file based off whatever the "rendered" output is.
# path_object.upload_review()  # attempts to upload a review, will make preview .mov if one doesn't exist.

# this will create the next version on disk and it will create it in ftrack, builds all folders and ftrack connections
# CreateProductionData(next_version_object, project_management='ftrack')
