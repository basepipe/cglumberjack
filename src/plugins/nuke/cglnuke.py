import os
import nuke
from Qt import QtWidgets

from cglcore.path import PathObject


def get_main_window():
    return QtWidgets.QApplication.activeWindow()


def get_scene_name():
    return nuke.Root().name()


def normpath(filepath):
    return filepath.replace('\\', '/')


def get_file_name():
    return unicode(nuke.Root().name())


def open_file(filepath):
    return nuke.scriptOpen(filepath)


def save_file(filepath):
    return nuke.scriptSave(filepath)


def save_file_as(filepath):
    return nuke.scriptSaveAs(filepath)


def import_media(filepath):
    """
    imports the filepath.  This assumes that sequences are formated as follows:
    [sequence] [sframe]-[eframe]
    sequence.####.dpx 1-234
    regular files are simply listed as a string with no frame numbers requred:
    bob.jpg
    :param filepath:
    :return:
    """
    readNode = nuke.createNode('Read')
    readNode.knob('file').fromUserText(filepath)
    path_object = PathObject(filepath).copy(resolution='hdProxy', ext='jpg')
    dir_ = os.path.dirname(path_object.path_root)
    if os.path.exists(dir_):
        readNode.knob('proxy').fromUserText(path_object.path_root)


def create_scene_write_node():
    """
    This function specifically assumes the current file is in the pipeline and that you want to make a write node for
    that.  We can get more complicated and build from here for sure.
    :param filepath:
    :return:
    """
    path_object = PathObject(get_file_name())
    path_object.set_attr(context='render')
    path_object.set_attr(ext='####.dpx')
    write_node = nuke.createNode('Write')
    write_node.knob('file').fromUserText(path_object.path_root)


def import_script(filepath):
    return nuke.nodePaste(filepath)


def import_read_geo(filepath):
    n = nuke.createNode("ReadGeo2")
    n.knob('file').setText(filepath)


def confirm_prompt(title='title', message='message', button=None):
    p = nuke.Panel(title)
    p.addNotepad('', message)
    if button:
        for b in button:
            p.addButton(b)
    else:
        p.addButton('OK')
        p.addButton('Cancel')
    return p.show()


def deselected():
    nuke.selectAll()
    nuke.invertSelection()
