import os
import json
from Qt import QtWidgets, QtCore, QtGui
from cglui.widgets.dialog import InputDialog
from cglui.widgets.base import LJDialog
from cglcore.path import load_style_sheet, get_cgl_tools
from utils import CGLMenu, PreflightStep

class Designer(LJDialog):
    def __init__(self, parent=None, type_=None, menu_path=None, pm_tasks=None):
        LJDialog.__init__(self, parent)
        self.type = type_
        self.cgl_tools = get_cgl_tools()

        self.menu_path = menu_path
        self.software = ''
        self.setWindowTitle('%s Designer' % type_.title())
        self.schema = pm_tasks
        self.task_list = []
        for each in self.schema['long_to_short']['assets']:
            if each not in self.task_list:
                self.task_list.append(each)
        for each in self.schema['long_to_short']['shots']:
            if each not in self.task_list:
                self.task_list.append(each)
        self.task_list.sort()
        self.task_list.insert(0, '')

        # create layouts
        layout = QtWidgets.QVBoxLayout(self)
        tool_bar = QtWidgets.QHBoxLayout()
        self.title_widget = QtWidgets.QWidget()
        title_widget_layout = QtWidgets.QHBoxLayout()
        self.title_widget.setLayout(title_widget_layout)
        grid_layout = QtWidgets.QGridLayout()
        menu_type_row = QtWidgets.QHBoxLayout()


        # create widgets
        self.software_label = QtWidgets.QLabel('Software:')
        self.software_label.setProperty('class', 'title')
        self.software_combo = QtWidgets.QComboBox()
        self.new_software_button = QtWidgets.QPushButton('Add Software')
        self.new_software_button.setProperty('class', 'add_button')
        self.menus = QtWidgets.QTabWidget()
        self.menus.setMovable(True)
        self.title_label = QtWidgets.QLabel()
        self.title_label.setProperty('class', 'ultra_title')
        if self.type == 'menus':
            self.add_menu_button = QtWidgets.QPushButton('add menu')
        elif self.type == 'preflights':
            self.add_menu_button = QtWidgets.QPushButton('add preflight')
        else:
            self.add_menu_button = QtWidgets.QPushButton('add %s' % self.type)
        self.add_menu_button.setProperty('class', 'add_button')
        # self.save_menu_button = QtWidgets.QPushButton('save menu')
        # self.save_menu_button.setProperty('class', 'add_button')
        self.title_widget.hide()


        # layout the GUI
        title_widget_layout.addWidget(self.title_label)
        title_widget_layout.addWidget(self.add_menu_button)
        title_widget_layout.addStretch(1)
        # title_widget_layout.addWidget(self.save_menu_button)
        grid_layout.addWidget(self.software_label, 0, 0)
        grid_layout.addWidget(self.software_combo, 0, 1)
        grid_layout.addWidget(self.new_software_button, 0, 2)


        tool_bar.addLayout(grid_layout)
        tool_bar.addStretch(1)
        layout.addLayout(tool_bar)
        layout.addWidget(self.title_widget)
        layout.addLayout(menu_type_row)
        layout.addWidget(self.menus)

        # SIGNALS AND SLOTS
        self.add_menu_button.clicked.connect(self.on_add_menu_clicked)
        self.new_software_button.clicked.connect(self.on_new_software_clicked)

        # Load the Menu Designer
        self.load_software()
        self.software_combo.currentIndexChanged.connect(self.update_menu_path)

    def load_software(self):
        self.software_label.show()
        self.software_combo.show()
        self.new_software_button.show()
        self.software_combo.clear()

        dir_ = self.cgl_tools
        if os.path.exists(dir_):
            softwares = os.listdir(dir_)
            for s in softwares:
                if '.' not in s:
                    self.software_combo.addItem(s)
        self.software = self.software_combo.currentText()
        self.update_menu_path()

    def update_menu_path(self):
        self.software = self.software_combo.currentText()
        self.menu_path = os.path.join(self.cgl_tools, self.software, '%s.cgl' % self.type)
        self.load_menus()

    def on_add_menu_clicked(self):
        dialog = InputDialog(title='Add %s' % self.type, message='Choose Task to Create a Preflight For',
                             line_edit=False, regex='[a-zA-Z0-0]{3,}', combo_box_items=self.task_list,
                             name_example='Only letters & Numbers Allowed in Button Names')
        dialog.exec_()
        if dialog.button == 'Ok':
            long_name = dialog.combo_box.currentText()
            if long_name in self.schema['long_to_short']['assets']:
                menu_name = self.schema['long_to_short']['assets'][long_name]
            elif long_name in self.schema['long_to_short']['shots']:
                menu_name = self.schema['long_to_short']['shots'][long_name]
            else:
                menu_name = long_name
            cgl_file = self.menu_path
            new_menu = CGLMenu(software=self.software, menu_name=menu_name, menu=[],
                               menu_path=cgl_file, menu_type=self.type)
            index = self.menus.addTab(new_menu, menu_name)
            self.menus.setCurrentIndex(index)

    def on_add_preflight_clicked(self):
        dialog = InputDialog(title='Add %s' % self.type, message='Create A Preflight \n(task names will automatically '
                                                                 'be connected to task publishes)', line_edit=False,
                             regex='[a-zA-Z0-0]{3,}', combo_box_items=self.task_list,
                             name_example='Only letters & Numbers Allowed in Button Names')
        dialog.exec_()
        if dialog.button == 'Ok':
            long_name = dialog.combo_box.currentText()
            if long_name in self.schema['long_to_short']['assets']:
                menu_name = self.schema['long_to_short']['assets'][long_name]
            elif long_name in self.schema['long_to_short']['shots']:
                menu_name = self.schema['long_to_short']['shots'][long_name]
            cgl_file = self.menu_path
            new_menu = CGLMenu(software=self.software, menu_name=menu_name, menu=[],
                               menu_path=cgl_file, menu_type=self.type)
            index = self.menus.addTab(new_menu, menu_name)
            self.menus.setCurrentIndex(index)

    def load_menus(self):
        menu_dict = {}
        self.menus.clear()
        self.title_widget.show()
        self.title_label.setText('%s %s' % (self.software_combo.currentText(), self.type))
        self.software = self.software_combo.currentText()
        if os.path.exists(self.menu_path):
            menu_dict = self.load_json(self.menu_path)
        if menu_dict:
            for i in range(len(menu_dict[self.software])+1):
                for menu in menu_dict[self.software]:
                    if i == menu_dict[self.software][menu]['order']:
                        buttons = CGLMenu(software=self.software, menu_name=menu, menu=menu_dict[self.software][menu],
                                          menu_path=self.menu_path, menu_type=self.type)
                        self.menus.addTab(buttons, menu)

    def on_new_software_clicked(self):
        dialog = InputDialog(title='Add Software', message='Enter or Choose Software',
                             combo_box_items=['', 'lumbermill', 'nuke', 'maya'],
                             regex='[a-zA-Z0-0]{3,}', name_example='Only letters & Numbers Allowed Software Names')
        dialog.exec_()
        if dialog.button == 'Ok':
            software_name = dialog.combo_box.currentText()
            folder = os.path.join(self.cgl_tools, software_name)
            os.makedirs(folder)
            self.software_combo.addItem(software_name)
            num = self.software_combo.count()
            self.software_combo.setCurrentIndex(num)

    def save_menus(self):
        menu_dict = {}
        for mi in range(self.menus.count()):
            menu_name = self.menus.tabText(mi)
            menu = self.menus.widget(mi)
            menu_dict[menu_name] = {}
            menu_dict[menu_name]['order'] = mi+1
            for bi in range(menu.buttons.count()):
                button_name = menu.buttons.tabText(bi)
                button_widget = menu.buttons.widget(bi)
                if self.type == 'preflights':
                    menu_dict[menu_name][button_name] = {
                        'module': button_widget.command_line_edit.text(),
                        'label': button_widget.label_line_edit.text(),
                        'order': bi + 1,
                        'required': button_widget.required_line_edit.text()
                    }
                else:
                    menu_dict[menu_name][button_name] = {
                                                         'module': button_widget.command_line_edit.text(),
                                                         'label': button_widget.label_line_edit.text(),
                                                         'order': bi+1
                                                         }

                self.save_code(menu_name, button_widget)
        json_object = {self.software: menu_dict}
        self.save_json(self.menu_path, json_object)

    def save_code(self, menu_name, button_widget):
        button_name = button_widget.name
        code = button_widget.code_text_edit.document().toPlainText()
        button_file = os.path.join(self.cgl_tools, self.software, self.type, menu_name,
                                   "%s.py" % button_name)
        dir_ = os.path.dirname(button_file)
        if not os.path.exists(dir_):
            os.makedirs(dir_)
        self.make_init_for_folders_in_path(dir_)
        if button_widget.do_save:
            with open(button_file, 'w+') as x:
                x.write(code)
            button_widget.do_save = False

    def make_init_for_folders_in_path(self, folder):
        config = self.cgl_tools.replace('\\', '/')

        folder = folder.replace('\\', '/')
        folder = folder.replace(config, '')
        parts = folder.split('/')
        if '' in parts:
            parts.remove('')
        string = config
        for p in parts:
            if not ':' in p:
                if '.' not in p:
                    string = '%s/%s' % (string, p)
                    init = '%s/__init__.py' % string
                    if not os.path.exists(init):
                        self.make_init(os.path.dirname(init))

    def make_init(self, folder):
        if '*' not in folder:
            with open(os.path.join(folder, '__init__.py'), 'w+') as i:
                i.write("")

    def save_json(self, filepath, data):
        self.make_init_for_folders_in_path(filepath)
        with open(filepath, 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)

    @staticmethod
    def load_json(filepath):
        with open(filepath) as jsonfile:
            data = json.load(jsonfile)
        return data

    def closeEvent(self, event):
        self.save_menus()


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    mw = Designer(type_='preflights')
    #mw = Designer(type_='menus')
    mw.setWindowTitle('Preflight Designer')
    mw.setMinimumWidth(1200)
    mw.setMinimumHeight(500)
    mw.show()
    mw.raise_()
    style_sheet = load_style_sheet()
    app.setStyleSheet(style_sheet)
    app.exec_()
