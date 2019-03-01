import os
import pandas as pd
from Qt import QtWidgets, QtGui, QtCore
import re

from cglui.widgets.project_selection_module import LineEditWidget, LabelComboRow
from cglui.widgets.dialog import AdvComboBox
from cglui.widgets.base import LJDialog
from core.path import get_projects, get_companies
from core.config import app_config


class QVLine(QtWidgets.QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, data, headers=None, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.headers = headers
        self._data = data

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.headers[section]

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._data.values[index.row()][index.column()])
        return ''


class VariableType(AdvComboBox):

    def __init__(self, parent=None):
        AdvComboBox.__init__(self, parent)
        self.addItems(['Dynamic', 'List', 'Static', "Automated"])

        # attributes of these types:

        # Dynamic: this is fluid, can be changed to almost anything, project name would be dynamic for instance, or it could also be enum if you wanted to lock it down a bit.
        # List: this is a list of possible items, it can potentially be added to
        # Static: This is a static string for instance having a folder called "Clients" that never changes would be an example of that.
        # Automated: This could be potentially the same as "Dynamic" except we're assuming there must be some kind of code that derives the value. This is a much more complex thing to manage.


class PathDesigner(QtWidgets.QVBoxLayout):

    def __init__(self, parent=None, variables=None):
        QtWidgets.QVBoxLayout.__init__(self, parent)

        if variables:
            self.variables = variables
        else:
            self.variables = ['Add Variable']

        self.scroll = QtWidgets.QScrollArea()
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(QtWidgets.QHBoxLayout())
        self.h_layout = QtWidgets.QHBoxLayout()
        self.example_path_label = QtWidgets.QLabel('Example Path')
        self.example_path_line_edit = QtWidgets.QLineEdit()
        self.root_label = QtWidgets.QLabel('root')
        self.root_line_edit = QtWidgets.QLineEdit()
        self.root_line_edit.setPlaceholderText('Root Does not match Company Default, past project root here...')
        self.example_path_line_edit.setPlaceholderText('Type or Paste Example Path Here...')
        self.variables_label = QtWidgets.QLabel('Variables:')
        self.formula_label = QtWidgets.QLabel('Formula:')
        self.grid_layout = QtWidgets.QGridLayout()
        self.root_combo = AdvComboBox()
        self.root_combo.addItem('root')
        self.root_combo.setEnabled(False)
        self.add_combo = QtWidgets.QPushButton()
        self.add_combo.setText('Add Folder')
        self.add_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.root_combo_text = AdvComboBox()
        self.root = app_config()['paths']['root']
        self.root_combo_text.addItem(self.root)
        self.variable_name_label = QtWidgets.QLabel('     Variable Name    ')
        self.type_label = QtWidgets.QLabel('     Type')
        self.example_text_label = QtWidgets.QLabel('     Example Path Pieces')

        self.variables = ['',
                          'company',
                          'project',
                          'user',
                          'date',
                          'task',
                          'media',
                          'stage']

        self.grid_layout.addWidget(self.variable_name_label, 1, 0)
        self.grid_layout.addWidget(self.type_label, 2, 0)
        self.grid_layout.addWidget(self.example_text_label, 0, 0)
        self.grid_layout.addWidget(self.root_combo, 1, 1)
        self.grid_layout.addWidget(VariableType(), 2, 1)
        self.grid_layout.addWidget(QtWidgets.QLabel(app_config()['paths']['root']), 0, 1)

        self.widget.layout().addLayout(self.grid_layout)
        self.widget.layout().addWidget(self.add_combo)
        self.widget.layout().addItem(self.spacer)
        self.scroll.setWidget(self.widget)
        self.scroll.setWidgetResizable(True)

        self.addWidget(self.example_path_label)
        self.addWidget(self.example_path_line_edit)
        self.addWidget(self.root_label)
        self.addWidget(self.root_line_edit)
        self.addWidget(self.variables_label)
        self.addWidget(self.scroll)
        self.addWidget(self.formula_label)

        self.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        self.add_combo.clicked.connect(self.on_add_selected)

        self.hide_root()
        self.hide_grid()
        # path 1: /Volumes/lightroom/cgl-cglumberjack/source/cglsocialmedia/shots/ingestion/2016-02-29/uncategorized/tmikota/high

        self.example_path_line_edit.textChanged.connect(self.on_example_path_changed)

    def on_example_path_changed(self):
        if self.root in self.example_path_line_edit.text():
            path = self.example_path_line_edit.text().replace(self.root, '')
            self.root_line_edit.setText(self.root)
            parts = path.split(os.sep)
        else:
            parts = self.example_path_line_edit.text().split(os.sep)
        self.show_root()
        self.show_grid()
        self.on_add_selected(variables=parts)
        print parts

    def hide_root(self):
        self.root_line_edit.hide()
        self.root_label.hide()

    def show_root(self):
        self.root_line_edit.show()
        self.root_label.show()

    def hide_grid(self):
        self.variables_label.hide()
        self.add_combo.hide()
        self.formula_label.hide()
        [self.grid_layout.itemAt(i).widget().hide()
         for i in range(self.grid_layout.rowCount() * self.grid_layout.columnCount()) if self.grid_layout.itemAt(i)]

    def show_grid(self):
        self.variables_label.show()
        self.add_combo.show()
        self.formula_label.show()
        [self.grid_layout.itemAt(i).widget().show()
         for i in range(self.grid_layout.rowCount() * self.grid_layout.columnCount()) if self.grid_layout.itemAt(i)]

    def on_variable_changed(self):
        print self.sender().parent()
        variable_text = self.sender().currentText()
        for col in range(self.grid_layout.columnCount()):
            current = self.grid_layout.itemAtPosition(0, col)
            if current:
                if current.widget() == self.sender():
                    if current.widget().currentText() == 'date' or current.widget().currentText() == 'media':
                        self.grid_layout.itemAtPosition(1, col).widget().lineEdit().setPlaceholderText('automatic')
                        self.grid_layout.itemAtPosition(1, col).widget().setEnabled(False)
                    else:
                        self.grid_layout.itemAtPosition(1, col).widget().lineEdit().setPlaceholderText(
                            'type %s' % variable_text)
                        self.grid_layout.itemAtPosition(1, col).widget().setEnabled(True)

    def on_add_selected(self, variables=None):
        if not variables:
            col = self.grid_layout.columnCount() + 1
            variable_box = AdvComboBox()
            variable_box.addItems(self.variables)
            self.grid_layout.addWidget(variable_box, 1, col)
            self.grid_layout.addWidget(VariableType(), 2, col)
            self.grid_layout.addWidget(QtWidgets.QLabel(), 0, col)
            variable_box.lineEdit().setPlaceholderText('type or choose path variable')

            variable_box.currentIndexChanged.connect(self.on_variable_changed)
        else:
            for each in variables:
                col = self.grid_layout.columnCount() + 1
                variable_box = AdvComboBox()
                variable_box.setMinimumWidth(200)
                variable_box.addItems(self.variables)
                self.grid_layout.addWidget(variable_box, 1, col)
                self.grid_layout.addWidget(VariableType(), 2, col)
                self.grid_layout.addWidget(QtWidgets.QLabel(each), 0, col)
                variable_box.lineEdit().setPlaceholderText('type or choose path variable')
                variable_box.currentIndexChanged.connect(self.on_variable_changed)

        # TODO - add ways of defining data: "type value, get from metadata, etc..."

        print 'Adding another combo to the variables'
        pass

    def build_file_path(self):
        # go through each column and pull out the text from the thing on row 1
        path = None
        for col in range(self.grid_layout.columnCount()):
            current = self.grid_layout.itemAtPosition(1, col)
            if current:
                print 1, col
                element = current.widget().currentText()
                if not path:
                    path = element
                else:
                    path = os.path.join(path, element)
        return path


class PathFormulator(LJDialog):

    def __init__(self, parent=None):
        super(PathFormulator, self).__init__()
        self.setMinimumWidth(1100)
        test_path = '/volumes/test/company_name/project_name/ingestion/2018-10-09/audio'
        self.company = LabelComboRow(label='Company')
        self.company.combo.setMinimumWidth(500)
        self.current_company = None
        self.current_project = None
        self.project = LabelComboRow(label='Project')
        self.formula = LabelComboRow(label='Path Formula')
        self.formula_name = LineEditWidget(label='Formula Name', read_only=False)
        self.path_example = LineEditWidget(label='Valid Path Example', read_only=False)
        self.path_example.line_edit.setText(test_path)
        self.v_layout = QtWidgets.QVBoxLayout()
        self.v_layout2 = QtWidgets.QVBoxLayout()
        self.h_layout = QtWidgets.QHBoxLayout()

        self.v_layout.addLayout(self.company)
        self.v_layout.addLayout(self.project)
        self.v_layout.addLayout(self.formula)
        self.v_layout.addItem(QtWidgets.QSpacerItem(240, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        self.h_layout.addLayout(self.v_layout)
        self.h_layout.addWidget(QVLine())
        self.h_layout.addLayout(PathDesigner())
        self.setLayout(self.h_layout)

        self.load_companies()
        if self.company:
            self.load_projects()

        self.company.combo.currentIndexChanged.connect(self.on_company_changed)
        self.project.combo.currentIndexChanged.connect(self.on_project_changed)

    def load_companies(self):
        companies = get_companies()
        if companies:
            self.company.combo.addItems(companies)
        self.on_company_changed()

    def load_projects(self):
        projects = get_projects(self.current_company)
        if projects:
            self.project.combo.addItems(projects)
        self.on_project_changed()

    def on_company_changed(self):
        self.current_company = self.company.combo.currentText()

    def on_project_changed(self):
        self.current_project = self.project.combo.currentText()

    def on_create_formula(self):
        self.show_formula_widgets()



if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = PathFormulator()
    td.setWindowTitle('Path Builder')
    td.show()
    td.raise_()
    app.exec_()

