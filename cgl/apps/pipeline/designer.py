import os
import json
from cgl.plugins.Qt import QtWidgets
from cgl.ui.widgets.dialog import InputDialog
from cgl.ui.widgets.base import LJDialog
from cgl.core.utils.general import load_style_sheet
from cgl.core.project import get_cgl_tools
from utils import CGLMenu


class Designer(LJDialog):
    def __init__(self, parent=None, type_=None, menu_path=None, pm_tasks=None):
        LJDialog.__init__(self, parent)
        self.type = type_
        self.cgl_tools = get_cgl_tools()
        self.singular = ''

        self.menu_path = menu_path
        self.software = ''
        self.setWindowTitle('Pipeline Designer')
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
            print 'Problems found in your globals "schema"'
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
        self.menu_type_label = QtWidgets.QLabel('Menu Type:')
        self.menu_type_label.setProperty('class', 'title')
        self.menu_type_combo = QtWidgets.QComboBox()
        self.menu_type_combo.addItems(['', 'menus', 'context-menus', 'shelves', 'preflights'])

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
            self.menus.removeTab(index)

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
        self.type = self.menu_type_combo.currentText()
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
        elif self.type == 'preflights':
            self.singular = 'preflight'
        elif self.type == 'context-menus':
            self.singular = 'context-menu'
        else:
            self.singular = 'not defined'

    def on_add_menu_clicked(self):
        if self.type == 'preflights' or self.type == 'context-menus':
            if self.type == 'preflights':
                singular = 'preflight'
            elif self.type == 'context-menus':
                singular = 'Context Menu'
            elif self.type == 'shelves':
                singular = 'Shelf'
            dialog = InputDialog(title='Add %s' % singular,
                                 message='Choose Task to Create a %s For\n Or Type to Create Your Own' % singular,
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

    def do_add_menu(self, menu_name):
        cgl_file = self.menu_path
        new_menu = CGLMenu(parent=self, software=self.software, menu_name=menu_name, menu=[],
                           menu_path=cgl_file, menu_type=self.type)
        new_menu.save_clicked.connect(self.on_save_clicked)
        index = self.menus.addTab(new_menu, menu_name)
        self.menus.setCurrentIndex(index)

    def on_save_clicked(self):
        print 'saving menus 182'
        self.save_menus()

    def load_menus(self):
        menu_dict = {}
        self.menus.clear()
        self.title_widget.show()
        self.title_label.setText('%s %s' % (self.software_combo.currentText(), self.type))
        self.software = self.software_combo.currentText()
        if os.path.exists(self.menu_path):
            menu_dict = self.load_json(self.menu_path)
        if menu_dict:
            if self.software in menu_dict:
                for i in range(len(menu_dict[self.software])+1):
                    for menu in menu_dict[self.software]:
                        if i == menu_dict[self.software][menu]['order']:
                            buttons = CGLMenu(parent=self, software=self.software, menu_name=menu, menu=menu_dict[self.software][menu],
                                              menu_path=self.menu_path, menu_type=self.type)
                            buttons.save_clicked.connect(self.on_save_clicked)
                            self.menus.addTab(buttons, menu)
            else:
                print '%s not found in %s' % (self.softwre, self.menu_path)

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
        # TODO - if you change the label this actually deletes stuff.
        menu_dict = {}
        for mi in range(self.menus.count()):
            menu_name = self.menus.tabText(mi)
            menu = self.menus.widget(mi)
            menu_dict[menu_name] = {}
            menu_dict[menu_name]['order'] = mi+1
            for bi in range(menu.buttons_tab_widget.count()):

                button_widget = menu.buttons_tab_widget.widget(bi)
                if button_widget.name_line_edit.text():
                    button_name = button_widget.name_line_edit.text()
                else:
                    split = button_widget.command_line_edit.text().split()
                    print 'setting name to module name: %s' % split[-1].split('.run()')[0]
                    button_name = split[-1].split('.run()')[0]
                if self.type == 'preflights':
                    menu_dict[menu_name][button_name] = {
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
                    menu_dict[menu_name][button_name] = {
                                                         'module': button_widget.command_line_edit.text(),
                                                         'label': button_widget.label_line_edit.text(),
                                                         'order': bi + 1,
                                                         'icon': icon_text,
                                                         'name': button_name
                                                        }
                    print '\t', button_name
                    print menu_dict[menu_name][button_name]
                else:
                    menu_dict[menu_name][button_name] = {
                                                         'module': button_widget.command_line_edit.text(),
                                                         'label': button_widget.label_line_edit.text(),
                                                         'order': bi+1,
                                                         'name': button_name
                                                         }

                self.save_code(menu_name, button_widget)
        json_object = {self.software: menu_dict}
        print 'saving json', self.menu_path
        print json_object
        self.save_json(self.menu_path, json_object)

    def create_empty_menu(self):
        json_object = {self.software: {}}
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
        if folder:
            folder = folder.replace('\\', '/')
            folder = folder.replace(config, '')
            parts = folder.split('/')
            if '' in parts:
                parts.remove('')
            string = config
            for p in parts:
                if ':' not in p:
                    if '.' not in p:
                        string = '%s/%s' % (string, p)
                        init = '%s/__init__.py' % string
                        if not os.path.exists(init):
                            self.make_init(os.path.dirname(init))

    @staticmethod
    def make_init(folder):
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
        #TODO - i'd like to save this only if it's actually got problems.
        if event:
            self.save_menus()


if __name__ == "__main__":
    from cgl.ui.startup import do_gui_init
    app = do_gui_init()
    mw = Designer(type_='preflights')
    # mw = Designer(type_='menus')
    mw.setWindowTitle('Preflight Designer')
    mw.setMinimumWidth(1200)
    mw.setMinimumHeight(500)
    mw.show()
    mw.raise_()
    style_sheet = load_style_sheet()
    app.setStyleSheet(style_sheet)
    app.exec_()

