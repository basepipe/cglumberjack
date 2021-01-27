from cgl.core.path import PathObject, CreateProductionData
# noinspection PyPackageRequirements
import plugins.nuke.cgl_nuke as cgl_nuke


def run():
	cgl_nuke.version_up()
