from cglcore.path import PathObject, CreateProductionData

def run():
	path_object = PathObject(nuke.Root().name())
	next_minor = path_object.new_minor_version_object().path_root
	CreateProductionData(next_minor)
	nuke.scriptSaveAs(next_minor)
	print 'Version Up Successful! %s ' % next_minor