import os
from Qt import QtWidgets, QtCore, QtGui
from cglui.widgets.dialog import InputDialog
from cglui.widgets.text import Highlighter
from cglcore.path import start


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


class PreflightStep(QtWidgets.QWidget):

    def __init__(self, parent=None, preflight_name='', preflight_step_name='', attrs={}, preflight_path=''):
        QtWidgets.QWidget.__init__(self, parent)
        self.attrs = attrs
        self.name = preflight_step_name
        self.parent = parent
        self.preflight_name = preflight_name
        self.preflight_path = preflight_path
        self.do_save = True
        # Create the Layouts
        layout = QtWidgets.QVBoxLayout(self)
        grid_layout = QtWidgets.QGridLayout()
        tool_row = QtWidgets.QHBoxLayout()

        # labels
        module_label = QtWidgets.QLabel('module')
        required_label = QtWidgets.QLabel('required')
        label_label = QtWidgets.QLabel('label')

        # line edits
        self.command_line_edit = QtWidgets.QLineEdit()
        self.command_line_edit.setEnabled(False)
        self.required_line_edit = QtWidgets.QLineEdit()
        self.required_line_edit.setText('True')
        #self.required_line_edit.setEnabled(False)
        self.label_line_edit = QtWidgets.QLineEdit()
        self.attrs_dict = {'module': self.command_line_edit,
                           'required': self.required_line_edit,
                           'label': self.label_line_edit}

        # tool buttons
        delete_button = QtWidgets.QPushButton('Delete')
        delete_button.setProperty('class', 'basic')
        open_button = QtWidgets.QPushButton('Open')
        open_button.setProperty('class', 'basic')

        # Text Edit
        self.code_text_edit = QtWidgets.QPlainTextEdit()
        metrics = QtWidgets.QFontMetrics(self.code_text_edit.font())
        self.code_text_edit.setTabStopWidth(4 * metrics.width(' '))
        highlighter = Highlighter(self.code_text_edit.document())

        # Layout the Grid
        grid_layout.addWidget(required_label, 2, 0)
        grid_layout.addWidget(self.required_line_edit, 2, 1)
        grid_layout.addWidget(label_label, 0, 0)
        grid_layout.addWidget(self.label_line_edit, 0, 1)
        grid_layout.addWidget(module_label, 1, 0)
        grid_layout.addWidget(self.command_line_edit, 1, 1)

        # Layout the tool row
        tool_row.addStretch(1)
        tool_row.addWidget(open_button)
        tool_row.addWidget(delete_button)

        # layout the widget
        layout.addLayout(grid_layout)
        layout.addWidget(self.code_text_edit)
        layout.addLayout(tool_row)

        # Signals and Slots
        self.code_text_edit.textChanged.connect(self.on_code_changed)
        delete_button.clicked.connect(self.on_delete_clicked)
        open_button.clicked.connect(self.on_open_clicked)
        self.load_attrs()
        self.label_line_edit.textChanged.connect(self.on_code_changed)

    def on_open_clicked(self):
        code_path = os.path.join(os.path.dirname(self.preflight_path), 'preflights', self.preflight_name,
                                 '%s.py' % self.name)
        print code_path
        start(code_path)

    def on_code_changed(self):
        code_path = os.path.join(os.path.dirname(self.preflight_path), 'preflights', self.preflight_name,
                                 '%s.py' % self.name)
        print code_path
        self.do_save = True

    def load_attrs(self):
        for attr in self.attrs:
            if attr in self.attrs_dict:
                self.attrs_dict[attr].setText(str(self.attrs[attr]))
        # load the python file into the text edit
        code_text = self.load_code_text()
        if code_text:
            self.code_text_edit.setPlainText(code_text)
            self.do_save = False
        else:
            code_text = self.load_default_text()
            self.code_text_edit.setPlainText(code_text)

    def load_code_text(self):
        code_path = os.path.join(os.path.dirname(self.preflight_path), 'preflights', self.preflight_name,
                                 '%s.py' % self.name)
        if os.path.exists(code_path):
            try:
                return open(code_path).read()
            except IOError:
                with open(code_path, 'w+') as y:
                    y.write("")
            return None

    def load_default_text(self):
        preflight = "from plugins.preflight.preflight_check import PreflightCheck\n" \
                    "\n" \
                    "class %s(PreflightCheck):\n" \
                    "\n" \
                    "    def getName(self):\n" \
                    "        pass\n" \
                    "\n" \
                    "    def run(self):\n" \
                    "        print '%s'\n" \
                    "        # self.pass_check('Check Passed')\n" \
                    "        # self.fail_check('Check Failed')\n\n" % (self.name, self.name)
        return preflight

    def on_delete_clicked(self):
        self.parent.removeTab(self.parent.currentIndex())


class MenuButton(QtWidgets.QWidget):

    def __init__(self, parent=None, menu_name='', button_name='', attrs={}, menu_path='', icon=False,
                 menu_type='menus'):
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
        icon_label = QtWidgets.QLabel('icon')


        # line edits
        self.command_line_edit = QtWidgets.QLineEdit()
        self.command_line_edit.setEnabled(False)
        self.button_name_line_edit = QtWidgets.QLineEdit()
        self.button_name_line_edit.setEnabled(False)
        self.label_line_edit = QtWidgets.QLineEdit()
        self.icon_line_edit = QtWidgets.QLineEdit()
        if icon:
            self.attrs_dict = {'command': self.command_line_edit,
                               'button name': self.button_name_line_edit,
                               'label': self.label_line_edit,
                               'icon': self.icon_line_edit}
        else:
            self.attrs_dict = {'command': self.command_line_edit,
                               'button name': self.button_name_line_edit,
                               'label': self.label_line_edit}



        # tool buttons
        find_icon_button = QtWidgets.QToolButton()
        find_icon_button.setText('...')
        delete_button = QtWidgets.QPushButton('Delete')
        delete_button.setProperty('class', 'basic')
        open_button = QtWidgets.QPushButton('Open')
        open_button.setProperty('class', 'basic')

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
        if icon:
            grid_layout.addWidget(icon_label, 3, 0)
            grid_layout.addWidget(self.icon_line_edit, 3, 1)
            grid_layout.addWidget(find_icon_button, 3, 2)
        else:
            icon_label.hide()
            self.icon_line_edit.hide()
            find_icon_button.hide()

        # Layout the tool row
        tool_row.addStretch(1)
        tool_row.addWidget(open_button)
        tool_row.addWidget(delete_button)

        # layout the widget
        layout.addLayout(grid_layout)
        layout.addWidget(self.code_text_edit)
        layout.addLayout(tool_row)
        
        # Signals and Slots
        self.button_name_line_edit.textChanged.connect(self.set_button_name)
        self.code_text_edit.textChanged.connect(self.on_code_changed)
        delete_button.clicked.connect(self.on_delete_clicked)
        open_button.clicked.connect(self.on_open_clicked)
        self.load_attrs()
        self.label_line_edit.textChanged.connect(self.on_code_changed)

    def on_open_clicked(self):
        code_path = os.path.join(os.path.dirname(self.menu_path), 'menus', self.menu_name, '%s.py' % self.name)
        print code_path
        start(code_path)

    def on_code_changed(self):
        code_path = os.path.join(os.path.dirname(self.menu_path), 'menus', self.menu_name, '%s.py' % self.name)
        self.do_save = True

    def load_attrs(self):
        for attr in self.attrs:
            if attr in self.attrs_dict:
                self.attrs_dict[attr].setText(self.attrs[attr])
        # load the python file into the text edit
        code_text = self.load_code_text()
        if code_text:
            self.code_text_edit.setPlainText(code_text)
            self.do_save = False
        else:
            code_text = self.load_default_text()
            self.code_text_edit.setPlainText(code_text)

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

    def __init__(self, parent=None, software=None, menu_type='menu', menu_name='', menu={}, menu_path=''):
        QtWidgets.QWidget.__init__(self, parent)

        # initialize variables
        self.type = menu_type
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
        self.title = ''
        if self.type == 'menus':
            self.title = QtWidgets.QLabel('%s %s Buttons: (Drag to Reorder)' % (self.menu_name, self.type.title()))
        elif self.type == 'preflights':
            self.title = QtWidgets.QLabel('%s %s Steps: (Drag to Reorder)' % (self.menu_name, self.type.title()))
        elif self.type == 'shelves':
            self.title = QtWidgets.QLabel('%s Shelf Buttons: (Drag to Reorder)' % self.menu_name)
        self.title.setProperty('class', 'title')

        if self.type == 'shelves':
            self.add_button = QtWidgets.QPushButton('add shelf button')
            self.delete_parent_button = QtWidgets.QPushButton('Delete Shelf')
        elif self.type == 'preflights':
            self.add_button = QtWidgets.QPushButton('add preflight step')
            self.delete_parent_button = QtWidgets.QPushButton('Delete Preflight')
        else:
            self.add_button = QtWidgets.QPushButton('add %s button' % self.type)
            self.delete_parent_button = QtWidgets.QPushButton('Delete Menu')
        self.add_button.setProperty('class', 'add_button')
        self.delete_parent_button.setProperty('class', 'add_button')

        # set parameters
        self.buttons.setMovable(True)

        # layout the widget
        title_layout.addWidget(self.title)
        title_layout.addWidget(self.add_button)
        title_layout.addWidget(self.delete_parent_button)
        title_layout.addStretch(1)
        layout.addLayout(title_layout)
        layout.addWidget(self.buttons)

        # connect SIGNALS and SLOTS
        self.add_button.clicked.connect(self.on_add_menu_button)
        self.delete_parent_button.clicked.connect(self.on_delete_parent_clicked)
        self.load_buttons()

    def on_delete_parent_clicked(self):
        print self.menu_name
        dialog = InputDialog(title='Delete %s?' % self.menu_name, message='Are you sure you want to delete %s' % self.menu_name)
        dialog.exec_()
        if dialog.button == 'Ok':
            print 'Deleting %s' % self.menu_name
            menus = self.buttons.parent().parent().parent()
            menus.removeTab(menus.currentIndex())

    def on_add_menu_button(self):
        print self.menu_path, 'is path'
        if self.type == 'menus':
            dialog = InputDialog(title='Add Menu Button', message='Enter a Name for your Button', line_edit=True,
                                 regex='[a-zA-Z0-0]{3,}', name_example='Only letters & Numbers Allowed in Button Names')
            dialog.exec_()
            if dialog.button == 'Ok':
                button_name = dialog.line_edit.text()
                command = self.get_command_text(button_name, 'menus')
                attrs = {'button name': button_name,
                         'label': button_name,
                         'command': command}
                new_button_widget = MenuButton(menu_name=self.menu_name, button_name=button_name,
                                               attrs=attrs, menu_path=self.menu_path)
                index = self.buttons.addTab(new_button_widget, button_name)
                self.buttons.setCurrentIndex(index)
        elif self.type == 'preflights':
            dialog = InputDialog(title='Add Preflight Step', message='Enter a Name for your Preflight Step',
                                 line_edit=True, regex='[a-zA-Z]{3,}',
                                 name_example='Ideally Preflights are CamelCase - ExamplePreflightName')
            dialog.exec_()
            if dialog.button == 'Ok':
                preflight_name = dialog.line_edit.text()
                module = self.default_preflight_text(preflight_name)
                attrs = {'label': preflight_name,
                         'required': 'True',
                         'module': module}
                new_button_widget = PreflightStep(parent=self.buttons, preflight_name=self.menu_name,
                                                  preflight_step_name=dialog.line_edit.text(),
                                                  attrs=attrs, preflight_path=self.menu_path)
                index = self.buttons.addTab(new_button_widget, preflight_name)
                self.buttons.setCurrentIndex(index)
        elif self.type == 'shelves':
            dialog = InputDialog(title='Add Shelf Button', message='Enter a Name for your Button',
                                 line_edit=True, regex='[a-zA-Z0-0]{3,}',
                                 name_example='Only letters & Numbers Allowed in Button Names')
            dialog.exec_()
            if dialog.button == 'Ok':
                button_name = dialog.line_edit.text()
                command = self.get_command_text(button_name, 'shelves')
                attrs = {'button name': button_name,
                         'label': button_name,
                         'command': command,
                         'icon': ''}
                new_button_widget = MenuButton(menu_name=self.menu_name, button_name=button_name,
                                               attrs=attrs, menu_path=self.menu_path, icon=True, menu_type='shelves')
                index = self.buttons.addTab(new_button_widget, button_name)
                self.buttons.setCurrentIndex(index)

    def get_command_text(self, button_name, menu_type):
        return 'import cgl_tools.%s.%s.%s.%s as %s; %s.run()' % (self.software, menu_type, self.menu_name, button_name,
                                                                    button_name, button_name)

    def default_preflight_text(self, preflight_name):
        return 'cgl_tools.%s.preflights.%s.%s' % (self.software, self.menu_name, preflight_name)

    def load_buttons(self):
        for i in range(len(self.menu)):
            for button in self.menu:
                if button != 'order':
                    if i == self.menu[button]['order']:
                        if self.type == 'menus':
                            button_widget = MenuButton(parent=self.buttons, menu_name=self.menu_name, button_name=button,
                                                       attrs=self.menu[button], menu_path=self.menu_path)
                            self.buttons.addTab(button_widget, button)
                        elif self.type == 'preflights':
                            button_widget = PreflightStep(parent=self.buttons, preflight_name=self.menu_name,
                                                          preflight_step_name=button,
                                                          attrs=self.menu[button], preflight_path=self.menu_path)
                            self.buttons.addTab(button_widget, button)









