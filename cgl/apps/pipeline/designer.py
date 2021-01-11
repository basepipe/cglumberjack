import os
import json
import logging
from cgl.plugins.Qt import QtWidgets
from cgl.ui.widgets.dialog import InputDialog
from cgl.ui.widgets.base import LJDialog
from cgl.core.utils.general import load_style_sheet
from cgl.apps.pipeline.utils import CGLMenu, get_menu_path, get_button_path
from cgl.core.config.config import ProjectConfig


class Designer(LJDialog):
    def __init__(self, parent=None, type_=None, menu_path=None, pm_tasks=None, cfg=None, path_object=None):
        LJDialog.__init__(self, parent)
        self.type = type_
        if cfg:
            self.cfg = cfg
        else:
            print('Designer')
            self.cfg = ProjectConfig(path_object)
        self.cgl_tools = self.cfg.cookbook_folder
        self.singular = ''

        self.menu_path = menu_path
        self.software = ''
        self.setWindowTitle("Alchemist's Cookbook")
        self.schema = pm_tasks
        self.task_list = []
        try:
            for each in self.schema['long_to_short']['assets']:
                if each not in self.task_list:
                    self.task_list.append(each)
            for each in self.schema['long_to_short']['shots']:
                if each not in self.task_list:
                    self.task_list.append(each)
        except TypeError:
            print('Problems found in your globals "schema"')
            return
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
        self.menu_type_label = QtWidgets.QLabel('Recipe Type:')
        self.menu_type_label.setProperty('class', 'title')
        self.menu_type_combo = QtWidgets.QComboBox()
        self.menu_type_combo.addItems(['', 'menus', 'shelves', 'pre_publish', 'pre_render', 'tasks'])

        self.new_software_button = QtWidgets.QPushButton('Add Software')
        self.new_software_button.setProperty('class', 'add_button')
        self.menus = QtWidgets.QTabWidget()
        self.menus.setMovable(True)
        self.title_label = QtWidgets.QLabel()
        self.title_label.setProperty('class', 'ultra_title')
        self.add_menu_button = QtWidgets.QPushButton('add')
        self.delete_menu_button = QtWidgets.QPushButton('delete')
        self.add_menu_button.setProperty('class', 'add_button')
        self.delete_menu_button.setProperty('class', 'add_button')

        # self.save_menu_button = QtWidgets.QPushButton('save menu')
        # self.save_menu_button.setProperty('class', 'add_button')
        self.title_widget.hide()
        # layout the GUI
        title_widget_layout.addWidget(self.title_label)
        title_widget_layout.addWidget(self.add_menu_button)
        title_widget_layout.addWidget(self.delete_menu_button)
        title_widget_layout.addStretch(1)
        # title_widget_layout.addWidget(self.save_menu_button)
        grid_layout.addWidget(self.software_label, 0, 0)
        grid_layout.addWidget(self.software_combo, 0, 1)
        grid_layout.addWidget(self.new_software_button, 0, 2)
        grid_layout.addWidget(self.menu_type_label, 1, 0)
        grid_layout.addWidget(self.menu_type_combo, 1, 1)
        tool_bar.addLayout(grid_layout)
        tool_bar.addStretch(1)
        layout.addLayout(tool_bar)
        layout.addWidget(self.title_widget)
        layout.addLayout(menu_type_row)
        layout.addWidget(self.menus)

        # SIGNALS AND SLOTS
        self.add_menu_button.clicked.connect(self.on_add_menu_clicked)
        self.delete_menu_button.clicked.connect(self.on_delete_menu_clicked)
        self.new_software_button.clicked.connect(self.on_new_software_clicked)

        # Load the Menu Designer
        self.load_software()
        self.software_combo.currentIndexChanged.connect(self.update_menu_path)
        self.menu_type_combo.currentIndexChanged.connect(self.update_menu_path)

    def on_delete_menu_clicked(self):
        index = self.menus.currentIndex()
        menu_name = self.menus.tabText(index)
        dialog = InputDialog(title='Delete %s?' % menu_name,
                             message='Are you sure you want to delete %s' % menu_name)
        dialog.exec_()
        if dialog.button == 'Ok':
            import shutil
            self.menus.removeTab(index)
            menu_folder = os.path.join(self.cgl_tools, self.software, self.menu_type_combo.currentText(), menu_name)
            print('Removing folder: {}'.format(menu_folder))
            shutil.rmtree(menu_folder)

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
                    if '__' not in s:
                        self.software_combo.addItem(s)
        self.software = self.software_combo.currentText()
        self.update_menu_path()

    def update_menu_path(self):
        self.software = self.software_combo.currentText()
        self.type = self.menu_type_combo.currentText()
        if self.type == 'tasks':
            self.add_menu_button.hide()
            self.delete_menu_button.hide()
        else:
            self.add_menu_button.show()
            self.delete_menu_button.show()
        self.get_singular(self.type)
        if self.type:
            self.menu_path = os.path.join(self.cgl_tools, self.software, '%s.cgl' % self.type)
            self.add_menu_button.setText('add %s' % self.singular)
            self.delete_menu_button.setText('delete %s' % self.singular)
            if not os.path.exists(self.menu_path):
                self.create_empty_menu()
            self.load_menus()

    def get_singular(self, type_):
        if self.type == 'shelves':
            self.singular = 'shelf'
        elif self.type == 'menus':
            self.singular = 'menu'
        elif self.type == 'pre_publish':
            self.singular = 'pre_publish'
        elif self.type == 'pre_render':
            self.singular = 'pre_render'
        elif self.type == 'tasks':
            self.singular = 'task'
        elif self.type == 'context-menus':
            self.singular = 'context-menu'
        else:
            self.singular = 'not defined'

    def on_add_menu_clicked(self):
        if self.type == 'pre_publish' or self.type == 'context-menus' or self.type == 'pre_render':
            if self.type == 'pre_publish':
                singular = 'Pre-Publish'
            elif self.type == 'pre_render':
                singular = 'Pre-Render'
            elif self.type == 'context-menus':
                singular = 'Context Menu'
            elif self.type == 'shelves':
                singular = 'Shelf'
            dialog = InputDialog(title='Add %s' % singular,
                                 message='Choose Task to Create a %s Recipe For\n '
                                         'Or Type to Create Your Own' % singular,
                                 line_edit=False, combo_box_items=self.task_list, regex='[a-zA-Z]',
                                 name_example='Only letters & Numbers Allowed in %s Names' % singular)
            dialog.exec_()
            if dialog.button == 'Ok':
                long_name = dialog.combo_box.currentText()
                if long_name in self.schema['long_to_short']['assets']:
                    menu_name = self.schema['long_to_short']['assets'][long_name]
                elif long_name in self.schema['long_to_short']['shots']:
                    menu_name = self.schema['long_to_short']['shots'][long_name]
                else:
                    menu_name = long_name
                self.do_add_menu(menu_name)
        elif self.type == 'menus' or self.type == 'shelves':
            dialog = InputDialog(title='Add %s' % self.singular, message='Create a Custom %s' % self.singular,
                                 line_edit=True)
            dialog.exec_()
            if dialog.button == 'Ok':
                menu_name = dialog.line_edit.text()
                self.do_add_menu(menu_name)
        elif self.type == 'tasks':
            singular = 'Task'
            dialog = InputDialog(title='Add %s' % singular,
                                 message='Choose Task to Create a %s Recipe For\n '
                                         'Or Type to Create Your Own' % singular,
                                 line_edit=False, combo_box_items=self.task_list, regex='[a-zA-Z]',
                                 name_example='Only letters & Numbers Allowed in %s Names' % singular)
            dialog.exec_()
            if dialog.button == 'Ok':
                long_name = dialog.combo_box.currentText()
                task_name = ''
                if long_name in self.schema['long_to_short']['assets']:
                    task_name = self.schema['long_to_short']['assets'][long_name]
                elif long_name in self.schema['long_to_short']['shots']:
                    task_name = self.schema['long_to_short']['shots'][long_name]
                else:
                    task_name = long_name
                if task_name:
                    self.do_add_task(task_name)

    def do_add_menu(self, menu_name):
        # remove spaces from the end of the name:
        if menu_name.endswith(' '):
            menu_name = menu_name.strip()
        if ' ' in menu_name:
            menu_name = menu_name.replace(' ', '_')
        cgl_file = self.menu_path
        menu_folder = get_menu_path(self.software, menu_name, menu_file=False, menu_type=self.type, cfg=self.cfg)
        new_menu = CGLMenu(parent=self, software=self.software, menu_name=menu_name, menu=[],
                           menu_path=cgl_file, menu_type=self.type, cfg=self.cfg)
        index = self.menus.addTab(new_menu, menu_name)
        self.menus.setCurrentIndex(index)
        if not os.path.exists(menu_folder):
            os.makedirs(menu_folder)
            # self.make_init_for_folders_in_path(menu_folder)
        self.save_menus()
        if self.software == 'blender':
            if self.type == 'menus':
                from cgl.plugins.blender.utils import create_menu_file
                create_menu_file(menu_name,self.cfg)

    def load_menus(self):
        menu_dict = {}
        self.menus.clear()
        self.title_widget.show()
        self.title_label.setText('%s %s' % (self.software_combo.currentText(), self.type))
        self.software = self.software_combo.currentText()
        # if self.sender().currentText() == 'tasks':
        #     self.load_tasks()
        #     return
        if os.path.exists(self.menu_path):
            menu_dict = self.load_json(self.menu_path)
        if menu_dict:
            if self.software in menu_dict:
                if isinstance(menu_dict[self.software], dict):
                    for i in range(len(menu_dict[self.software])+1):
                        for menu in menu_dict[self.software]:
                            if i == menu_dict[self.software][menu]['order']:
                                buttons = CGLMenu(parent=self, software=self.software, menu_name=menu,
                                                  menu=menu_dict[self.software][menu],
                                                  menu_path=self.menu_path, menu_type=self.type, cfg=self.cfg)
                                buttons.menu_button_save_clicked.connect(self.on_save_clicked)
                                self.menus.addTab(buttons, menu)
                elif isinstance(menu_dict[self.software], list):
                    for menu in menu_dict[self.software]:
                        menu_name = menu['name']
                        # buttons = menu['buttons']
                        buttons = CGLMenu(parent=self, software=self.software, menu_name=menu_name,
                                          menu=menu,
                                          menu_path=self.menu_path, menu_type=self.type, cfg=self.cfg)
                        # buttons.menu_button_save_clicked.connect(self.on_save_clicked)
                        self.menus.addTab(buttons, menu_name)

            else:
                print('%s not found in %s' % (self.softwre, self.menu_path))

    def load_tasks(self):
        ignore = ['__init__.py']
        tasks_path = self.menu_path.replace('.cgl', '')
        if os.path.exists(tasks_path):
            for each in os.listdir(tasks_path):
                print(each)

    def on_new_software_clicked(self):
        dialog = InputDialog(title='Add Software', message='Enter or Choose Software',
                             combo_box_items=['', 'lumbermill', 'nuke', 'maya', 'blender', 'houdini', 'unreal'],
                             regex='[a-zA-Z0-0]{3,}', name_example='Only letters & Numbers Allowed Software Names')
        dialog.exec_()
        if dialog.button == 'Ok':
            software_name = dialog.combo_box.currentText()
            folder = os.path.join(self.cgl_tools, software_name)
            os.makedirs(folder)
            self.software_combo.addItem(software_name)
            num = self.software_combo.count()
            self.software_combo.setCurrentIndex(num)

    def save_button(self, button_widget):
        print('Saving All Dirty Buttons')
        if button_widget.dirty:
            print('Saving {}'.format(button_widget.name))

    def save_menus(self):
        """
        Saves the .json files for the menus in the current session.
        Also saves all "dirty" or changed buttons from the current session.
        :return:
        """
        menu_name = ''
        menu_dict = {}
        menu_array = []
        button_widget = None
        for mi in range(self.menus.count()):
            menu_name = self.menus.tabText(mi)
            menu = self.menus.widget(mi)
            if self.software == 'blender':
                from cgl.plugins.blender.utils import add_buttons_to_menu
                add_buttons_to_menu(menu_name)
            mi_dict = {"name": menu_name,
                       "buttons": []}
            # menu_dict[menu_name]['order'] = mi+1
            for bi in range(menu.buttons_tab_widget.count()):
                button_dict = {}
                button_widget = menu.buttons_tab_widget.widget(bi)
                reference_path = button_widget.reference_path
                if button_widget.dirty:
                    button_widget.on_menu_button_save_clicked()
                if button_widget.name_line_edit.text():
                    button_name = button_widget.name_line_edit.text()
                else:
                    split = button_widget.command_line_edit.text().split()
                    print('setting name to module name: %s' % split[-1].split('.run()')[0])
                    button_name = split[-1].split('.run()')[0]
                if self.type == 'pre_publish':
                    button_dict = {
                                        'module': button_widget.command_line_edit.text(),
                                        'label': button_widget.label_line_edit.text(),
                                        'order': bi + 1,
                                        'required': button_widget.required_line_edit.text(),
                                        'name': button_name
                                    }
                elif self.type == 'shelves':
                    if button_widget.icon_path_line_edit.text():
                        icon_text = button_widget.icon_path_line_edit.text()
                    else:
                        icon_text = ""
                    button_dict = {
                                     'module': button_widget.command_line_edit.text(),
                                     'label': button_widget.label_line_edit.text(),
                                     'order': bi + 1,
                                     'icon': icon_text,
                                     'name': button_name,
                                     'reference_path': reference_path
                                    }
                else:
                    button_dict = {
                                     'module': button_widget.command_line_edit.text(),
                                     'label': button_widget.label_line_edit.text(),
                                     'order': bi+1,
                                     'name': button_name
                                     }
                mi_dict['buttons'].append(button_dict)
                # print(mi_dict)
            menu_array.append(mi_dict)
        if self.software.lower() == 'unreal':
            print('Unreal Engine')
        json_object = {self.software: menu_array}
        print('saving menu json', self.menu_path)
        self.save_json(self.menu_path, json_object)

    def create_empty_menu(self):
        json_object = {self.software: {}}
        if self.type == 'tasks':
            tasks_path = self.menu_path.replace('.cgl', '\\tasks')
            print(tasks_path)
            json_object = {self.software: [{'buttons': [], 'name': 'tasks'}]}

        self.save_json(self.menu_path, json_object)

    @staticmethod
    def save_json(filepath, data):
        """
        saves a json file
        :param filepath:
        :param data:
        :return:
        """
        try:
            with open(filepath, 'w') as outfile:
                json.dump(data, outfile, indent=4, sort_keys=True)
        except TypeError:
            pass

    @staticmethod
    def load_json(filepath):
        """
        loads a .json file and returns a dictionary: data
        :param filepath:
        :return:
        """
        with open(filepath) as jsonfile:
            data = json.load(jsonfile)
        return data

    def closeEvent(self, event):
        """
        what happens when the app is closed using the "x' button
        :param event:
        :return:
        """
        if event:
            self.save_menus()


if __name__ == "__main__":
    from cgl.ui.startup import do_gui_init
    app = do_gui_init()
    mw = Designer(type_='pre_publish')
    # mw = Designer(type_='menus')
    mw.setWindowTitle('Alchemists Cookbook')
    mw.setMinimumWidth(1200)
    mw.setMinimumHeight(500)
    mw.show()
    mw.raise_()
    style_sheet = load_style_sheet()
    app.setStyleSheet(style_sheet)
    app.exec_()

