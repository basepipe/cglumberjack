from cgl.core.path import PathObject, CreateProductionData

filepath = r'Z:/Projects/VFX/source/16BTH_2020_Arena/shots/020/0600/comp/tmikota/000.000/high/020_0600_comp.nk'

path_object = PathObject(filepath)

print path_object.path
print path_object.path_root
print path_object.project
print path_object.scope
print path_object.company
print path_object.context
print path_object.seq
print path_object.shot
print path_object.task
print path_object.user
print path_object.version
print path_object.resolution
print path_object.filename
print path_object.next_minor_version_number()
print path_object.next_major_version_number()

next_version_object = path_object.next_major_version() # returns a pathObject reflecting the next version globally.
print next_version_object.path_root
# you can use set_attr to change any attribute, and you can do it with multiple attrs.
path_object.set_attr(project='bob', resolution='low')
print path_object.path_root
pathObjectCopy = next_version_object.copy(project='bob')  # use "copy" when you don't want to do anything to the original path object.
print pathObjectCopy.path_root

# path_object.make_preview()  # attempts to make a preview file based off whatever the "rendered" output is.
# path_object.upload_review()  # attempts to upload a review, will make preview .mov if one doesn't exist.

# this will create the next version on disk and it will create it in ftrack, builds all folders and ftrack connections
# CreateProductionData(next_version_object, project_management='ftrack')
