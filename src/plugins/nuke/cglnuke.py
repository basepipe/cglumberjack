import os
import nuke
from PySide2 import QtWidgets


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