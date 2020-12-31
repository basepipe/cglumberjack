from Qt import QtWidgets, QtGui
from cgl.ui.widgets.base import LJDialog
from cgl.core.config.config import ProjectConfig, get_root
from cgl.core.path import lj_list_dir
import os


NODE = 0
NODE_TYPE = 1
FIND_TEXT = 2
REPLACE_TEXT = 3
CURRENT_PATH = 6
NEW_PATH = 5
NEW_PATH_EXISTS = 4


class PathFixer(LJDialog):

    def __init__(self, nodes=[], cfg=None):
        LJDialog.__init__(self)
        if not cfg:
            print(PathFixer)
            self.cfg = ProjectConfig()
        else:
            self.cfg = cfg

        self.nodes = nodes
        self.node_dict = {}
        self.root = get_root()
        layout = QtWidgets.QVBoxLayout(self)
        find_replace_row = QtWidgets.QHBoxLayout()
        button_row = QtWidgets.QHBoxLayout()
        # grid_layout = QtWidgets.QGridLayout()
        find_label = QtWidgets.QLabel('Find:')
        replace_label = QtWidgets.QLabel('Replace')
        self.replace_root = QtWidgets.QCheckBox('Replace Root With Current')
        self.replace_root.setChecked(True)

        self.find_line_edit = QtWidgets.QLineEdit()
        self.replace_line_edit = QtWidgets.QLineEdit()

        self.path_table = QtWidgets.QTableWidget()
        self.replace_paths_button = QtWidgets.QPushButton('Replace Paths')

        button_row.addStretch(1)
        button_row.addWidget(self.replace_paths_button)

        find_replace_row.addWidget(self.replace_root)
        find_replace_row.addWidget(find_label)
        find_replace_row.addWidget(self.find_line_edit)
        find_replace_row.addWidget(replace_label)
        find_replace_row.addWidget(self.replace_line_edit)
        find_replace_row.addStretch(1)

        layout.addLayout(find_replace_row)
        layout.addWidget(self.path_table)
        layout.addLayout(button_row)

        self.path_table.setColumnCount(7)
        # path_table.setColumnHidden(4, True)
        self.path_table.setHorizontalHeaderLabels(['Node', 'Node Type', 'Find Text', 'Replace Text', 'New Path Exists',
                                              'New Path', 'Current Path'])
        self.path_table.hideColumn(0)
        self.path_table.hideColumn(1)

        header = self.path_table.horizontalHeader()
        # header.setResizeMode(NODE, QtWidgets.QHeaderView.ResizeToContents)
        # header.setResizeMode(NODE_TYPE, QtWidgets.QHeaderView.ResizeToContents)
        # header.setResizeMode(FIND_TEXT, QtWidgets.QHeaderView.ResizeToContents)
        # header.setResizeMode(REPLACE_TEXT, QtWidgets.QHeaderView.ResizeToContents)
        # header.setResizeMode(CURRENT_PATH, QtWidgets.QHeaderView.ResizeToContents)
        # header.setResizeMode(NEW_PATH, QtWidgets.QHeaderView.ResizeToContents)
        # header.setResizeMode(NEW_PATH_EXISTS, QtWidgets.QHeaderView.ResizeToContents)
        self.path_table.setMinimumHeight(250)
        self.path_table.setMinimumWidth(800)

        self.replace_root.clicked.connect(self.on_replace_root_clicked)
        self.replace_line_edit.textChanged.connect(self.on_replace_line_edit_changed)
        self.find_line_edit.textChanged.connect(self.on_find_line_edit_changed)
        self.replace_paths_button.clicked.connect(self.replace_button_clicked)
        self.process_nodes()

    def replace_button_clicked(self):
        for row in range(self.path_table.rowCount()):
            node_name = self.path_table.item(row, NODE).text()
            filepath = self.path_table.item(row, NEW_PATH).text()
            node = self.node_dict[node_name]
            node.knob('file').fromUserText(filepath)
            try:
                contents = lj_list_dir(os.path.dirname(filepath), cfg=self.cfg)
                for c in contents:
                    if ' ' in c:
                        frange_ = c.split(' ')[-1]
                        if '-' in frange_:
                            sframe, eframe = frange_.split('-')
                            print('setting frange to %s-%s' % (sframe, eframe))
                            node['first'].setValue(int(sframe))
                            node['last'].setValue(int(eframe))
            except WindowsError:
                print('filepath does not exist: %s' % filepath)

    def on_replace_root_clicked(self):
        if self.replace_root.isChecked():
            self.replace_line_edit.setText(self.root)
            for row in range(self.path_table.rowCount()):
                current_path = self.path_table.item(row, CURRENT_PATH).text()
                path_root = self.find_root(current_path)
                self.path_table.item(row, FIND_TEXT).setText(path_root)
                self.update_row(row, find_text=path_root, replace_text=self.root)
        else:
            self.replace_line_edit.clear()
            self.find_line_edit.clear()
            # self.update_row(row, find_text=path_root, replace_text=self.root)

    def on_find_line_edit_changed(self):
        text = self.find_line_edit.text()
        for row in range(self.path_table.rowCount()):
            self.path_table.item(row, FIND_TEXT).setText(text)
            self.update_row(row, find_text=text)

    def on_replace_line_edit_changed(self):
        text = self.replace_line_edit.text()
        for row in range(self.path_table.rowCount()):
            self.path_table.item(row, REPLACE_TEXT).setText(text)
            self.update_row(row, replace_text=text)

    def update_row(self, row, find_text=None, replace_text=None):
        if not find_text:
            find_text = self.path_table.item(row, FIND_TEXT).text()
        if not replace_text:
            replace_text = self.path_table.item(row, REPLACE_TEXT).text()
        current_path = self.path_table.item(row, CURRENT_PATH).text()
        new_path = current_path.replace(find_text, replace_text)
        self.path_table.item(row, NEW_PATH).setText(new_path)
        self.update_colors(row)

    def update_colors(self, row):
        new_path = self.path_table.item(row, NEW_PATH).text()
        find_text = self.path_table.item(row, FIND_TEXT).text()
        replace_text = self.path_table.item(row, REPLACE_TEXT).text()
        current_path = self.path_table.item(row, CURRENT_PATH).text()
        if find_text in current_path:
            self.path_table.item(row, FIND_TEXT).setForeground(QtGui.QBrush(QtGui.QColor(0, 255, 0)))
        else:
            self.path_table.item(row, FIND_TEXT).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
        if os.path.exists(os.path.dirname(new_path)):
            self.path_table.item(row, NEW_PATH_EXISTS).setText('True')
            self.path_table.item(row, NEW_PATH).setForeground(QtGui.QBrush(QtGui.QColor(0, 255, 0)))
        else:
            try:
                self.path_table.item(row, NEW_PATH_EXISTS).setText('False')
            except AttributeError:
                self.path_table.setItem(row, NEW_PATH_EXISTS, QtWidgets.QTableWidgetItem('False'))
            self.path_table.item(row, NEW_PATH).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))

        if os.path.exists(os.path.dirname(current_path)):
            # what we really need is a check box saying that a current path exists, this is the goal of this gui.
            self.path_table.item(row, CURRENT_PATH).setForeground(QtGui.QBrush(QtGui.QColor(0, 255, 0)))
        else:
            self.path_table.item(row, CURRENT_PATH).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))

    @staticmethod
    def find_root(path):
        # TODO - this is a temp fix assuming internal CGL paths
        if 'source' in path:
            return os.path.dirname(os.path.dirname(path.split('source')[0]).replace('\\', '/'))
        if 'render' in path:
            return os.path.dirname(os.path.dirname(path.split('render')[0]).replace('\\', '/'))

    def get_new_path(self, row):
        current_path = self.path_table.item(row, CURRENT_PATH).text()
        find_text = self.path_table.item(row, FIND_TEXT).text()
        replace_text = self.path_table.item(row, REPLACE_TEXT).text()
        new_text = current_path.replace(find_text, replace_text)
        if os.path.exists(os.path.dirname(new_text)):
            self.path_table.setItem(row, NEW_PATH_EXISTS, QtWidgets.QTableWidgetItem('True'))
        return new_text

    def process_nodes(self):
        """
        specifically for processing nuke nodes
        :return:
        """
        path_roots = {}
        for n in self.nodes:
            self.node_dict[n.name()] = n
            row_position = self.path_table.rowCount()
            c_path = n['file'].value().replace('\\', '/')
            path_root = self.find_root(c_path)
            if path_root in path_roots.keys():
                path_roots[path_root] = path_roots[path_root]+1
            path_roots[path_root] = 1
            self.path_table.insertRow(row_position)
            self.path_table.setItem(row_position, NODE, QtWidgets.QTableWidgetItem(n.name()))
            self.path_table.setItem(row_position, NODE_TYPE, QtWidgets.QTableWidgetItem(n.Class()))
            if self.replace_root.isChecked():
                self.path_table.setItem(row_position, REPLACE_TEXT,
                                        QtWidgets.QTableWidgetItem(self.root))
                self.path_table.setItem(row_position, FIND_TEXT,
                                        QtWidgets.QTableWidgetItem(path_root))
            self.path_table.setItem(row_position, CURRENT_PATH,
                                    QtWidgets.QTableWidgetItem(c_path))
            self.path_table.setItem(row_position, NEW_PATH,
                                    QtWidgets.QTableWidgetItem(self.get_new_path(row_position)))
            # self.update_colors(row_position)

        self.find_line_edit.setText(self.get_highest_path_root(path_roots))
        self.replace_line_edit.setText(self.root)

    @staticmethod
    def get_highest_path_root(path_roots):
        highest_key = None
        if path_roots.keys:
            highest = 0
            for key in path_roots:
                current = path_roots[key]
                if current > highest:
                    highest = current
                    highest_key = key
            return highest_key
        else:
            return None
            

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_window = PathFixer()
    main_window.show()
    app.exec_()
