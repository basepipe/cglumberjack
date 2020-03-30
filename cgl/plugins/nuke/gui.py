import os
from cgl.plugins.Qt import QtCore, QtWidgets
from apps.lumbermill.main import CGLumberjack, CGLumberjackWidget
import nuke
from cgl.ui.widgets.dialog import InputDialog
from cgl.plugins.nuke import cgl_nuke
from cgl.core.path import PathObject
from cgl.core.config import app_config
from cgl.core.utils.general import current_user
from cgl.plugins.preflight.main import Preflight


CONFIG = app_config()


def get_nuke_main_window():
    """Returns Nuke's main window"""

    app = QtWidgets.QApplication.instance()
    for obj in app.topLevelWidgets():
        if obj.inherits('QMainWindow') and obj.metaObject().className() == 'Foundry::UI::DockMainWindow':
            return obj
    else:
        raise RuntimeError('Could not find DockMainWindow instance')


class NukeBrowserWidget(CGLumberjackWidget):
    def __init__(self, parent=None, path=None,
                 show_import=False):
        super(NukeBrowserWidget, self).__init__(parent=parent, path=path, show_import=show_import)
        print 'Nuke Scene path: ', path

    def open_clicked(self):
        print self.path_object.path_root
        print 'open nuke'

    def import_clicked(self):
        from cgl_nuke import import_media, import_script, import_directory, import_geo
        for selection in self.source_selection:
            base_, ext = os.path.splitext(selection)
            if os.path.isdir(selection):
                import_directory(selection)
            if selection.endswith('.nk'):
                import_script(selection)
            elif ext.lower() == '.obj' or ext.lower() == '.fbx':
                import_geo(selection.replace('\\', '/'))
            else:
                import_media(selection)
            print 'nuke import'
        self.parent().parent().accept()


class CGLNukeWidget(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        scene_name = cgl_nuke.get_file_name()
        scene = PathObject(scene_name)
        self.setWindowTitle('Nuke - Lumbermill')
        location = '%s/*' % scene.split_after('shot')
        project_management = CONFIG['account_info']['project_management']
        users = CONFIG['project_management'][project_management]['users']
        user_info = users[current_user()]
        layout = QtWidgets.QVBoxLayout(self)
        main = CGLNuke(path=location, user_info=user_info)
        layout.addWidget(main)


class CGLNuke(CGLumberjack):
    def __init__(self, parent=None, path=None, user_info=None):
        CGLumberjack.__init__(self, parent, user_info=user_info, previous_path=path)
        print 'CGLNuke path is %s' % path
        self.setCentralWidget(NukeBrowserWidget(self, show_import=True, path=path))


class RenderDialog(QtWidgets.QDialog):
    from cgl_nuke import get_main_window

    def __init__(self, parent=get_main_window(), write_node=''):
        QtWidgets.QDialog.__init__(self, parent)

        self.write_node = write_node
        self.render_path = ''
        self.sframe = nuke.knob("root.first_frame")
        self.eframe = nuke.knob("root.last_frame")
        self.byframe = 1
        self.setWindowTitle("Render %s" % self.write_node)

        # define the layouts
        layout = QtWidgets.QVBoxLayout(self)
        grid_layout = QtWidgets.QGridLayout()
        button_row = QtWidgets.QHBoxLayout()

        # define the widgets
        # self.title = QtWidgets.QLabel('Render Write Node:')
        frange_label = QtWidgets.QLabel('Frame Range')
        render_by_label = QtWidgets.QLabel('Render By')

        self.frange_line_edit = QtWidgets.QLineEdit()
        self.render_by_line_edit = QtWidgets.QLineEdit()
        self.render_by_line_edit.setText("1")

        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.render_button = QtWidgets.QPushButton('Render')

        # add stuff to layouts
        grid_layout.addWidget(frange_label, 0, 0)
        grid_layout.addWidget(self.frange_line_edit, 0, 1)
        grid_layout.addWidget(render_by_label, 1, 0)
        grid_layout.addWidget(self.render_by_line_edit, 1, 1)

        button_row.addWidget(self.cancel_button)
        button_row.addWidget(self.render_button)

        layout.addLayout(grid_layout)
        layout.addLayout(button_row)

        self.render_button.clicked.connect(self.on_render_clicked)
        self.render_by_line_edit.textChanged.connect(self.on_text_changed)
        self.frange_line_edit.textChanged.connect(self.on_text_changed)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)

        self.get_frame_range()

    def on_cancel_clicked(self):
        self.accept()

    def get_frame_range(self):
        print 'Getting Frame Range'
        self.frange_line_edit.setText('%s-%s' % (self.sframe, self.eframe))

    def on_render_clicked(self):
        self.accept()
        print 'Rendering %s-%s by %s' % (self.sframe, self.eframe, self.byframe)
        nuke.execute(self.write_node, start=int(self.sframe), end=int(self.eframe), incr=int(self.byframe))
        n = nuke.toNode(self.write_node)
        self.render_path = n['file'].value()
        return self.render_path

    def on_text_changed(self):
        frange = self.frange_line_edit.text()
        self.sframe, self.eframe = frange.split('-')
        self.byframe = self.render_by_line_edit.text()


def render_all_write_nodes():
    """
    render all write nodes (spedifically for handilng in GUI rendering)
    :return:
    """
    render_paths = []
    for n in nuke.allNodes('Write'):
        dialog = RenderDialog(write_node=n.name())
        dialog.exec_()
        render_paths.append(dialog.render_path)
    return render_paths


def render_node(n):
    """
    this is a render command specifically for rendering through the nuke gui interface.
    :param n: nuke node
    :return:
    """
    if n.Class() == 'Write':
        dialog = RenderDialog(write_node=n.name())
        dialog.exec_()
        return dialog.render_path
    else:
        print '%s is not a Write node' % n


def render_selected_local():
    """
    renders selected write nodes through the GUI
    :return:
    """
    render_paths = []
    for s in nuke.selectedNodes():
        if s.Class() == 'Write':
            dialog = RenderDialog(write_node=s.name())
            dialog.exec_()
            render_paths.append(dialog.render_path)
    return render_paths


def getMainWindow():
    app = QtWidgets.QApplication.instance()
    for widget in app.topLevelWidgets():
        if widget.metaObject().className() == 'Foundry::UI::DockMainWindow':
            return widget


def create_write_node():
    """
    Pops up a gui that allows you to create a custom write node or a default write node if left blank
    :return:
    """
    write_nodes = ['']
    dialog = InputDialog(title='Create Write Node',
                         message='Type a Name for an Element (Leave blank for default write node)',
                         combo_box_items=write_nodes)
    dialog.setAttribute(QtCore.Qt.WA_QuitOnClose)
    dialog.exec_()
    if dialog.button == 'Ok':
        if dialog.combo_box.currentText():
            elem_name = 'elem%s' % dialog.combo_box.currentText().title()
            padding = '#' * cgl_nuke.get_biggest_read_padding()
            if not padding:
                padding = '####'
            path_object = cgl_nuke.NukePathObject(cgl_nuke.get_file_name())
            path_object.set_attr(task=elem_name)
            path_object.set_attr(context='render')
            path_object.set_attr(version='000.001')
            path_object.set_attr(filename='%s.%s.exr' % (elem_name, padding))
            write_node = nuke.createNode('Write')
            file_path = os.path.join(path_object.path_root)
            write_node.knob('file').fromUserText(file_path)
            write_node.knob('name').setValue(elem_name)
            return write_node
        else:
            this = cgl_nuke.create_scene_write_node()
            return this


def review_selected():
    """
    Request a review of the selected write node.
    :return:
    """
    import glob
    path_objects = cgl_nuke.get_write_paths_as_path_objects()
    for each in path_objects:
        glob_string = '%s*' % each.path_root.split('#')[0]
        files = glob.glob(glob_string)
        if files:
            each.upload_review()
            print 'reviewing %s' % each.path_root
        else:
            dialog = InputDialog(title='No Rendered Files', message='No Renders Found!  Can not Submit Review',
                                 buttons=['Render', 'Ok'])
            dialog.exec_()
            if dialog.button == 'Render':
                print 'Clicking the Render Selected Button'
            else:
                dialog.accept()


def render_selected():
    if nuke.selectedNodes():
        project_management = CONFIG['account_info']['project_management']
        users = CONFIG['project_management'][project_management]['users']
        if current_user() in users:
            user_info = users[current_user()]
            if user_info:
                dialog = Preflight(parent=None, software='nuke', preflight='render')
                #gui.setWindowFlags(QtCore.Qt.Window)
                dialog.setWindowTitle('Preflight')
                dialog.exec_()


def launch_lumbermill():
    scene_name = cgl_nuke.get_file_name()
    scene = PathObject(scene_name)
    location = '%s/*' % scene.split_after('shot')
    project_management = CONFIG['account_info']['project_management']
    users = CONFIG['project_management'][project_management]['users']
    if current_user() in users:
        user_info = users[current_user()]
        app = QtWidgets.QApplication.instance()
        main_window = CGLNuke(user_info=user_info, path=location)
        main_window.setWindowTitle('CG Lumberjack: Nuke')
        main_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        main_window.show()
        main_window.raise_()
    app.exec_()


def fix_paths():
    import cgl.ui.widgets.path_fixer as path_fixer
    reload(path_fixer)
    write_nodes = nuke.allNodes('Write')
    read_nodes = nuke.allNodes('Read')
    all_nodes = write_nodes + read_nodes
    dialog = path_fixer.PathFixer(nodes=all_nodes)
    dialog.show()
