from cgl.core.path import PathObject
# noinspection PyPackageRequirements
import nuke
from cgl.plugins.nuke.gui import create_write_node

def run():
    write_node = create_write_node()
    write_node['channels'].setValue('rgba')
