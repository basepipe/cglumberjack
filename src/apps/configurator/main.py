import yaml
import os
from Qt import QtWidgets, QtGui, QtCore
from core.config import app_config, UserConfig
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.base import LJDialog
import copy


class NewProjectWindow(LJDialog):
    def __init__(self, parent=None):
        LJDialog.__init__(self, parent)
        # Environment Stuff
        self.setWindowTitle("Name of New Project")
        self.root_path = app_config()['paths']['root']
        self.v_layout = QtWidgets.QVBoxLayout(self)
        self.newclient_row = QtWidgets.QHBoxLayout(self)
        self.newclient_row2 = QtWidgets.QHBoxLayout(self)
        self.message_label = QtWidgets.QLabel("%s" % "Create New Client and Project")
        self.newclient_label = QtWidgets.QLabel("%s" % "New Client Name")
        self.newclient_lineedit = QtWidgets.QLineEdit()
        self.newclient_label2 = QtWidgets.QLabel("%s" % "New Project Name")
        self.newclient_lineedit2 = QtWidgets.QLineEdit()
        self.newclient_row.addWidget(self.newclient_label)
        self.newclient_row.addWidget(self.newclient_lineedit)
        self.newclient_row2.addWidget(self.newclient_label2)
        self.newclient_row2.addWidget(self.newclient_lineedit2)

        self.buttons = QtWidgets.QHBoxLayout(self)
        self.buttonA = QtWidgets.QPushButton('OK')
        self.buttons.addWidget(self.buttonA)
        self.v_layout.addWidget(self.message_label)
        self.v_layout.addLayout(self.newclient_row)
        self.v_layout.addLayout(self.newclient_row2)
        self.v_layout.addLayout(self.buttons)


class Configurator(LJDialog):
    def __init__(self, parent=None, company=None):
        LJDialog.__init__(self, parent)
        self.company = company
        self.tabs = QtWidgets.QTabWidget()

        company_label = QtWidgets.QLabel("%s" % "Company")
        self.company_combo = AdvComboBox()
        company_row = QtWidgets.QHBoxLayout()
        company_row.addWidget(company_label)
        company_row.addWidget(self.company_combo)

        project_label = QtWidgets.QLabel("%s" % "Project")
        self.project_combo = AdvComboBox()
        project_row = QtWidgets.QHBoxLayout()
        project_row.addWidget(project_label)
        project_row.addWidget(self.project_combo)

        config_label = QtWidgets.QLabel("%s" % 'Config Directory')
        self.config_line_edit = QtWidgets.QLineEdit()
        config_choose = QtWidgets.QToolButton()
        config_choose.setText('...')
        # config_label.setMaximumWidth(250)
        config_row = QtWidgets.QHBoxLayout()
        config_row.addWidget(config_label)
        config_row.addWidget(self.config_line_edit)
        config_row.addWidget(config_choose)
        self.current_path = os.path.dirname(UserConfig().user_config_path)
        self.user_config_path = os.path.dirname(UserConfig().user_config_path)
        self.config_line_edit.setText(self.user_config_path)

        self.inner = QtGui.QVBoxLayout()
        self.layout = QtGui.QVBoxLayout()
        self.layout.addLayout(self.inner)
        self.layout.addLayout(config_row)
        self.layout.addLayout(company_row)
        self.layout.addLayout(project_row)
        self.layout.addWidget(self.tabs)

        import_btn = QtWidgets.QPushButton("Import")
        save_btn = QtWidgets.QPushButton("Save")



        button_row2 = QtWidgets.QHBoxLayout()
        button_row2.addWidget(import_btn)
        button_row2.addWidget(save_btn)

        self.layout.addLayout(button_row2)
        self.setWindowTitle("LUMBERJACK CONFIG")
        self.setLayout(self.layout)
        self.file = ""
        self.load_companies()

        import_btn.clicked.connect(self.select_file)
        self.company_combo.currentIndexChanged.connect(self.load_projects)
        self.project_combo.currentIndexChanged.connect(self.load_file)

    def load_companies(self):
        self.current_path = os.path.join(self.config_line_edit.text(), 'companies')
        companies = os.listdir(self.current_path)
        companies.insert(0, '')
        self.company_combo.addItems(companies)
        if self.company:
            index = self.company_combo.findText(self.company)
            if index != -1:
                self.company_combo.setCurrentIndex(index)
                self.load_projects()

    def load_projects(self):
        ignore = ['cgl_tools']
        self.current_path = os.path.join(self.current_path, self.company_combo.currentText())
        projects = os.listdir(self.current_path)
        for each in ignore:
            if each in projects:
                projects.remove(each)
        projects.insert(0, '')
        self.project_combo.addItems(projects)

    def load_file(self):
        project = self.project_combo.currentText()
        if project == '':
            return
        if project == 'global.yaml':
            self.current_path = os.path.join(self.current_path, project)
        else:
            self.current_path = os.path.join(os.path.dirname(self.current_path), project, 'global.yaml')
        self.file = self.current_path
        # TODO - need to clear everything
        print 'Loading Globals: %s' % self.file
        self.parse(self.file)

    def select_file(self):
        self.file = str(QtWidgets.QFileDialog.getOpenFileName()[0])
        #print(self.file)
        self.parse(self.file)

    def parse(self, filename):
        self.yamlfile = filename
        with open(filename, 'r') as stream:
            f = yaml.load(stream)

        for tabs_dict in f:
            tab = QtWidgets.QWidget()
            tab.setLayout(self.generate_tab(f[tabs_dict], tabs_dict))
            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setWidget(tab)
            scroll_area.setWidgetResizable(True)
            self.tabs.addTab(scroll_area, str(tabs_dict))

    def generate_tab(self, tabs_dict, tabname):
        layout = QtWidgets.QVBoxLayout()
        self.tn = tabname

        for x in tabs_dict:
            if type(tabs_dict[x]) is unicode:
                #print(x, tabs_dict[x].encode('utf-8'))
                layout.addLayout(self.get_label_row(x, tabs_dict[x].encode('utf-8'), [x]))
            elif type(tabs_dict[x]) is not dict:
                #print(x, str(tabs_dict[x]))
                layout.addLayout(self.get_label_row(x, str(tabs_dict[x]), [x]))

        for x in tabs_dict:
            if type(tabs_dict[x]) is dict:
                layout.addWidget(QtWidgets.QLabel("<b>%s<b>" % x))
                widget = QtWidgets.QWidget()
                new_layout = QtWidgets.QVBoxLayout()
                layout.addWidget(widget)
                widget.setLayout(self.iterate_over_dict(tabs_dict[x], new_layout, [x]))

        return layout

    def iterate_over_dict(self, x, layout, p):
        for y in x:
            print(y)
            if type(x[y]) is dict:
                widget = QtWidgets.QWidget()
                new_layout = QtWidgets.QVBoxLayout()
                layout.addWidget(QtWidgets.QLabel("<b>  %s<b>" % y))
                layout.addWidget(widget)
                p.append(y)
                widget.setLayout(self.iterate_over_dict(x[y], new_layout, p))
            else:
                p.append(y)
                #print(self.tn)
                #print(p)
                layout.addLayout(self.get_label_row("\t"+y, str(x[y]), p))
            p.pop()
        layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        return layout

    def save_change(self, edit):
        print(edit.dict_path, edit.text().encode('utf-8'))
        print(len(edit.dict_path))

        p = copy.copy(edit.dict_path)
        t = edit.text().encode('utf-8')

        with open(self.file, 'r') as stream:
            y = yaml.load(stream)

        #y = yml[p.pop(0)]
        #j = copy.copy(y)

        if len(p) == 2:
            y[p[0]][p[1]] = t

        if len(p) == 3:
            y[p[0]][p[1]][p[2]] = t

        if len(p) == 4:
            y[p[0]][p[1]][p[2]][p[3]] = t

        if len(p) == 5:
            y[p[0]][p[1]][p[2]][p[3]][p[4]] = t

        if len(p) == 6:
            y[p[0]][p[1]][p[2]][p[3]][p[4]][p[5]] = t

        if len(p) == 7:
            y[p[0]][p[1]][p[2]][p[3]][p[4]][p[5]][p[6]] = t

        if len(p) == 8:
            y[p[0]][p[1]][p[2]][p[3]][p[4]][p[5]][p[6]][p[7]] = t

        if len(p) == 9:
            y[p[0]][p[1]][p[2]][p[3]][p[4]][p[5]][p[6]][p[7]][p[8]] = t

        with open(self.file, 'w') as yaml_file:
            yaml.dump(y, yaml_file)

    def get_label_row(self, lab, ed, path):
        label = QtWidgets.QLabel("%s" % lab)
        label.setMinimumWidth(250)
        edit = QtWidgets.QLineEdit()
        edit.setText(ed)
        row = QtWidgets.QHBoxLayout()
        edit.dict_path = copy.copy(path)
        edit.dict_path.insert(0, self.tn)
        edit.textChanged[str].connect(lambda: self.save_change(edit))
        row.addWidget(label)
        row.addWidget(edit)
        print(edit.dict_path)
        return row

    def get_edit_row(self):
        edit = QtWidgets.QLineEdit()
        edit2 = QtWidgets.QLineEdit()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(edit)
        row.addWidget(edit2)
        return row


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    mw = Configurator()
    mw.setWindowTitle('Configurator')
    mw.show()
    mw.raise_()
    app.exec_()