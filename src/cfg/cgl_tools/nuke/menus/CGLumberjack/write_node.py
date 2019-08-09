from cglcore.path import PathObject
# noinspection PyPackageRequirements
import nuke


def get_scene_name():
    return nuke.Root().name()


def create_scene_write_node():
    """
    This function specifically assumes the current file is in the pipeline and that you want to make a write node for
    that.  We can get more complicated and build from here for sure.
    :return:
    """
    path_object = PathObject(get_scene_name())
    path_object.set_attr(context='render')
    path_object.set_attr(ext='####.dpx')
    write_node = nuke.createNode('Write')
    write_node.knob('file').fromUserText(path_object.path_root)


def run():
    create_scene_write_node()

