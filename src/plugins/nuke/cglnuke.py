import nuke
from PySide2 import QtGui


def get_main_window():
    return QtGui.QApplication.activeWindow()


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


def import_file(filepath):
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