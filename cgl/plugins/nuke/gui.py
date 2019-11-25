from Qt import QtWidgets, QtCore, QtGui
from apps.lumbermill.main import CGLumberjack, CGLumberjackWidget
import nuke
import cgl.ui.startup as startup
from cgl.core.path import PathObject
from cgl.core.config import app_config
from cgl.core.util import current_user


class NukeBrowserWidget(CGLumberjackWidget):
    def __init__(self, parent=None, path=None,
                 show_import=False):
        super(NukeBrowserWidget, self).__init__(parent=parent, path=path, show_import=show_import)
        print 'Nuke Scene path: ', path

    def open_clicked(self):
        print self.path_object.path_root
        print 'open nuke'

    def import_clicked(self):
        from cgl_nuke import import_media, import_script
        for selection in self.source_selection:
            if selection.endswith('.nk'):
                import_script(selection)
            else:
                print selection, '-------------------'
                import_media(selection)
            print 'nuke import'


class CGLNuke(CGLumberjack):
    def __init__(self, parent, path=None, user_info=None):
        CGLumberjack.__init__(self, parent, user_info=user_info)
        print 'CGLNuke path is %s' % path
        self.setCentralWidget(NukeBrowserWidget(self, show_import=True))


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


def render_selected_write_nodes():
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


def launch():
    from cgl_nuke import get_file_name, get_main_window
    scene_name = get_file_name()
    if scene_name == 'Root':
        print 'Lumbermill can not determine project, please launch files from the lumbermill browser'
        location = ''
    else:
        scene = PathObject(scene_name)
        location = '%s/*' % scene.split_after('shot')
        new_object = PathObject(location)
    project_management = app_config()['account_info']['project_management']
    users = app_config()['project_management'][project_management]['users']
    if current_user() in users:
        user_info = users[current_user()]
        if user_info:
            gui = CGLNuke(parent=get_main_window(), path=location, user_info=user_info)
            app = startup.do_nuke_gui_init(gui)
            gui.setWindowFlags(QtCore.Qt.Window)
            gui.setWindowTitle('CG Lumberjack')
            if scene_name != 'Root':
                gui.centralWidget().update_location(new_object)
            gui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            gui.show()
            gui.raise_()
            app.exec_()  # this is required to work, yet i get this error: "NoneType" object has no attribute 'exec_',
        else:
            print 'Cant find user info in lumbermill for %s' % current_user()