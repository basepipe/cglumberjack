import os
import re
import yaml
import copy
import glob
import shutil
from Qt import QtWidgets, QtGui, QtCore
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.base import LJDialog
from core.config import app_config


class PreflightTool(LJDialog):
    def __init__(self, parent=None, company_config=None):
        LJDialog.__init__(self, parent)
        print company_config
        if not company_config:
            if parent:
                print 'test'
                # self.company_config_dir = os.path.dirname(parent.centralWidget().initial_path_object.company_config)
        else:
            self.company_config_dir = company_config

        self.root = self.company_config_dir
        self.software_dict = {}
        self.max_tab = 0
        self.software = ""

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setMovable(True)
        self.tabs.tabnum = 0
        self.tabs.tabBar().tabMoved.connect(lambda: self.reorder_top())

        client_label = QtWidgets.QLabel("%s" % "Software")
        self.software_combo = AdvComboBox()
        add_software_btn = QtWidgets.QPushButton("New Software")
        add_software_btn.clicked.connect(self.add_software)
        self.software_row = QtWidgets.QHBoxLayout()
        self.software_row.addWidget(client_label)
        self.software_row.addWidget(self.software_combo)
        self.software_row.addWidget(add_software_btn)

        self.add_shelf_btn = QtWidgets.QPushButton("Add New Shelf")
        self.add_shelf_btn.clicked.connect(self.add_shelf)

        self.inner = QtWidgets.QVBoxLayout()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.minimumWidth = 1000
        self.layout.minimumHeight = 500
        self.layout.addLayout(self.inner)
        self.layout.addLayout(self.software_row)
        self.layout.addWidget(self.tabs)

        self.setWindowTitle("The Shelf Manager")
        self.setLayout(self.layout)
        self.file = ""
        self.populate_software_combo()
        self.software_combo.currentIndexChanged.connect(self.on_software_selected)

    def add_software(self):
        software, result = QtWidgets.QInputDialog.getText(self, "Add New Software", "New Software Name:")
        if result:
            shelves_yaml = os.path.join(self.root, 'cgl_tools', software, 'shelves.yaml')
            shelves_code_folder = os.path.join(self.root, 'cgl_tools', software, 'shelves')
            if not os.path.exists(shelves_code_folder):
                os.makedirs(shelves_code_folder)

            y = dict()
            y[software.encode('utf-8')] = {}

            with open(shelves_yaml, 'w') as yaml_file:
                yaml.dump(y, yaml_file)

            self.software = software.encode('utf-8')
            self.software_dict[self.software] = shelves_yaml
            self.populate_software_combo()

    def populate_software_combo(self):
        cfg = os.path.join(self.root, 'cgl_tools', '*', 'shelves.yaml')
        yamls = glob.glob(cfg)
        shelves = []
        software_list = ['']
        for each in yamls:
            software_root = os.path.split(each)[0]
            software = os.path.split(software_root)[-1]
            shelves.append(software_root)
            self.software_dict[software] = each

        for key in self.software_dict:
            software_list.append(key)

        self.software_combo.clear()
        self.software_combo.addItems(software_list)

    def on_software_selected(self):
        self.software = self.software_combo.currentText().encode('utf-8')
        if self.software:
            self.software_row.addWidget(self.add_shelf_btn)
            self.file = self.software_dict[self.software]
            self.parse(self.file)

    def select_file(self):
        self.file = str(QtWidgets.QFileDialog.getOpenFileName()[0])

    def add_shelf(self):
        print 'add shelf'


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    mw = PreflightTool(company_config=r'C:\Users\tmiko\Documents\cglumberjack\companies\cgl-fsutests\global.yaml')
    mw.setWindowTitle('Shelf Tool')
    mw.show()
    mw.raise_()
    app.exec_()