import yaml
import os
import json
from Qt import QtWidgets, QtCore, QtGui
from cglui.widgets.dialog import InputDialog
from cglui.widgets.base import LJDialog
from cglcore.path import load_style_sheet, get_company_config
from cglui.widgets.text import Highlighter


GUI_DICT = {'shelves.yaml': ['button name', 'command', 'icon', 'order', 'annotation', 'label'],
            'preflights.yaml': ['order', 'module', 'name', 'required'],
            'menus.yaml': ['order', 'name']}


class CGLTabBar(QtWidgets.QTabBar):

    def tabSizeHint(self, index):
        s = QtWidgets.QTabBar.tabSizeHint(self, index)
        s.transpose()
        return s

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        opt = QtWidgets.QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QtCore.QRect(QtCore.QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt);
            painter.restore()


class LJTabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QTabWidget.__init__(self, *args, **kwargs)
        self.setTabBar(CGLTabBar(self))
        self.setTabPosition(QtWidgets.QTabWidget.West)


class MenuButton(QtWidgets.QWidget):

    def __init__(self, parent=None, menu_name='', button_name='', attrs={}, menu_path=''):
        QtWidgets.QWidget.__init__(self, parent)
        self.attrs = attrs
        self.name = button_name
        self.parent = parent
        self.menu_name = menu_name
        self.menu_path = menu_path
        self.do_save = True
        # Create the Layouts
        layout = QtWidgets.QVBoxLayout(self)
        grid_layout = QtWidgets.QGridLayout()
        tool_row = QtWidgets.QHBoxLayout()

        # labels
        command_label = QtWidgets.QLabel('command')
        button_name_label = QtWidgets.QLabel('button name')
        label_label = QtWidgets.QLabel('label')


        # line edits
        self.command_line_edit = QtWidgets.QLineEdit()
        self.command_line_edit.setEnabled(False)
        self.button_name_line_edit = QtWidgets.QLineEdit()
        self.button_name_line_edit.setEnabled(False)
        self.label_line_edit = QtWidgets.QLineEdit()
        self.attrs_dict = {'command': self.command_line_edit,
                           'button name': self.button_name_line_edit,
                           'label': self.label_line_edit}

        # tool buttons
        delete_button = QtWidgets.QPushButton('Delete')

        # Text Edit
        self.code_text_edit = QtWidgets.QPlainTextEdit()
        metrics = QtWidgets.QFontMetrics(self.code_text_edit.font())
        self.code_text_edit.setTabStopWidth(4 * metrics.width(' '))
        highlighter = Highlighter(self.code_text_edit.document())

        # Layout the Grid
        grid_layout.addWidget(button_name_label, 0, 0)
        grid_layout.addWidget(self.button_name_line_edit, 0, 1)
        grid_layout.addWidget(label_label, 1, 0)
        grid_layout.addWidget(self.label_line_edit, 1, 1)
        grid_layout.addWidget(command_label, 2, 0)
        grid_layout.addWidget(self.command_line_edit, 2, 1)

        # Layout the tool row
        tool_row.addStretch(1)
        tool_row.addWidget(delete_button)

        # layout the widget
        layout.addLayout(grid_layout)
        layout.addWidget(self.code_text_edit)
        layout.addLayout(tool_row)
        
        # Signals and Slots
        self.button_name_line_edit.textChanged.connect(self.set_button_name)
        #self.label_line_edit.textChanged.connect(self.on_code_changed)
        self.code_text_edit.textChanged.connect(self.on_code_changed)
        delete_button.clicked.connect(self.on_delete_clicked)
        self.load_attrs()

    def on_code_changed(self):
        code_path = os.path.join(os.path.dirname(self.menu_path), 'menus', self.menu_name, '%s.py' % self.name)
        self.do_save = True
        print 'Changing %s setting do save True' % self.name

    def load_attrs(self):
        for attr in self.attrs:
            if attr in self.attrs_dict:
                self.attrs_dict[attr].setText(self.attrs[attr])
        # load the python file into the text edit
        code_text = self.load_code_text()
        if code_text:
            self.do_save = False
            self.code_text_edit.setPlainText(code_text)
            print 'loading %s from disk set do save false' % self.name
        else:
            code_text = self.load_default_text()
            self.code_text_edit.setPlainText(code_text)
            #self.on_code_changed()

    def load_code_text(self):
        code_path = os.path.join(os.path.dirname(self.menu_path), 'menus', self.menu_name, '%s.py' % self.name)
        if os.path.exists(code_path):
            try:
                return open(code_path).read()
            except IOError:
                with open(code_path, 'w+') as y:
                    y.write("")
            return None

    def load_default_text(self):
        return "def run():\n    print(\"hello world: %s\")" % self.name

    def set_button_name(self):
        self.name = self.button_name_line_edit.text()

    def on_delete_clicked(self):
        self.parent.removeTab(self.parent.currentIndex())


class CGLMenu(QtWidgets.QWidget):

    def __init__(self, parent=None, software=None, menu_name='', menu={}, menu_path=''):
        QtWidgets.QWidget.__init__(self, parent)

        # initialize variables
        self.software = software
        self.menu = menu
        self.menu_name = menu_name
        self.menu_path = menu_path

        # create layouts
        layout = QtWidgets.QVBoxLayout(self)
        title_layout = QtWidgets.QHBoxLayout()
        self.buttons = LJTabWidget()
        self.buttons.setProperty('class', 'vertical')
        self.buttons.tabBar().setProperty('class', 'vertical')
        self.title = QtWidgets.QLabel('%s Menu Buttons: (Drag to Reorder)' % self.menu_name)
        self.title.setProperty('class', 'title')
        self.add_button = QtWidgets.QPushButton('add menu button')
        self.add_button.setProperty('class', 'add_button')

        # set parameters
        self.buttons.setMovable(True)

        # layout the widget
        title_layout.addWidget(self.title)
        title_layout.addWidget(self.add_button)
        title_layout.addStretch(1)
        layout.addLayout(title_layout)
        layout.addWidget(self.buttons)

        # connect SIGNALS and SLOTS
        self.add_button.clicked.connect(self.on_add_menu_button)

        self.load_buttons()

    def on_add_menu_button(self):
        dialog = InputDialog(title='Add Menu Button', message='Enter a Name for your Button', line_edit=True,
                             regex='[a-zA-Z0-0]{3,}', name_example='Only letters & Numbers Allowed in Button Names')
        dialog.exec_()
        if dialog.button == 'Ok':
            button_name = dialog.line_edit.text()
            command = self.get_command_text(button_name)
            attrs = {'button name': button_name,
                     'label': button_name,
                     'command': command}
            new_button_widget = MenuButton(menu_name=self.menu_name, button_name=button_name,
                                           attrs=attrs, menu_path=self.menu_path)
            index = self.buttons.addTab(new_button_widget, button_name)
            self.buttons.setCurrentIndex(index)

    def save_initialized(self, data):
        print data

    def get_command_text(self, button_name):

        return 'import cgl_tools.%s.menus.%s.%s as %s; %s.run()' % (self.software, self.menu_name, button_name,
                                                                    button_name, button_name)

    def find_tab(self, name):
        print name

    def order_buttons(self):
        for button in self.menu:
            if button != 'order':
                print button, ' order : ', self.menu[button]['order']

    def load_buttons(self):
        print 'number of buttons', len(self.menu)-1
        for i in range(len(self.menu)):
            for button in self.menu:
                if button != 'order':
                    if i == self.menu[button]['order']:
                        button_widget = MenuButton(parent=self.buttons, menu_name=self.menu_name, button_name=button,
                                                   attrs=self.menu[button], menu_path=self.menu_path)
                        self.buttons.addTab(button_widget, button)
        self.order_buttons()


class MenuDesigner(LJDialog):
    def __init__(self, parent=None, company_config=None, menu_path=None):
        LJDialog.__init__(self, parent)
        self.company_config = company_config
        self.menu_path = menu_path
        self.software = ''
        self.company = ''

        # create layouts
        layout = QtWidgets.QVBoxLayout(self)
        tool_bar = QtWidgets.QHBoxLayout()
        self.title_widget = QtWidgets.QWidget()
        title_widget_layout = QtWidgets.QHBoxLayout()
        self.title_widget.setLayout(title_widget_layout)
        grid_layout = QtWidgets.QGridLayout()
        menu_type_row = QtWidgets.QHBoxLayout()


        # create widgets
        self.company_label = QtWidgets.QLabel('Company:')
        self.company_label.setProperty('class', 'title')
        self.company_combo = QtWidgets.QComboBox()
        self.software_label = QtWidgets.QLabel('Software:')
        self.software_label.setProperty('class', 'title')
        self.software_combo = QtWidgets.QComboBox()
        self.new_software_button = QtWidgets.QPushButton('Add Software')
        self.new_software_button.setProperty('class', 'add_button')
        self.menus = QtWidgets.QTabWidget()
        self.title_label = QtWidgets.QLabel()
        self.title_label.setProperty('class', 'ultra_title')
        self.add_menu_button = QtWidgets.QPushButton('add menu')
        self.add_menu_button.setProperty('class', 'add_button')
        self.save_menu_button = QtWidgets.QPushButton('save menu')
        self.save_menu_button.setProperty('class', 'add_button')

        self.company_combo.hide()
        self.company_label.hide()
        self.title_widget.hide()

        # layout the GUI
        title_widget_layout.addWidget(self.title_label)
        title_widget_layout.addWidget(self.add_menu_button)
        title_widget_layout.addStretch(1)
        title_widget_layout.addWidget(self.save_menu_button)
        grid_layout.addWidget(self.company_label, 0, 0)
        grid_layout.addWidget(self.company_combo, 0, 1)
        grid_layout.addWidget(self.software_label, 1, 0)
        grid_layout.addWidget(self.software_combo, 1, 1)
        grid_layout.addWidget(self.new_software_button, 1, 2)

        tool_bar.addLayout(grid_layout)
        tool_bar.addStretch(1)
        layout.addLayout(tool_bar)
        layout.addWidget(self.title_widget)
        layout.addLayout(menu_type_row)
        layout.addWidget(self.menus)

        # SIGNALS AND SLOTS
        self.company_combo.currentIndexChanged.connect(self.load_software)
        self.software_combo.currentIndexChanged.connect(self.load_menus)
        self.add_menu_button.clicked.connect(self.on_add_menu_clicked)
        self.save_menu_button.clicked.connect(self.save_menus)
        self.new_software_button.clicked.connect(self.on_new_software_clicked)

        # Load the Menu Designer
        if not self.company_config:
            self.company_combo.show()
            self.company_label.show()
            self.company_config = get_company_config()

        self.load_companies()
        self.load_software()

    def load_companies(self):
        self.company_combo.clear()
        self.company_combo.addItem('')
        self.company_combo.addItems(os.listdir(self.company_config))

    def load_software(self):
        self.software_combo.clear()
        self.company = self.company_combo.currentText()
        dir_ = os.path.join(self.company_config, self.company, 'cgl_tools')
        if os.path.exists(dir_):
            softwares = os.listdir(dir_)
            for s in softwares:
                if '.' not in s:
                    self.software_combo.addItem(s)
        self.software = self.software_combo.currentText()
        self.update_menu_path()

    def update_menu_path(self):
        self.menu_path = os.path.join(self.company_config, self.company, 'cgl_tools', self.software, 'menus.cgl')

    def on_add_menu_clicked(self):
        dialog = InputDialog(title='Add Menu', message='Enter a Name for your Menu', line_edit=True,
                             regex='[a-zA-Z0-0]{3,}', name_example='Only letters & Numbers Allowed in Button Names')
        dialog.exec_()
        if dialog.button == 'Ok':
            menu_name = dialog.line_edit.text()
            file_ = os.path.join(self.company_config, self.company, 'cgl_tools', self.software, 'menus.yaml')
            new_menu = CGLMenu(software=self.software, menu_name=menu_name, menu=[],
                               menu_path=file_)
            index = self.menus.addTab(new_menu, menu_name)
            self.menus.setCurrentIndex(index)

    def load_menus(self):
        menu_dict = {}
        self.menus.clear()
        self.title_widget.show()
        self.title_label.setText('%s Menus' % self.software_combo.currentText())
        self.software = self.software_combo.currentText()
        file_ = os.path.join(self.company_config, self.company, 'cgl_tools', self.software, 'menus.yaml')
        cgl_file = os.path.join(self.company_config, self.company, 'cgl_tools', self.software, 'menus.cgl')

        if os.path.exists(cgl_file):
            menu_dict = self.load_json(cgl_file)
        elif os.path.exists(file_):
            with open(file_, 'r') as yaml_file:
                temp = yaml.load(yaml_file)
                menu_dict = temp
        if menu_dict:
            for menu in menu_dict[self.software]:
                buttons = CGLMenu(software=self.software, menu_name=menu, menu=menu_dict[self.software][menu],
                                  menu_path=file_)
                self.menus.addTab(buttons, menu)

    def on_new_software_clicked(self):
        dialog = InputDialog(title='Add Software', message='Enter or Choose Software',
                             combo_box_items=['', 'lumbermill', 'nuke', 'maya'],
                             regex='[a-zA-Z0-0]{3,}', name_example='Only letters & Numbers Allowed Software Names')
        dialog.exec_()
        if dialog.button == 'Ok':
            software_name = dialog.combo_box.currentText()
            folder = os.path.join(self.company_config, self.company, 'cgl_tools', software_name)
            os.makedirs(folder)
            self.software_combo.addItem(software_name)
            num = self.software_combo.count()
            self.software_combo.setCurrentIndex(num)

    def save_menus(self):
        file_ = os.path.join(self.company_config, self.company, 'cgl_tools', self.software, 'menus.cgl')
        menu_dict = {}
        for mi in range(self.menus.count()):
            menu_name = self.menus.tabText(mi)
            menu = self.menus.widget(mi)
            menu_dict[menu_name] = {}
            menu_dict[menu_name]['order'] = mi+1
            for bi in range(menu.buttons.count()):
                button_name = menu.buttons.tabText(bi)
                button_widget = menu.buttons.widget(bi)
                menu_dict[menu_name][button_name] = {'button name': button_widget.button_name_line_edit.text(),
                                                     'command': button_widget.command_line_edit.text(),
                                                     'label': button_widget.label_line_edit.text(),
                                                     'order': bi+1
                                                     }
                self.save_code(menu_name, button_widget)
        json_object = {self.software: menu_dict}
        self.save_json(file_, json_object)

    def save_code(self, menu_name, button_widget):
        button_name = button_widget.name
        code = button_widget.code_text_edit.document().toPlainText()
        button_file = os.path.join(self.company_config, self.company, 'cgl_tools', self.software, 'menus', menu_name,
                                   "%s.py" % button_name)
        dir_ = os.path.dirname(button_file)
        if not os.path.exists(dir_):
            os.makedirs(dir_)
        if button_widget.do_save:
            print 1, button_file
            with open(button_file, 'w+') as x:
               x.write(code)
            button_widget.do_save = False

    def make_init(self, folder):
        print 'creating init for %s' % folder
        with open(os.path.join(folder, '__init__.py'), 'w+') as i:
            i.write("")

    @staticmethod
    def save_json(filepath, data):
        print filepath
        with open(filepath, 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)

    @staticmethod
    def load_json(filepath):
        with open(filepath) as jsonfile:
            data = json.load(jsonfile)
        return data


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    menu_path = r'C:\Users\tmiko\Documents\cglumberjack\companies'
    app = do_gui_init()
    mw = MenuDesigner()
    mw.setWindowTitle('Menu Designer')
    mw.setMinimumWidth(1200)
    mw.setMinimumHeight(500)
    mw.show()
    mw.raise_()
    style_sheet = load_style_sheet()
    app.setStyleSheet(style_sheet)
    app.exec_()







