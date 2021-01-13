import os
import logging
import stringcase
from cgl.ui.widgets.base import LJDialog
from cgl.core.utils.general import cgl_copy
from cgl.core.utils.read_write import load_text_file, save_text_lines
from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.ui.widgets.dialog import InputDialog
from cgl.core.path import start
from cgl.ui.widgets.text import Highlighter
from cgl.ui.widgets.widgets import AdvComboBox



GUI_DICT = {'shelves.yaml': ['button name', 'command', 'icon', 'order', 'annotation', 'label'],
            'pre_publish.yaml': ['order', 'module', 'name', 'required'],
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
    menu_button_save_clicked = QtCore.Signal()

    def __init__(self, parent=None, preflight_name='', preflight_step_name='', attrs=None, preflight_path='',
                 menu_type='pre_publish', menu=None, reference_path=None, cfg=None):
        # TODO - we need to choose better variable names, this is obviously "preflight" specific.
        QtWidgets.QWidget.__init__(self, parent)
        try:
            dialog = self.parent().parent().parent()
            self.software = dialog.software_combo.currentText()
        except AttributeError:
            # TODO - look into this a bit deeper, this is a fairly generic catch right now.
            dialog = self.parent().parent().parent().parent().parent()
            self.software = dialog.software_combo.currentText()
        self.cfg = cfg
        self.menu_type = menu_type
        self.attrs = attrs
        self.name = attrs['name']
        self.preflight_name = preflight_name
        self.preflight_path = preflight_path
        # self.menu_name = os.path.split(preflight_path.split(menu_type)[1])[0]
        self.dirty = False
        self.menu = menu
        self.reference_path = reference_path
        # Create the Layouts
        layout = QtWidgets.QVBoxLayout(self)
        grid_layout = QtWidgets.QGridLayout()
        tool_row = QtWidgets.QHBoxLayout()

        # labels
        module_label = QtWidgets.QLabel('module')
        required_label = QtWidgets.QLabel('required')
        label_label = QtWidgets.QLabel('label')
        icon_button = QtWidgets.QToolButton()
        icon_button.setIcon(QtGui.QIcon(self.cfg.icon_path('folder24px.png')))
        self.icon_label = QtWidgets.QLabel('icon')
        name_label = QtWidgets.QLabel('name')

        # line edits
        self.command_line_edit = QtWidgets.QLineEdit()
        self.command_line_edit.setEnabled(False)
        self.required_line_edit = QtWidgets.QLineEdit()
        self.required_line_edit.setText('True')
        self.icon_path_line_edit = QtWidgets.QLineEdit()
        # self.required_line_edit.setEnabled(False)
        self.label_line_edit = QtWidgets.QLineEdit()
        self.name_line_edit = QtWidgets.QLineEdit()
        self.attrs_dict = {'module': self.command_line_edit,
                           'required': self.required_line_edit,
                           'label': self.label_line_edit,
                           'name': self.name_line_edit,
                           'icon': self.icon_path_line_edit}



        # tool buttons
        delete_button = QtWidgets.QPushButton('Delete')
        delete_button.setProperty('class', 'basic')
        open_button = QtWidgets.QPushButton('Edit')
        open_button.setProperty('class', 'basic')
        copy_button = QtWidgets.QPushButton('Copy Test Code'.format(self.software))
        copy_button.setProperty('class', 'basic')
        self.save_button = QtWidgets.QPushButton('Save')
        self.save_button.setProperty('class', 'basic')

        # Text Edit
        self.code_text_edit = QtWidgets.QPlainTextEdit()
        if reference_path:
            self.code_text_edit.setEnabled(False)
        metrics = QtGui.QFontMetrics(self.code_text_edit.font())
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
        grid_layout.addWidget(name_label, 4, 0)
        grid_layout.addWidget(self.name_line_edit, 4, 1)

        name_label.hide()
        self.name_line_edit.hide()

        if self.menu_type != 'shelves':
            self.icon_label.hide()
            self.icon_path_line_edit.hide()
            icon_button.hide()
        else:
            self.required_line_edit.hide()
            required_label.hide()

        # Layout the tool row
        tool_row.addStretch(1)
        tool_row.addWidget(copy_button)
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
        copy_button.clicked.connect(self.on_copy_button_clicked)
        self.save_button.clicked.connect(self.on_menu_button_save_clicked)
        self.load_attrs()
        self.label_line_edit.textChanged.connect(self.on_code_changed)
        self.dirty = False
        self.save_button.hide()

    def on_copy_button_clicked(self):
        import pyperclip

        name = self.name
        text = 'import cookbook.{}.pre_publish.{}.{} as {}\nreload({})\n\n{}.{}().run()'.format(self.software,
                                                                                                self.preflight_name,
                                                                                                name,
                                                                                                name,
                                                                                                name,
                                                                                                name,
                                                                                                name)
        pyperclip.copy(text)

    def on_icon_button_clicked(self):
        default_folder = os.path.join(self.cfg.cookbook_folder, self.software, self.menu_type, self.preflight_name)
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
        icon = QtGui.QIcon(to_path)
        tab_ = self.parent().parent()
        index_ = tab_.currentIndex()
        tab_.setTabIcon(index_, icon)
        # # display the icon?
        self.on_menu_button_save_clicked()

    def on_menu_button_save_clicked(self):
        if self.reference_path:
            return
        else:
            button_name = self.name
            print(self.menu)
            menu_name = self.menu.menu_name
            menu_type = self.menu.menu_type
            button_file = get_button_path(software=self.software, menu_name=menu_name, button_name=button_name,
                                          menu_type=menu_type, cfg=self.cfg)

            dir_ = os.path.dirname(button_file)
            if not os.path.exists(dir_):
                os.makedirs(dir_)
            make_init_for_folders_in_path(dir_, self.cfg)

            if self.dirty:
                print('Saving {}: {}'.format(button_name, button_file))
                code = self.code_text_edit.document().toPlainText()
                if self.software.lower() == 'unreal':
                    if os.path.exists(button_file):
                        self.dirty = False
                        return
                with open(button_file, 'w+') as x:
                    x.write(code)
                self.dirty = False
            else:
                print('No Changes to Save')

    def on_open_clicked(self):
        code_path = os.path.join(os.path.dirname(self.preflight_path), self.menu_type, self.preflight_name,
                                 '%s.py' % self.name)
        start(code_path)

    def on_code_changed(self):
        self.save_button.show()
        self.dirty = True

    def load_attrs(self):
        """
        Loads the attrs for each "button" in the "Menu".
        :return:
        """
        for attr in self.attrs:
            if attr in self.attrs_dict:
                attr_value = str(self.attrs[attr])
                if attr == 'name':
                    if not str(self.attrs[attr]):
                        split = self.attrs['module'].split()
                        attr_value = split[-1].split('.run()')[0]
                self.attrs_dict[attr].setText(attr_value)
        # load the python file into the text edit
        code_text = self.load_code_text()
        if code_text:
            self.code_text_edit.setPlainText(code_text)
        else:
            self.create_default_button()

    def load_code_text(self):
        if self.software.lower() != 'unreal':
            if not self.reference_path:
                code_path = get_button_path(self.software, self.preflight_name, self.name, menu_type=self.menu_type,
                                            cfg=self.cfg)
            else:
                code_path = self.reference_path
                print('loading code from reference {}'.format(self.reference_path))
            if os.path.exists(code_path):
                try:
                    return open(code_path).read()
                except IOError:
                    with open(code_path, 'w+') as y:
                        y.write("")
                return None
            else:
                print('%s does not exist' % code_path)
        else:
            print('Not loading for Unreal Buttons')

    def create_default_button(self):
        create_button_file(software=self.software, menu_name=self.preflight_name, button_name=self.name,
                           menu_type=self.menu_type, cfg=self.cfg)
        code_text = self.load_code_text()
        if code_text:
            self.code_text_edit.setPlainText(code_text)

    def on_delete_clicked(self):
        menu_widget = self.parent().parent()
        # delete the file
        filepath = menu_widget.currentWidget().command_line_edit.text().replace('.', '\\')
        if 'import ' in filepath:
            filepath = filepath.replace('import ', '')
            filepath = filepath.split(' as ')[0]
            filepath = '{}.py'.format(filepath)
        else:
            print('not sure what to do with non-python filepath {}'.format(filepath))
        filepath = os.path.join(os.path.dirname(self.cfg.cookbook_folder), filepath)
        if os.path.exists(filepath):
            print('Deleting the file: {}'.format(filepath))
            # os.remove(filepath)
        else:
            print('File Does Not Exist: {}'.format(filepath))
        self.parent().parent().removeTab(self.parent().parent().currentIndex())


class CGLMenu(QtWidgets.QWidget):
    """
    This creates the top level "Menu" Tab with the "buttons" within it.  Menu is a catch all for "Menus", "Shelves",
    "pre_publish", "Context-menus" and anything else in the future that fits the structure we've got here.

    """
    menu_button_save_clicked = QtCore.Signal(object)

    def __init__(self, parent=None, software=None, menu_type='menus', menu_name='', menu=None, menu_path='', cfg=None):
        QtWidgets.QWidget.__init__(self, parent)
        # initialize variables
        self.menu_type = menu_type
        if self.menu_type == 'shelves':
            self.singular = 'shelf'
        elif self.menu_type == 'menus':
            self.singular = 'menu'
        elif self.menu_type == 'pre_publish':
            self.singular = 'preflight'
        elif self.menu_type == 'context-menus':
            self.singular = 'context-menu'
        else:
            self.singluar = 'not defined'
        self.software = software
        self.cfg = cfg
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
        elif self.menu_type == 'pre_publish':
            self.title = QtWidgets.QLabel('%s %s Steps: (Drag to Reorder)' % (self.menu_name, self.menu_type.title()))
        elif self.menu_type == 'pre_render':
            self.title = QtWidgets.QLabel('%s %s Steps: (Drag to Reorder)' % (self.menu_name, self.menu_type.title()))
        elif self.menu_type == 'tasks':
            self.title = QtWidgets.QLabel('')
        elif self.menu_type == 'shelves':
            self.title = QtWidgets.QLabel('%s Shelf Buttons: (Drag to Reorder)' % self.menu_name)
        elif self.menu_type == 'context-menus':
            self.title = QtWidgets.QLabel('Context Menu Buttons: (Drag to Reorder)')
        self.title.setProperty('class', 'title')
        if self.menu_type == 'shelves':
            self.add_button = QtWidgets.QPushButton('add shelf button')
            self.import_menu_button = QtWidgets.QPushButton('import shelf button')
        elif self.menu_type == 'pre_publish':
            self.add_button = QtWidgets.QPushButton('add step')
            self.import_menu_button = QtWidgets.QPushButton('import pre_publish step')
        elif self.menu_type == 'pre_render':
            self.add_button = QtWidgets.QPushButton('add step')
            self.import_menu_button = QtWidgets.QPushButton('import pre_render step')
        elif self.menu_type == 'tasks':
            self.add_button = QtWidgets.QPushButton('add task')
            self.import_menu_button = QtWidgets.QPushButton('import task')
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
                             message="This button will allow you to import buttons/pre_publish from other menus")
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
        if self.menu_type == 'tasks':
            self.schema = get_schema(self.cfg)
            singular = 'Task'
            dialog = InputDialog(title='Add %s' % singular,
                                 message='Choose Task to Create a %s Recipe For\n '
                                         'Or Type to Create Your Own' % singular,
                                 line_edit=False, combo_box_items=task_list(), regex='[a-zA-Z]',
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
            return
        elif self.menu_type == 'pre_publish':
            title_ = 'Add Preflight Step'
            message = 'Enter a Name for your Preflight Step'
        elif self.menu_type == 'menus':
            title_ = 'Add Menu'
            message = 'Enter a Name for your Menu Button'
        elif self.menu_type == 'shelves':
            title_ = 'Add Shelf'
            message = 'Enter a Name for your Shelf button'
        elif self.menu_type == 'context-menus':
            title_ = 'Add Context Menu Item'
            message = 'Enter a name for your Context Menu Item'

        dialog = NewButtonDialog(software=self.software, menu_type=self.menu_type, menu_name=self.menu_name,
                                 cfg=self.cfg)
        dialog.exec_()
        if dialog.button == 'Ok':
            text_ = stringcase.snakecase(dialog.button_name_line_edit.text().lower())
            button_name = stringcase.pascalcase(text_)
            label = stringcase.titlecase(text_)
            if dialog.cgl_button_type == 'New':
                command = self.get_command_text(button_name=button_name, menu_type=self.menu_type)
                module = self.default_preflight_text(button_name)
                module_path = None
            elif dialog.cgl_button_type == 'Referenced':
                command = dialog.command
                module = dialog.module
                module_path = dialog.button_path

            if self.menu_type == 'pre_publish' or self.menu_type == 'pre_render':
                attrs = {'label': label,
                         'name': button_name,
                         'required': 'True',
                         'module': module,
                         'reference_path': module_path}
            elif self.menu_type == 'menus' or self.menu_type == 'context-menus':
                attrs = {'label': label,
                         'name': button_name,
                         'module': command,
                         'reference_path': module_path}
            elif self.menu_type == 'shelves':
                attrs = {'label': label,
                         'name': button_name,
                         'module': command,
                         'icon': '',
                         'reference_path': module_path}

            self.new_button_widget = CGLMenuButton(parent=self.buttons_tab_widget, preflight_name=self.menu_name,
                                                   preflight_step_name=button_name, menu=self,
                                                   attrs=attrs, preflight_path=self.menu_path, menu_type=self.menu_type,
                                                   reference_path=module_path, cfg=self.cfg)
            if 'icon' in attrs.keys():
                icon = QtGui.QIcon(attrs['icon'])
                index = self.buttons_tab_widget.addTab(self.new_button_widget, icon, button_name)
            else:
                index = self.buttons_tab_widget.addTab(self.new_button_widget, button_name)
            self.buttons_tab_widget.setCurrentIndex(index)

    def do_add_task(self, task_name):
        print('Adding Task {}'.format(task_name))
        module = 'cgl_tools.%s.tasks.tasks.%s' % (self.software, task_name)
        attrs = {'label': task_name,
                 'name': task_name,
                 'module': module
                 }
        self.new_button_widget = CGLMenuButton(parent=self.buttons_tab_widget, preflight_name='tasks',
                                               preflight_step_name=task_name, menu=self,
                                               attrs=attrs, preflight_path=self.menu_path, menu_type=self.menu_type,
                                               cfg=self.cfg)
        # TODO - make sure that a smart_task.py file exists in the folder.
        smart_task_path = self.menu_path.replace('.cgl', '\\tasks\\smart_task.py')
        if not os.path.exists(smart_task_path):
            template_path = (os.path.join(self.cfg.get_cgl_resources_path(), 'alchemists_cookbook', 'default', 'smart_task.py'))
            template_lines = load_text_file(template_path)
            changed_lines = []
            for l in template_lines:
                if 'SOFTWARE' in l:
                    new_l = l.replace('SOFTWARE', self.software)
                    changed_lines.append(new_l)
                else:
                    changed_lines.append(l)
            save_text_lines(changed_lines, smart_task_path)
            # TODO - replace 'SOFTWARE' with self.software in the smart_task.py file.
        index = self.buttons_tab_widget.addTab(self.new_button_widget, task_name)
        self.buttons_tab_widget.setCurrentIndex(index)

    def get_command_text(self, button_name, menu_type):
        if self.software.lower() == 'unreal':
            return "/cgl_tools/{}/{}/{}/{}.uasset".format(self.software, menu_type, self.menu_name, button_name)
        else:
            return 'import cgl_tools.%s.%s.%s.%s as %s; %s.run()' % (self.software, menu_type, self.menu_name, button_name,
                                                                     button_name, button_name)

    def default_preflight_text(self, preflight_name):
        return 'cookbook.%s.%s.%s.%s' % (self.software, self.menu_type, self.menu_name, preflight_name)

    def load_buttons(self):
        if self.menu:
            if 'buttons' in self.menu.keys():
                for button in self.menu['buttons']:
                    try:
                        ref_path = button['reference_path']
                    except KeyError:
                        ref_path = None
                    button_widget = CGLMenuButton(parent=self.buttons_tab_widget, preflight_name=self.menu_name,
                                                  preflight_step_name=button['label'],
                                                  attrs=button, preflight_path=self.menu_path,
                                                  menu_type=self.menu_type, menu=self, reference_path=ref_path,
                                                  cfg=self.cfg)
                    if 'icon' in button.keys():
                        if button['icon']:
                            icon = QtGui.QIcon(button['icon'])
                            self.buttons_tab_widget.addTab(button_widget, icon, button['name'])
                        else:
                            self.buttons_tab_widget.addTab(button_widget, button['name'])
                    else:
                        self.buttons_tab_widget.addTab(button_widget, button['name'])
            else:
                for i in range(len(self.menu)):
                    for button in self.menu:
                        if button != 'order':
                            if i == self.menu[button]['order']:
                                button_widget = CGLMenuButton(parent=self.buttons_tab_widget, preflight_name=self.menu_name,
                                                              preflight_step_name=button,
                                                              attrs=self.menu[button], preflight_path=self.menu_path,
                                                              menu_type=self.menu_type, menu=self, cfg=self.cfg)
                                if 'icon' in self.menu[button].keys():
                                    if self.menu[button]['icon']:
                                        icon = QtGui.QIcon(self.menu[button]['icon'])
                                        self.buttons_tab_widget.addTab(button_widget, icon, self.menu[button]['name'])
                                    else:
                                        self.buttons_tab_widget.addTab(button_widget, button)
                                else:
                                    self.buttons_tab_widget.addTab(button_widget, button)


def create_button_file(software, menu_name, button_name, menu_type, cfg):
    button_path = get_button_path(software, menu_name, button_name, menu_type=menu_type, cfg=cfg)
    if software == 'lumbermill':
        template_software = 'lumbermill'
    elif software == 'blender':
        template_software = 'blender'
    elif software.lower() == 'unreal':
        template_software = 'unreal'
    else:
        template_software = 'default'
    if software.lower() == 'unreal':
        button_template = os.path.join(cfg.get_cgl_resources_path(), 'alchemists_cookbook', template_software, 'buttons',
                                       'for_%s.uasset' % menu_type)
        dirname = os.path.dirname(button_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        # copy button_template to button_path
        print('Copying {} to {}'.format(button_template, button_path))
        cgl_copy(button_template, button_path)
        return
    else:
        button_template = os.path.join(cfg.get_cgl_resources_path(), 'alchemists_cookbook',
                                       template_software, 'buttons',
                                       'for_%s.py' % menu_type)
    button_lines = load_text_file(button_template)
    changed_lines = []
    for l in button_lines:
        if software == 'blender':
            if l.startswith('class ButtonTemplate'):
                new_l = l.replace('ButtonTemplate', button_name)
                changed_lines.append(new_l)
            elif 'object.button_template' in l:
                new_l = l.replace('button_template', stringcase.snakecase(button_name))
                changed_lines.append(new_l)
            elif 'bl_label' in l:
                new_l = l.replace('button_template', stringcase.titlecase(button_name))
                changed_lines.append(new_l)
            elif 'print' in l:
                new_l = l.replace('button_template', stringcase.titlecase(button_name))
                new_l = l.replace('PreflightTemplate', stringcase.titlecase(button_name))
                changed_lines.append(new_l)
            elif 'PreflightTemplate' in l:
                new_l = l.replace('PreflightTemplate', stringcase.titlecase(button_name))
                changed_lines.append(new_l)
            else:
                changed_lines.append(l)
        else:
            if 'print' in l:
                new_l = l.replace('button_template', stringcase.titlecase(button_name))
                changed_lines.append(new_l)
            elif 'PreflightTemplate' in l:
                new_l = l.replace('PreflightTemplate', button_name)
                changed_lines.append(new_l)
            elif 'SOFTWARE' in l:
                new_l = l.replace('SOFTWARE', software)
                changed_lines.append(new_l)
            else:
                changed_lines.append(l)
    dirname = os.path.dirname(button_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    save_text_lines(changed_lines, button_path)
    return button_path


def get_menu_path(software, menu_name, menu_file=False, menu_type='menus', cfg=None):
    """
    returns the menu path for a menu with the given name
    :param software: software package to get the menu path for.
    :param menu_name: CamelCase string - all menus created with pipeline designer are CamelCase
    :param menu_file: if True returns a menu path with a menu_name.py file.
    :param menu_type: menus, pre_publish, shelves, context-menus
    :return:
    """
    cfg = cfg
    if menu_file:
        menu_folder = os.path.join(cfg.cookbook_folder, software, menu_type, menu_name, '%s.py' % menu_name)
    else:
        logging.debug("software: {}".format(software),
                      "menu type: {}".format(menu_type),
                      "menu_name: {}".format(menu_name))
        menu_folder = os.path.join(cfg.cookbook_folder, software, menu_type, menu_name)
        print(menu_folder)
    return menu_folder


def get_button_path(software, menu_name, button_name, menu_type='menus', cfg=None):
    """

    :param software: software as it appears in pipeline designer.
    :param menu_name: CamelCase menu name
    :param button_name: CamelCase button name
    :param menu_type: menus, pre_publish, shelves, context-menus
    :return:
    """
    if isinstance(menu_name, dict):
        menu_name = menu_name['name']
    menu_folder = get_menu_path(software, menu_name, menu_type=menu_type, cfg=cfg)
    if software.lower() == 'unreal':
        button_path = os.path.join(menu_folder, '%s.uasset' % button_name)
    else:
        button_path = os.path.join(menu_folder, '%s.py' % button_name)
    return button_path


def make_init_for_folders_in_path(folder, cfg):
    config = cfg.cookbook_folder.replace('\\', '/')
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
                        make_init(os.path.dirname(init))


def make_init(folder):
    if '*' not in folder:
        with open(os.path.join(folder, '__init__.py'), 'w+') as i:
            i.write("")


class NewButtonDialog(LJDialog):
    def __init__(self, parent=None, software=None, menu_type=None, menu_name=None, cfg=None):
        LJDialog.__init__(self, parent)
        self.cfg = cfg
        self.software = software
        self.cgl_button_type = 'New Button'
        self.menu_type = menu_type
        self.module = None
        self.command = None
        self.button_path = None
        layout = QtWidgets.QVBoxLayout(self)
        self.setWindowTitle('New Pipeline Button')
        self.reference_button_label = QtWidgets.QLabel()
        self.reference_button_label.setProperty('class', 'title')
        self.reference_button_label.hide()
        combo_label = QtWidgets.QLabel("Button Type: ")
        self.reference_combo_label = QtWidgets.QLabel('Reference :')
        self.button_type = QtWidgets.QComboBox()
        self.reference_buttons = AdvComboBox()
        self.menu_name = menu_name
        self.menu_types = ['menus', 'context-menus', 'shelves', 'pre_publish']
        self.menu_directory = os.path.join(self.cfg.cookbook_folder, self.software, self.menu_type)
        self.button_type.addItems(['New', 'Referenced'])
        self.new_button_label = QtWidgets.QLabel()
        self.button_name_line_edit = QtWidgets.QLineEdit()
        self.ok_button = QtWidgets.QPushButton('Ok')
        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.button = 'Cancel'

        grid = QtWidgets.QGridLayout()

        grid.addWidget(combo_label, 0, 0)
        grid.addWidget(self.button_type, 0, 1)
        grid.addWidget(self.reference_combo_label, 1, 0)
        grid.addWidget(self.reference_buttons, 1, 1)
        grid.addWidget(self.new_button_label, 2, 0)
        grid.addWidget(self.button_name_line_edit, 2, 1)

        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self.cancel_button)
        button_row.addWidget(self.ok_button)

        layout.addLayout(grid)
        layout.addLayout(button_row)

        self.reference_buttons.hide()
        self.reference_combo_label.hide()

        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.button_type.currentIndexChanged.connect(self.on_type_changed)
        self.reference_buttons.currentTextChanged.connect(self.on_reference_button_selected)
        self.on_type_changed()
        self.load_buttons_for_reference()

    def load_buttons_for_reference(self):
        """
        loads all available buttons into the adv combo box.
        :return:
        """
        self.reference_buttons.clear()
        self.reference_buttons.addItem('')
        print('loading buttons from {}'.format(self.menu_directory))
        for root, dirs, files in os.walk(self.menu_directory):
            for name in files:
                if self.menu_name not in root:
                    if name.endswith('.py'):
                        if '__init__' not in name:
                            button_name = '{}/{}'.format(os.path.basename(root), name)
                            self.reference_buttons.addItem(button_name)

    def on_reference_button_selected(self):
        """

        :return:
        """
        button_text = self.reference_buttons.currentText()
        if '.py' in button_text:
            menu, button = os.path.split(button_text)
            button_name = button.replace('.py', '')
            full_button_path = os.path.join(self.menu_directory, menu, button)
            splitted = full_button_path.split('_config')[-1].split('\\')
            if splitted[0] == '':
                splitted.pop(0)
            module = '.'.join(splitted).replace('.py', '')
            command = 'import {} as {}; {}.run()'.format(module, button_name, button_name)
            self.button_path = full_button_path
            self.module = module
            self.command = command
            self.button_name_line_edit.setText(button_name)
            print(self.button_path)
            print(self.module)
            print(self.command)

    def on_type_changed(self):
        """
        when the type changes, change the text
        :return:
        """
        self.new_button_label.setText('Button Name'.format(self.button_type.currentText()))
        self.cgl_button_type = self.button_type.currentText()
        if self.cgl_button_type == 'Referenced':
            self.reference_buttons.show()
            self.reference_combo_label.show()
            # dialog = QtWidgets.QFileDialog()
            # dialog.title = 'Choose a Button To Reference'
            # dialog.setDirectory(os.path.join(get_cgl_tools(), self.software, self.menu_type))
            # if dialog.exec_():
            #     file_names = dialog.selectedFiles()
            #     if file_names:
            #         button_path = file_names[0]
            #         splitted = button_path.split('_config')[-1].split('/')
            #         if splitted[0] == '':
            #             splitted.pop(0)
            #         filename = splitted[-1].replace('.py', '')
            #         module = '.'.join(splitted).replace('.py', '')
            #         from_label = "Referencing: {}".format(module)
            #         command = 'import {} as {}; {}.run()'.format(module, filename, filename)
            #         self.reference_button_label.setText(from_label)
            #         self.reference_button_label.show()
            #         self.button_path = button_path
            #         self.module = module
            #         self.command = command
        else:
            self.reference_buttons.hide()
            self.reference_combo_label.hide()

    def on_ok_clicked(self):
        self.button = 'Ok'
        self.accept()

    def on_cancel_clicked(self):
        self.accept()

    def load_buttons(self):
        print(self.menu_types_combo.currentText())


def get_schema(cfg):
    config = cfg.project_config
    proj_man = config['account_info']['project_management']
    def_schema = config['project_management'][proj_man]['api']['default_schema']
    schema = config['project_management'][proj_man]['tasks'][def_schema]
    return schema


def task_list(cfg):
    schema = get_schema(cfg)
    task_list = []
    try:
        for each in schema['long_to_short']['assets']:
            if each not in task_list:
                task_list.append(each)
        for each in schema['long_to_short']['shots']:
            if each not in task_list:
                task_list.append(each)
    except TypeError:
        print('Problems found in your globals "schema"')
        return
    task_list.sort()
    task_list.insert(0, '')
    return task_list





