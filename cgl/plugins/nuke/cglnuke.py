import os
import nuke
from Qt import QtWidgets

from cgl.core.path import PathObject


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
    :return:
    """
    padding = '#'*get_biggest_read_padding()
    path_object = PathObject(get_file_name())
    path_object.set_attr(context='render')
    path_object.set_attr(ext='%s.dpx' % padding)
    write_node = nuke.createNode('Write')
    write_node.knob('file').fromUserText(path_object.path_root)


def get_biggest_read_padding():
    biggest_padding = 0
    for n in nuke.allNodes('Read'):
        temp = os.path.splitext(n['file'].value())[0]
        padding = int(temp.split('%')[1].replace('d', ''))
        if padding > biggest_padding:
            biggest_padding = padding
    return biggest_padding


def check_write_padding():
    """
    Checks all read nodes in the scene to find the largest num padding.  then checks all write nodes to ensure they
    comply.
    :return:
    """
    edited_nodes = []
    scene_padding = get_biggest_read_padding()
    for n in nuke.allNodes('Write'):
        temp, ext = os.path.splitext(n['file'].value())
        base_file = temp.split('%')[0]
        padding = int(temp.split('%')[1].replace('d', ''))
        if padding < scene_padding:
            if scene_padding < 10:
                numformat = '%0'+str(scene_padding)+'d'
            elif scene_padding < 100 and scene_padding > 9:
                numformat = '%'+str(scene_padding)+'d'
            new_file_name = '%s%s%s' % (base_file, numformat, ext)
            edited_nodes.append(new_file_name)
            n.knob('file').fromUserText(new_file_name)
    return edited_nodes


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

def render_local():
    print 'Rendering locally'
