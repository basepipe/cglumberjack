import os
from cgl.core.util import cgl_copy
from Qt import QtWidgets, QtCore, QtGui
from cgl.ui.widgets.dialog import InputDialog
from cgl.core.path import start, icon_path
from cgl.core.project import get_cgl_tools
from cgl.ui.widgets.text import Highlighter


GUI_DICT = {'shelves.yaml': ['button name', 'command', 'icon', 'order', 'annotation', 'label'],
            'preflights.yaml': ['order', 'module', 'name', 'required'],
            'menus.yaml': ['order', 'name']}


class CGLTabBar(QtWidgets.QTabBar):

    def tabSizeHint(self, index):
        s = QtWidgets.QTabBar.tabSizeHint(self, index)
        s.transpose()
        return s

    # noinspection PyUnusedLocal
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
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt)
            painter.restore()


class LJTabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QTabWidget.__init__(self, *args, **kwargs)
        self.setTabBar(CGLTabBar(self))
        self.setTabPosition(QtWidgets.QTabWidget.West)


class CGLMenuButton(QtWidgets.QWidget):
    """
    Represents the "Button" within the parent "Menu".
    """
    save_clicked = QtCore.Signal()

    def __init__(self, parent=None, preflight_name='', preflight_step_name='', attrs=None, preflight_path='',
                 menu_type='preflights'):
        # TODO - we need to choose better variable names, this is obviously "preflight" specific.
        QtWidgets.QWidget.__init__(self, parent)

        try:
            dialog = self.parent().parent().parent()
            self.software = dialog.software_combo.currentText()
        except AttributeError:
            # TODO - look into this a bit deeper, this is a fairly generic catch right now.
            print 'getting a wierd error on %s ' % dialog
            self.software = ''
        self.menu_type = menu_type
        self.attrs = attrs
        self.name = preflight_step_name
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
        icon_button = QtWidgets.QToolButton()
        icon_button.setIcon(QtGui.QIcon(os.path.join(icon_path(), 'folder24px.png')))
        self.icon_label = QtWidgets.QLabel('icon')

        # line edits
        self.command_line_edit = QtWidgets.QLineEdit()
        self.command_line_edit.setEnabled(False)
        self.required_line_edit = QtWidgets.QLineEdit()
        self.required_line_edit.setText('True')
        self.icon_path_line_edit = QtWidgets.QLineEdit()
        # self.required_line_edit.setEnabled(False)
        self.label_line_edit = QtWidgets.QLineEdit()
        self.attrs_dict = {'module': self.command_line_edit,
                           'required': self.required_line_edit,
                           'label': self.label_line_edit,
                           'icon': self.icon_path_line_edit}

        # tool buttons
        delete_button = QtWidgets.QPushButton('Delete')
        delete_button.setProperty('class', 'basic')
        open_button = QtWidgets.QPushButton('Open in Editor')
        open_button.setProperty('class', 'basic')
        self.save_button = QtWidgets.QPushButton('Save All')
        self.save_button.setProperty('class', 'basic')

        # Text Edit
        self.code_text_edit = QtWidgets.QPlainTextEdit()
        metrics = QtWidgets.QFontMetrics(self.code_text_edit.font())
        self.code_text_edit.setTabStopWidth(4 * metrics.width(' '))
        Highlighter(self.code_text_edit.document())
        # Layout the Grid

        grid_layout.addWidget(label_label, 0, 0)
        grid_layout.addWidget(self.label_line_edit, 0, 1)
        grid_layout.addWidget(module_label, 1, 0)
        grid_layout.addWidget(self.command_line_edit, 1, 1)
        grid_layout.addWidget(required_label, 2, 0)
        grid_layout.addWidget(self.required_line_edit, 2, 1)
        grid_layout.addWidget(self.icon_label, 3, 0)
        grid_layout.addWidget(self.icon_path_line_edit, 3, 1)
        grid_layout.addWidget(icon_button, 3, 2)
        if self.menu_type != 'shelves':
            self.icon_label.hide()
            self.icon_path_line_edit.hide()
            icon_button.hide()
        else:
            self.required_line_edit.hide()
            required_label.hide()

        # Layout the tool row
        tool_row.addStretch(1)
        tool_row.addWidget(open_button)
        tool_row.addWidget(delete_button)
        tool_row.addWidget(self.save_button)

        # layout the widget
        layout.addLayout(grid_layout)
        layout.addWidget(self.code_text_edit)
        layout.addLayout(tool_row)

        # Signals and Slots
        self.code_text_edit.textChanged.connect(self.on_code_changed)
        icon_button.clicked.connect(self.on_icon_button_clicked)
        delete_button.clicked.connect(self.on_delete_clicked)
        open_button.clicked.connect(self.on_open_clicked)
        self.save_button.clicked.connect(self.on_save_clicked)
        self.load_attrs()
        self.label_line_edit.textChanged.connect(self.on_code_changed)

    def on_icon_button_clicked(self):
        default_folder = os.path.join(get_cgl_tools(), self.software, self.menu_type, self.preflight_name)
        file_paths = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose a File to Attach', default_folder, "*")
        from_path = file_paths[0].replace('\\', '/')
        _, file_ = os.path.split(from_path)
        to_path = os.path.join(default_folder, file_).replace('\\', '/')
        if from_path != to_path:
            dirname = os.path.dirname(to_path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            cgl_copy(from_path, to_path)
        self.icon_path_line_edit.setText(to_path)
        # copy selected icon to icon folder path

    def on_save_clicked(self):
        self.save_clicked.emit()

    def on_open_clicked(self):
        code_path = os.path.join(os.path.dirname(self.preflight_path), self.menu_type, self.preflight_name,
                                 '%s.py' % self.name)
        start(code_path)

    def on_code_changed(self):
        self.do_save = True

    def load_attrs(self):
        """
        Loads the attrs for each "button" in the "Menu".
        :return:
        """
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
        code_path = os.path.join(os.path.dirname(self.preflight_path), self.menu_type, self.preflight_name,
                                 '%s.py' % self.name)
        if os.path.exists(code_path):
            try:
                return open(code_path).read()
            except IOError:
                with open(code_path, 'w+') as y:
                    y.write("")
            return None

    def load_default_text(self):
        if self.menu_type == 'preflights':
            preflight = "from plugins.preflight.preflight_check import PreflightCheck\n" \
                        "\n\n" \
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
        else:
            return "def run():\n    print(\"hello world: %s\")" % self.name

    def on_delete_clicked(self):
        print self
        print self.parent().parent()
        print self.parent().parent().parent()
        print '--------------------'
        print self.parent().parent().currentIndex()
        self.parent().parent().removeTab(self.parent().parent().currentIndex())


class CGLMenu(QtWidgets.QWidget):
    """
    This creates the top level "Menu" Tab with the "buttons" within it.  Menu is a catch all for "Menus", "Shelves",
    "Preflights", "Context-menus" and anything else in the future that fits the structure we've got here.

    """
    save_clicked = QtCore.Signal()

    def __init__(self, parent=None, software=None, menu_type='menus', menu_name='', menu=None, menu_path=''):
        QtWidgets.QWidget.__init__(self, parent)
        # initialize variables
        self.menu_type = menu_type
        if self.menu_type == 'shelves':
            self.singular = 'shelf'
        elif self.menu_type == 'menus':
            self.singular = 'menu'
        elif self.menu_type == 'preflights':
            self.singular = 'preflight'
        elif self.menu_type == 'context-menus':
            self.singular = 'context-menu'
        else:
            self.singluar = 'not defined'
        self.software = software
        self.menu = menu
        self.menu_name = menu_name
        self.menu_path = menu_path
        self.new_button_widget = None

        # create layouts
        layout = QtWidgets.QVBoxLayout(self)
        title_layout = QtWidgets.QHBoxLayout()
        if menu_type != 'shelves':
            self.buttons_tab_widget = LJTabWidget()
            self.buttons_tab_widget.setProperty('class', 'vertical')
            self.buttons_tab_widget.tabBar().setProperty('class', 'vertical')
        else:
            self.buttons_tab_widget = QtWidgets.QTabWidget()

        self.title = ''
        if self.menu_type == 'menus':
            self.title = QtWidgets.QLabel('%s %s Buttons: (Drag to Reorder)' % (self.menu_name, self.menu_type.title()))
        elif self.menu_type == 'preflights':
            self.title = QtWidgets.QLabel('%s %s Steps: (Drag to Reorder)' % (self.menu_name, self.menu_type.title()))
        elif self.menu_type == 'shelves':
            self.title = QtWidgets.QLabel('%s Shelf Buttons: (Drag to Reorder)' % self.menu_name)
        elif self.menu_type == 'context-menus':
            self.title = QtWidgets.QLabel('Context Menu Buttons: (Drag to Reorder)')
        self.title.setProperty('class', 'title')
        if self.menu_type == 'shelves':
            self.add_button = QtWidgets.QPushButton('add shelf button')
            self.import_menu_button = QtWidgets.QPushButton('import shelf button')
        elif self.menu_type == 'preflights':
            self.add_button = QtWidgets.QPushButton('add preflight step')
            self.import_menu_button = QtWidgets.QPushButton('import preflight step')
        else:
            self.add_button = QtWidgets.QPushButton('add %s button' % self.singular)
            self.import_menu_button = QtWidgets.QPushButton('import %s button' % self.singular)
        self.add_submenu_button = QtWidgets.QPushButton('add submenu')
        self.add_submenu_button.hide()
        self.import_menu_button.hide()
        self.add_button.setProperty('class', 'add_button')
        self.add_submenu_button.setProperty('class', 'add_button')
        self.import_menu_button.setProperty('class', 'add_button')

        # set parameters
        self.buttons_tab_widget.setMovable(True)

        # layout the widget
        title_layout.addWidget(self.title)
        title_layout.addWidget(self.add_submenu_button)
        title_layout.addWidget(self.import_menu_button)
        title_layout.addWidget(self.add_button)
        title_layout.addStretch(1)
        layout.addLayout(title_layout)
        layout.addWidget(self.buttons_tab_widget)

        # connect SIGNALS and SLOTS
        self.add_button.clicked.connect(self.on_add_menu_button)
        self.add_submenu_button.clicked.connect(self.on_submenu_button_clicked)
        self.import_menu_button.clicked.connect(self.on_import_menu_button_clicked)
        self.load_buttons()

    @staticmethod
    def on_import_menu_button_clicked():
        dialog = InputDialog(title="Feature In Progress",
                             message="This button will allow you to import buttons/preflights from other menus")
        dialog.exec_()
        if dialog.button == 'Ok' or dialog.button == 'Cancel':
            dialog.accept()

    @staticmethod
    def on_submenu_button_clicked():
        dialog = InputDialog(title="Feature In Progress",
                             message="This button will allow you to create a submenu!")
        dialog.exec_()
        if dialog.button == 'Ok' or dialog.button == 'Cancel':
            dialog.accept()

    def on_add_menu_button(self):
        if self.menu_type == 'preflights':
            title_ = 'Add Preflight Step'
            message = 'Enter a Name for your Preflight Step'
        elif self.menu_type == 'menus':
            title_ = 'Add Menu'
            message = 'Enter a Name for your Menu Button'
        elif self.menu_type == 'shelves':
            title_ = 'Add Shelf'
            message = 'Enter a Name for your shelf button'
        elif self.menu_type == 'context-menus':
            title_ = 'Add Context Menu Item'
            message = 'Enter a name for your Context Menu Item'

        dialog = InputDialog(title=title_, message=message,
                             line_edit=True, regex='^([A-Z][a-z]+)+$',
                             name_example='class name must be CamelCase - ExamplePreflightName')
        dialog.exec_()
        if dialog.button == 'Ok':
            preflight_name = dialog.line_edit.text()
            command = self.get_command_text(button_name=preflight_name, menu_type=self.menu_type)
            module = self.default_preflight_text(preflight_name)
            if self.menu_type == 'preflights':
                attrs = {'label': preflight_name,
                         'required': 'True',
                         'module': module}
            elif self.menu_type == 'menus' or self.menu_type == 'context-menus':
                attrs = {'label': preflight_name,
                         'module': command}
            elif self.menu_type == 'shelves':
                attrs = {'label': preflight_name,
                         'module': command,
                         'icon': ''}
            self.new_button_widget = CGLMenuButton(parent=self.buttons_tab_widget, preflight_name=self.menu_name,
                                                   preflight_step_name=dialog.line_edit.text(),
                                                   attrs=attrs, preflight_path=self.menu_path, menu_type=self.menu_type)
            self.new_button_widget.save_clicked.connect(self.on_save_clicked)
            if 'icon' in attrs.keys():
                icon = QtGui.QIcon(attrs['icon'])
                index = self.buttons_tab_widget.addTab(self.new_button_widget, icon, preflight_name)
            else:
                index = self.buttons_tab_widget.addTab(self.new_button_widget, preflight_name)
            self.buttons_tab_widget.setCurrentIndex(index)

    def on_save_clicked(self):
        self.save_clicked.emit()

    def get_command_text(self, button_name, menu_type):
        print 'import cgl_tools.%s.%s.%s.%s as %s; %s.run()' % (self.software, menu_type, self.menu_name, button_name,
                                                                 button_name, button_name)
        return 'import cgl_tools.%s.%s.%s.%s as %s; %s.run()' % (self.software, menu_type, self.menu_name, button_name,
                                                                 button_name, button_name)

    def default_preflight_text(self, preflight_name):
        return 'cgl_tools.%s.%s.%s.%s' % (self.software, self.menu_type, self.menu_name, preflight_name)

    def load_buttons(self):
        for i in range(len(self.menu)):
            for button in self.menu:
                if button != 'order':
                    if i == self.menu[button]['order']:
                        button_widget = CGLMenuButton(parent=self.buttons_tab_widget, preflight_name=self.menu_name,
                                                      preflight_step_name=button,
                                                      attrs=self.menu[button], preflight_path=self.menu_path,
                                                      menu_type=self.menu_type)
                        if 'icon' in self.menu[button].keys():
                            if self.menu[button]['icon']:
                                icon = QtGui.QIcon(self.menu[button]['icon'])
                                self.buttons_tab_widget.addTab(button_widget, icon, '')
                            else:
                                self.buttons_tab_widget.addTab(button_widget, button)
                        else:
                            self.buttons_tab_widget.addTab(button_widget, button)












