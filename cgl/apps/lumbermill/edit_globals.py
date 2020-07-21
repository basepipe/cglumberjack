import os
import copy
from Qt import QtWidgets, QtCore, QtGui
from cgl.ui.widgets.base import LJDialog
from cgl.ui.widgets.combo import AdvComboBox
from cgl.core.utils.general import load_json

# TODO - I should be pulling globals from an environment variable, this current method is a bit to much
# TODO - Save out to a globals file in the right place for
# TODO - Load Company global edits and change colors accordingly
# TODO - Load Project global edits and change colors accordingly
CGL_CONFIG = os.environ['CGL_CONFIG']
CGL_HOME = os.environ['CGL_HOME']
CGL_ROOT = os.environ['CGL_ROOT']


class EditGlobals(LJDialog):

    def __init__(self):
        LJDialog.__init__(self)
        layout = QtWidgets.QVBoxLayout(self)
        label_company = QtWidgets.QLabel('Company')
        label_company.setStyleSheet('color: blue')

        label_project = QtWidgets.QLabel('Project')
        label_project.setStyleSheet('color: green')
        self.globals_dict = load_json(os.path.join(CGL_CONFIG, 'globals.json'))
        self.edited_globals_dict = copy.deepcopy(self.globals_dict)

        self.temp_dict = {}
        self.company = None
        self.project = None
        self.combo_company = AdvComboBox()
        self.combo_project = AdvComboBox()
        self.tree_widget = QtWidgets.QTreeWidget()
        # self.tree_widget.setSelectionModel()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setColumnWidth(0, 350)
        self.tree_widget.setColumnWidth(0, 400)
        self.tree_widget.setHeaderLabels(['Global', 'Value'])
        self.key = ''
        self.value = ''

        grid = QtWidgets.QGridLayout()

        grid.addWidget(label_company, 0, 0)
        grid.addWidget(self.combo_company, 0, 1)
        grid.addWidget(label_project, 0, 2)
        grid.addWidget(self.combo_project, 0, 3)

        layout.addLayout(grid)
        layout.addWidget(self.tree_widget)

        self.combo_company.currentIndexChanged.connect(self.load_projects)
        self.combo_project.currentIndexChanged.connect(self.project_selected)
        self.tree_widget.clicked.connect(self.on_cell_clicked)
        self.tree_widget.itemChanged.connect(self.on_value_edited)
        self.load_default_globals()
        self.load_companies()

    def create_tree_widget_item(self, globals, key, value=False, parent=None):
        item = QtWidgets.QTreeWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        item.setText(0, key)
        if value:
            item.setText(1, value)
        if parent:
            parent.addChild(item)
        else:
            self.tree_widget.addTopLevelItem(item)
            self.add_children(item, globals[key])
        return item

    def load_default_globals(self):
        for key in self.globals_dict:
            if isinstance(self.globals_dict[key], dict):
                # add it as a top level thingy
                self.create_tree_widget_item(self.globals_dict, key)
            elif isinstance(self.globals_dict[key], list):
                self.create_tree_widget_item(self.globals_dict, key, value=str(self.globals_dict[key]))
            elif isinstance(self.globals_dict[key], str):
                logging.debug('string:', key, self.globals_dict[key])

    def add_children(self, parent_item, children):
        if isinstance(children, dict):
            for key in children:
                if isinstance(children[key], dict):
                    item = self.create_tree_widget_item(children, key, parent=parent_item)
                    self.add_children(item, children[key])
                elif isinstance(children[key], list):
                    item = self.create_tree_widget_item(children, key, value=str(children[key]), parent=parent_item)
                    self.add_children(item, children[key])
                elif isinstance(children[key], str) or isinstance(children[key], int) \
                        or isinstance(children[key], float):
                    self.create_tree_widget_item(children, key, value=str(children[key]), parent=parent_item)
                else:
                    logging.debug(key, 'is type ', type(children[key]))

    def load_projects(self):
        """
        load available projects
        :return:
        """
        company = self.combo_company.currentText()
        if company == 'All':
            self.company = None
        else:
            self.company = company
        self.combo_project.clear()
        if company != 'All':
            proj_dir = os.path.join(CGL_ROOT, company, 'source')
            projects = os.listdir(proj_dir)
            projects.insert(0, 'All')
            self.combo_project.addItems(projects)
        else:
            self.combo_project.clear()
        pass

    def load_companies(self):
        """
        load available compaines
        :return:
        """
        companies = os.listdir(CGL_ROOT)
        companies.insert(0, 'All')
        self.combo_company.addItems(companies)
        pass

    def project_selected(self):
        self.project = self.combo_project.currentText()
        if self.project == 'All':
            self.project = None

    def load_company_globals(self):
        """
        load globals for the selected company
        :return:
        """
        pass

    def load_project_globals(self):
        """
        load globals for the selected project
        :return:
        """
        pass

    def on_cell_clicked(self):
        """

        :return:
        """
        item = self.sender().selectedItems()[0]
        self.key = item.text(0)
        self.value = item.text(1)

    def on_value_edited(self):
        """

        :return:
        """
        item = self.tree_widget.selectedItems()[0]
        if self.key != item.text(0):
            dict_ = self.get_dictionary(item, item.text(0), item.text(1))
            self.set_value(item, item.text(0), item.text(1))
            if self.project:
                self.save_globals(dict_)
                item.setForeground(0, QtGui.QBrush(QtGui.QColor(0, 255, 0)))
                return
            if self.company:
                self.save_globals(dict_)
                item.setForeground(0, QtGui.QBrush(QtGui.QColor(0, 0, 255)))
                return

            self.save_globals(dict_)
            return
        if self.value != item.text(1):
            dict_ = self.get_dictionary(item, item.text(0), item.text(1))
            self.set_value(item, item.text(0), item.text(1))
            if self.project:
                self.save_globals(dict_)
                item.setForeground(1, QtGui.QBrush(QtGui.QColor(0, 255, 0)))
                return
            if self.company:
                self.save_globals(dict_)
                item.setForeground(1, QtGui.QBrush(QtGui.QColor(0, 0, 255)))
                return
            self.save_globals(dict_)
            return

    def save_globals(self, dict_):
        """

        :return:
        """
        if self.project:
            globals_path = os.path.join(CGL_CONFIG, self.company, self.project, 'globals.json')
        elif self.company:
            globals_path = os.path.join(CGL_CONFIG, self.company, 'globals.json')
        else:
            globals_path = os.path.join(CGL_CONFIG, 'globals.json')
        if os.path.exists(globals_path):
            gbals = load_json(globals_path)
            # gbals.update(dict_)
            # save_json(globals_path, gbals)
        else:
            os.makedirs(os.path.dirname(globals_path))
            # save_json(globals_path, dict_)
        logging.debug(globals_path)

    def get_dictionary(self, item, key=False, value=False):
        dict_ = {}
        dict_[key] = value
        parent_item = item.parent()
        if parent_item:
            parent_text = parent_item.text(0)
            dict_ = self.get_dictionary(parent_item, key=parent_text, value=dict_)
            self.temp_dict = dict_
            return dict_
        else:
            self.temp_dict = dict_
            return dict_

    def set_value(self, item, key=False, value=False):
        previous_keys = [key]
        parent_item = item.parent()
        while parent_item:
            parent_key = parent_item.text(0)
            previous_keys.append(parent_key)
        else:
            logging.debug('Editing value on the copied dict')
            logging.debug('keys:', previous_keys, 'value:', value)

    def get_parentage(self, item, prev_text=None, dict_=None):
        if not dict_:
            dict_ = {}
        parent_item = item.parent()
        if parent_item:
            text = parent_item.text(0)
            if prev_text:
                dict_[parent_item.text(0)] = dict_
                text = '%s:%s' % (parent_item.text(0), prev_text)
            text, dict_ = self.get_parentage(parent_item, text, dict_=dict_)
            return text, dict_
            # text = self.get_parentage(item, text)
        else:
            return prev_text, dict_


if __name__ == "__main__":
    from cgl.ui.startup import do_gui_init
    app = do_gui_init()
    td = EditGlobals()

    td.setWindowTitle = 'Edit Globals'
    td.show()
    td.raise_()
    app.exec_()
