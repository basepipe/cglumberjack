from Qt import QtWidgets, QtCore, QtGui
from apps.lumbermill.main import CGLumberjack, CGLumberjackWidget
import nuke
import cglnuke
import cglui.startup as startup
from cglcore.path import PathObject


class NukeBrowserWidget(CGLumberjackWidget):
    def __init__(self, parent=None, path=None,
                 show_import=False):
        super(NukeBrowserWidget, self).__init__(parent=parent, path=path, show_import=show_import)
        print 'Nuke Scene path: ', path

    def open_clicked(self):
        print self.path_object.path_root
        print 'open nuke'

    def import_clicked(self):
        for selection in self.source_selection:
            if selection.endswith('.nk'):
                cglnuke.import_script(selection)
            else:
                print selection, '-------------------'
                cglnuke.import_media(selection)
            print 'nuke import'


class CGLNuke(CGLumberjack):
    def __init__(self, parent, path=None):
        super(CGLNuke, self, parent).__init__()
        print 'CGLNuke path is %s' % path
        self.setCentralWidget(NukeBrowserWidget(self, show_import=True))


class RenderDialog(QtWidgets.QDialog):
    def __init__(self, parent=cglnuke.get_main_window(), write_node=''):
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
        print 'Rendering %s-%s by %s' % (self.sframe, self.eframe, self.byframe)
        nuke.execute(self.write_node, start=int(self.sframe), end=int(self.eframe), incr=int(self.byframe))
        n = nuke.toNode(self.write_node)
        self.render_path = n['file'].value()
        self.accept()
        return self.render_path

    def on_text_changed(self):
        frange = self.frange_line_edit.text()
        self.sframe, self.eframe = frange.split('-')
        self.byframe = self.render_by_line_edit.text()


def render_all_write_nodes():
    render_paths = []
    for n in nuke.allNodes('Write'):
        dialog = RenderDialog(write_node=n.name())
        dialog.exec_()
        render_paths.append(dialog.render_path)
    return render_paths


def launch():
    scene_name = cglnuke.get_file_name()
    if scene_name == 'Root':
        print 'Lumbermill can not determine project, please launch files from the lumbermill browser'
        return
    else:
        scene = PathObject(scene_name)
        location = '%s/*' % scene.split_after('shot')
        new_object = PathObject(location)
    gui = CGLNuke(parent=cglnuke.get_main_window(), path=location)
    app = startup.do_nuke_gui_init(gui)
    gui.setWindowFlags(QtCore.Qt.Window)
    gui.setWindowTitle('CG Lumberjack')
    if scene_name != 'Root':
        gui.centralWidget().update_location(new_object)
    gui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    gui.show()
    gui.raise_()
    app.exec_()  # this is required to work, yet i get this error: "NoneType" object has no attribute 'exec_',
