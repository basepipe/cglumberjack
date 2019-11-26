from cgl.core.path import PathObject, CreateProductionData
# noinspection PyPackageRequirements
import nuke


def run():
	path_object = PathObject(nuke.Root().name())
	next_minor = path_object.new_minor_version_object().path_root
	CreateProductionData(next_minor)
	nuke.scriptSaveAs(next_minor)
    # TODO - add stuff that helps with the versioning as well
	print 'Version Up Successful! %s ' % next_minor

