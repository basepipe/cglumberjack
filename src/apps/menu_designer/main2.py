import os
import re
import yaml
import copy
import glob
import shutil
from Qt import QtWidgets, QtGui, QtCore
from cglui.widgets.base import LJDialog
from cglui.widgets.text import Highlighter
from cglcore.config import app_config

GUI_DICT = {'shelves.yaml': ['button name', 'command', 'icon', 'order', 'annotation', 'label'],
            'preflights.yaml': ['order', 'module', 'name', 'required'],
            'menus.yaml': ['order', 'name']}

class MenuDesigner(LJDialog):
    def __init__(self, parent=None):
        LJDialog.__init__(self, parent)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setMovable(True)
        self.tabs.tabnum = 0
        try:
            self.company_config_dir = os.path.dirname(parent.centralWidget().path_object.company_config)
        except AttributeError:
            self.company_config_dir = r'C:\Users\tmiko\Documents\cglumberjack\companies\cgl-fsutests'
        self.root = self.company_config_dir
        self.software_dict = {}
        self.max_tab = 0
        self.software = ""
        self.current_type = None

        # main top row
        software_label = QtWidgets.QLabel("%s" % "Software")
        self.software_combo = QtWidgets.QComboBox()
        self.type_label = QtWidgets.QLabel("%s" % "System")
        self.type_combo = QtWidgets.QComboBox()
        self.add_software_btn = QtWidgets.QPushButton("New Software")
        self.add_shelf_btn = QtWidgets.QPushButton("Add New Shelf")
        self.type_label.hide()
        self.type_combo.hide()
        self.software_row = QtWidgets.QHBoxLayout()
        self.software_row.addWidget(software_label)
        self.software_row.addWidget(self.software_combo)
        self.software_row.addWidget(self.type_label)
        self.software_row.addWidget(self.type_combo)
        self.software_row.addWidget(self.add_software_btn)
        self.software_row.addWidget(self.add_shelf_btn)
        self.software_row.addStretch(1)

        self.inner = QtWidgets.QVBoxLayout()
        self.layout = QtWidgets.QVBoxLayout()

        self.layout.minimumWidth = 1000
        self.layout.minimumHeight = 500
        self.layout.addLayout(self.inner)
        self.layout.addLayout(self.software_row)
        self.layout.addWidget(self.tabs)

        self.setWindowTitle("Menu Designer")
        self.setLayout(self.layout)
        self.file = ""
        self.populate_software_combo()

        self.add_software_btn.clicked.connect(self.add_software)
        self.software_combo.currentIndexChanged.connect(self.on_software_selected)
        self.type_combo.currentIndexChanged.connect(self.on_type_selected)
        self.add_shelf_btn.clicked.connect(self.add_shelf)

        # connections
        self.tabs.tabBar().tabMoved.connect(lambda: self.reorder_top())

    def add_software(self):
        software, result = QtWidgets.QInputDialog.getText(self, "Add New Software", "New Software Name:")
        if not os.path.exists(os.path.join(self.root, '__init__.py')):
            self.make_init(self.root)

        if result:
            software_code_folder = os.path.join(self.root, 'cgl_tools', software)
            if not os.path.exists(software_code_folder):
                os.makedirs(software_code_folder)
            if not os.path.exists(os.path.join(software_code_folder, '__init__.py')):
                self.make_init(software_code_folder)
            for each in ['shelves', 'menus', 'preflights']:
                shelves_yaml = os.path.join(self.root, 'cgl_tools', software, '%s.yaml' % each)

                shelves_code_folder = os.path.join(self.root, 'cgl_tools', software, each)

                if not os.path.exists(shelves_code_folder):
                    os.makedirs(shelves_code_folder)

                if not os.path.exists(os.path.join(self.root, 'cgl_tools', '__init__.py')):
                    self.make_init(os.path.join(os.path.join(self.root, 'cgl_tools')))

                if not os.path.exists(os.path.join(shelves_code_folder, '__init__.py')):
                    self.make_init(shelves_code_folder)

                y = dict()
                y[software.encode('utf-8')] = {}

                with open(shelves_yaml, 'w') as yaml_file:
                    yaml.dump(y, yaml_file)

                self.software = software.encode('utf-8')
                self.software_dict[self.software] = shelves_yaml
                self.populate_software_combo()

    def populate_software_combo(self):
        self.software_combo.clear()
        cfg = os.path.join(self.root, 'cgl_tools', '*')
        yamls = glob.glob(cfg)
        shelves = []
        software_list = ['']
        for each in yamls:
            if '.' not in each:
                if 'icons' not in each:
                    software_root = os.path.split(each)[0]
                    software = os.path.split(each)[-1]
                    shelves.append(software_root)
                    self.software_combo.addItem(software)
        if self.software_combo.count() > -1:
            self.on_software_selected()

    def on_software_selected(self):
        self.software = self.software_combo.currentText().encode('utf-8')
        if self.software:
            self.populate_types()
            self.type_combo.show()

    def populate_types(self):
        self.type_combo.clear()
        cfg = os.path.join(self.root, 'cgl_tools', self.software_combo.currentText(), '*.yaml')
        yamls = glob.glob(cfg)
        for each in yamls:
            self.type_combo.addItem(os.path.split(each)[-1])
        if self.type_combo.count() > -1:
            self.on_type_selected()

    def on_type_selected(self):
        print 'made it'
        self.clear_tabs()
        self.file = os.path.join(self.root, 'cgl_tools', self.software_combo.currentText(), self.type_combo.currentText())
        file_, ext_ = os.path.splitext(self.file)
        file_ = os.path.split(file_)[-1]
        if self.type_combo.currentText():
            self.current_type, ext = os.path.splitext(self.type_combo.currentText())
            self.parse(self.file, type=self.type_combo.currentText())
            #self.add_software_btn.show()
            #self.add_shelf_btn.show()
            #self.add_shelf_btn.setText('Add New %s' % file_)

    def select_file(self):
        self.file = str(QtWidgets.QFileDialog.getOpenFileName()[0])

    def clear_tabs(self):
        for x in range(0, self.tabs.tabnum):
            self.tabs.removeTab(0)
        self.tabs.tabnum = 0

    def parse(self, filename, type='shelves.yaml'):
        self.clear_tabs()
        f = self.load_yaml(filename)
        # create

    def load_yaml(self, filepath):
        with open(filepath, 'r') as stream:
            f = yaml.load(stream)
            if len(f) == 0:
                return
            else:
                return f

    def add_shelf(self):
        shelf_name, result = QtWidgets.QInputDialog.getText(self, "Add a New Shelf", "New Shelf Name:")
        if result:
            with open(self.file, 'r') as yaml_file:
                shelf = yaml.load(yaml_file)

            self.tabs.setTabText(self.tabs.tabnum, shelf_name.encode('utf-8'))
            self.tabs.tabnum += 1

            shelf[self.software][shelf_name.encode('utf-8')] = {"order": self.tabs.tabnum}

            with open(self.file, 'w') as yaml_file:
                yaml.dump(shelf, yaml_file)

            software_folder, shelves_folder, shelf_name_folder = self.get_software_folder(self.software, shelf_name)
            if not os.path.exists(shelf_name_folder):
                os.makedirs(shelf_name_folder)

            self.make_init(software_folder)
            self.make_init(shelves_folder)
            self.make_init(shelf_name_folder)

            self.parse(self.file)


class Menu(QtWidgets.QWidget):
    def __init__(self, parent=None):
        Menu.__init__(self, parent)
        print 'this'


class MenuButton(QtWidgets.QWidget):
    def __init__(self, parent=None, ):
        MenuButton.__init__(self, parent)
        self.setLayout()

    def generate_buttons(self, tabs_dict, tabname):
        """
        Creates the "Child Level" tabs that represent individual shelf buttons, or individual preflights.
        :param tabs_dict:
        :param tabname:
        :return:
        """
        newtabs = QtWidgets.QTabWidget()
        newtabs.setMovable(True)
        newtabs.tabnum = 0
        newtabs.tabBar().tabMoved.connect(lambda: self.reorder_bottom(newtabs))

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(newtabs)

        order = 1
        olen = 1

        for x in tabs_dict:
            if type(tabs_dict[x]) is dict:
                olen += 1
        k = 1
        for i in range(0, olen):
            for x in tabs_dict:
                if str(x) != "order" and str(x) != "active":
                    if tabs_dict[x]["order"] == i:
                        tab = QtWidgets.QWidget()
                        tab.setLayout(self.generate_details(newtabs, tabs_dict[x], x, newtabs, i))
                        scroll_area = QtWidgets.QScrollArea()
                        scroll_area.setWidget(tab)
                        scroll_area.setWidgetResizable(True)
                        newtabs.addTab(scroll_area, str(x))
                        newtabs.tabnum += 1
                        if newtabs.tabnum > self.max_tab:
                            self.max_tab = newtabs.tabnum
                        root = app_config()['paths']['code_root']
                        if "icon" in tabs_dict[x]:
                            icon_path = os.path.join(self.company_config_dir, 'cgl_tools', tabs_dict[x]["icon"])
                            if os.path.exists(icon_path):
                                newtabs.setTabIcon(int(tabs_dict[x]["order"]) - 1, QtGui.QIcon(icon_path))
                                newtabs.setIconSize(QtCore.QSize(24, 24))

        scroll_area = self.make_new_button(newtabs, tabname, newtabs.tabnum)
        scroll_area.setWidgetResizable(True)
        newtabs.addTab(scroll_area, str("+"))
        newtabs.tabnum += 1
        if newtabs.tabnum > self.max_tab:
            self.max_tab = newtabs.tabnum

        # TODO - it'd be nice to have this number derived from how many tabs in the shelf with the most tabs. sizeHint()
        self.tabs.setMinimumWidth(1300)
        self.tabs.setMinimumHeight(800)

        return layout


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    mw = MenuDesigner()
    mw.setWindowTitle('Tool Shed')
    mw.show()
    mw.raise_()
    app.exec_()