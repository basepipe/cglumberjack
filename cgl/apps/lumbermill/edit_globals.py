import os
from Qt import QtWidgets
from cgl.ui.widgets.base import LJDialog
from cgl.ui.widgets.combo import AdvComboBox
from cgl.core.config import app_config


class EditGlobals(LJDialog):

    def __init__(self):
        LJDialog.__init__(self)
        layout = QtWidgets.QVBoxLayout(self)
        label_company = QtWidgets.QLabel('Company')
        label_project = QtWidgets.QLabel('Project')
        self.company = 'All'
        self.project = ''
        self.combo_company = AdvComboBox()
        self.combo_project = AdvComboBox()
        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(['Global', 'Value'])

        grid = QtWidgets.QGridLayout()

        grid.addWidget(label_company, 0, 0)
        grid.addWidget(self.combo_company, 0, 1)
        grid.addWidget(label_project, 0, 2)
        grid.addWidget(self.combo_project, 0, 3)

        layout.addLayout(grid)
        layout.addWidget(self.tree_widget)

        self.combo_company.currentIndexChanged.connect(self.load_projects)
        self.combo_project.currentIndexChanged.connect(self.project_selected)
        self.load_default_globals()
        self.load_companies()

    def load_default_globals(self):
        globals = app_config()
        for key in globals:
            if isinstance(globals[key], dict):
                # add it as a top level thingy
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, key)
                self.tree_widget.addTopLevelItem(item)
                self.add_children(item, globals[key])
            elif isinstance(globals[key], list):
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, key)
                item.setText(1, str(globals[key]))
                self.tree_widget.addTopLevelItem(item)
            elif isinstance(globals[key], unicode):
                print key, globals[key]

    def add_children(self, parent_item, children):
        if isinstance(children, dict):
            for key in children:
                if isinstance(children[key], dict):
                    item = QtWidgets.QTreeWidgetItem()
                    item.setText(0, key)
                    parent_item.addChild(item)
                    self.add_children(item, children[key])
                elif isinstance(children[key], list):
                    item = QtWidgets.QTreeWidgetItem()
                    item.setText(0, key)
                    item.setText(1, str(children[key]))
                    parent_item.addChild(item)
                    self.add_children(item, children[key])
                elif isinstance(children[key], unicode) or isinstance(children[key], int) \
                        or isinstance(children[key], float):
                    item = QtWidgets.QTreeWidgetItem()
                    item.setText(0, key)
                    item.setText(1, str(children[key]))
                    parent_item.addChild(item)
                else:
                    print key, 'is type ', type(children[key])

    def load_projects(self):
        """
        load available projects
        :return:
        """

        directory = r'C:\cgl_root\companies'
        company = self.combo_company.currentText()
        self.company = company
        self.combo_project.clear()
        if company != 'All':
            proj_dir = os.path.join(directory, company, 'source')
            projects = os.listdir(proj_dir)
            self.combo_project.addItems(projects)
        else:
            self.combo_project.clear()
        pass

    def load_companies(self):
        """
        load available compaines
        :return:
        """
        directory = r'C:\cgl_root\companies'
        companies = os.listdir(directory)
        companies.insert(0, 'All')
        self.combo_company.addItems(companies)
        pass

    def project_selected(self):
        self.project = self.combo_project.currentText()

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

    def on_value_edited(self):
        """

        :return:
        """
        print self.project
        print self.company
        # save value to the globals file for the company or the project



if __name__ == "__main__":
    from cgl.ui.startup import do_gui_init
    app = do_gui_init()
    td = EditGlobals()
    td.setWindowTitle = 'Edit Globals'
    td.show()
    td.raise_()
    app.exec_()
