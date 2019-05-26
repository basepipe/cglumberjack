from Qt import QtCore
from Qt import QtWidgets
from Qt import QtGui
import sys
import yaml
import os
import re
import datetime
from cglcore.util import current_user, test_string_against_rules
#from cglcore import lj_mail
from cglcore.config import app_config, user_config
#from cglcore import screen_grab
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.widgets import AdvComboBox
from cglui.widgets.containers.table import LJTableWidget
from cglui.widgets.containers.menu import LJMenu
from cglui.widgets.base import LJDialog


class FileTableModel(ListItemModel):
    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == QtCore.Qt.DisplayRole:
            return self.data_[row][col]


class ItemTable(LJTableWidget):
    delete_item_signal = QtCore.Signal()
    rename_item_signal = QtCore.Signal()
    show_in_folder_signal = QtCore.Signal()
    show_in_shotgun_signal = QtCore.Signal()

    def __init__(self, parent, title):
        LJTableWidget.__init__(self, parent)
        self.item_right_click_menu = LJMenu(self)
        self.label = title
        self.clicked.connect(self.row_selected)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.item_right_click_menu.create_action("Show in Folder", self.show_in_folder_signal)
        self.item_right_click_menu.create_action("Show in Shotgun", self.show_in_shotgun_signal)
        # self.item_right_click_menu.create_action("Delete", self.delete_item_signal)
        self.customContextMenuRequested.connect(self.item_right_click)

    def item_right_click(self, position):
        self.item_right_click_menu.exec_(self.mapToGlobal(position))


class MagicList(LJDialog):
    """
    Magic List is an incredibly useful dialog that allows you a lot of flexibility when creating custom "list" dialogs
    """
    combo_changed_signal = QtCore.Signal()
    item_selected = QtCore.Signal(object)
    button_name = ''
    button_signal = QtCore.Signal(object)

    def __init__(self, parent=None, title='Dialog Title', list_items=None, buttons=None, message=None,
                 combo_box=None, combo_label='Label', combo=False, button_functions=None, auto_close=True,
                 on_selection=None, on_button_clicked=None):
        """

        :param parent: Parent GUI
        :param title: Title of the Gui
        :param list_items: Items that will go into the table view
        :param buttons: List of buttons that will be created - up to 4 allowed
        :param combo_box: List of items to populate the combo_box
        :param combo_label: Label for the combo_box
        :param combo: If False combo_box is hidden, if True it is displayed
        :param button_functions: Allows for a list of static methods that correspond to the button list
        :param auto_close: Closes the dialog after button is pushed
        """
        LJDialog.__init__(self, parent)
        if list_items is None:
            list_items = []
        if buttons is None:
            buttons = []
        if combo_box is None:
            combo_box = []
        self.auto_close = auto_close
        self.selection = None
        self.setMinimumWidth(600)
        self.list_items = list_items
        self.button_functions = button_functions
        self.user_buttons = buttons
        self.combo_defaults = combo_box
        self.root_path = app_config()['paths']['root']
        self.v_layout = QtWidgets.QVBoxLayout(self)
        self.combo_row = QtWidgets.QHBoxLayout(self)
        self.combo_label = QtWidgets.QLabel("<b>%s</b>" % combo_label)
        self.message = QtWidgets.QLabel("\n\n%s\n\n" % message)
        self.combo = AdvComboBox(self)
        self.combo_row.addWidget(self.combo_label)
        self.combo_row.addWidget(self.combo)
        if not combo:
            self.combo_label.hide()
            self.combo.hide()
        self.buttons = QtWidgets.QHBoxLayout(self)
        self.button1 = QtWidgets.QPushButton('Button1')
        self.button2 = QtWidgets.QPushButton('Button2')
        self.button3 = QtWidgets.QPushButton('Button3')
        self.button4 = QtWidgets.QPushButton('Button4')
        button_list = [self.button1, self.button2, self.button3, self.button4]
        for i in range(len(buttons)):
            button_list[i].setText(buttons[i])
            self.buttons.addWidget(button_list[i])

        self.data_table = LJTableWidget(self)
        self.data_table.set_item_model(FileTableModel([], [""]))
        self.data_table.selected.connect(self.on_selected)

        self.v_layout.addLayout(self.combo_row)
        self.v_layout.addWidget(self.data_table)
        if message:
            self.v_layout.addWidget(self.message)
        self.v_layout.addLayout(self.buttons)

        self.setLayout(self.v_layout)
        self.setWindowTitle(title)
        self.load_combo()
        self.load_items()

        self.combo.currentIndexChanged.connect(self.on_combo_changed)
        self.button1.clicked.connect(self.on_button_clicked)
        self.button2.clicked.connect(self.on_button_clicked)
        self.button3.clicked.connect(self.on_button_clicked)
        self.button4.clicked.connect(self.on_button_clicked)
        if on_button_clicked:
            self.button_signal.connect(on_button_clicked)
        if on_selection:
            self.item_selected.connect(on_selection)

    def on_button_clicked(self):
        if self.button_functions:
            position = self.user_buttons.index(self.sender().text())
            self.button_functions[position]()
        else:
            self.button_name = self.sender().text()
            data = [self.sender(), self.selection]
            self.button_signal.emit(data)
            self.accept()

    def load_combo(self):
        if self.combo_defaults:
            self.combo.addItem('')
            for item in self.combo_defaults:
                self.combo.addItem(item)

    def load_items(self):
        """
        loads items, set up initially to handle a list only.
        :return:
        """
        items = []
        for each in self.list_items:
            items.append([each])
        self.data_table.set_item_model(FileTableModel(items, ['']))

    def on_combo_changed(self):
        self.combo_changed_signal.emit()

    def on_selected(self, data):
        print 'on selected', data
        self.selection = data
        self.item_selected.emit(data)


class FrameRange(LJDialog):
    cancel_signal = QtCore.Signal()
    button = True

    def __init__(self, parent=None, title="Frame Range", sframe=None, eframe=None, camera=None):
        LJDialog.__init__(self, parent)
        layout = QtWidgets.QFormLayout()
        hlayout = QtWidgets.QHBoxLayout()
        blayout = QtWidgets.QHBoxLayout()
        self.sframe = sframe
        self.eframe = eframe
        if camera:
            self.title = '%s for: %s' % (title, camera)
        else:
            self.title = title
        self.sframe_label = QtWidgets.QLabel('Start Frame')
        self.eframe_label = QtWidgets.QLabel('End Frame')
        self.sframe_line_edit = QtWidgets.QLineEdit()
        self.eframe_line_edit = QtWidgets.QLineEdit()
        if sframe:
            print sframe, 'yup'
            self.sframe_line_edit.setText(str(sframe))
        if eframe:
            self.eframe_line_edit.setText(str(eframe))
        hlayout.addWidget(self.sframe_label)
        hlayout.addWidget(self.sframe_line_edit)
        hlayout.addWidget(self.eframe_label)
        hlayout.addWidget(self.eframe_line_edit)
        self.button_cancel = QtWidgets.QPushButton('Cancel')
        self.button = QtWidgets.QPushButton('Confirm Frame Range')
        blayout.addWidget(self.button_cancel)
        blayout.addWidget(self.button)
        layout.addRow(hlayout)
        layout.addRow(blayout)
        self.setLayout(layout)
        self.setWindowTitle(self.title)

        self.button.clicked.connect(self.on_button_clicked)
        self.button_cancel.clicked.connect(self.cancel_clicked)

    def cancel_clicked(self):
        self.button = False
        self.cancel_signal.emit()
        self.accept()

    def on_button_clicked(self):
        self.button = True
        sframe = self.sframe_line_edit.text()
        eframe = self.eframe_line_edit.text()
        if sframe:
            if eframe:
                self.eframe = eframe
                self.sframe = sframe
                self.accept()
            else:
                print 'No end frame defined'
        else:
            print 'No Start Frame Defined'


class InputDialog(LJDialog):
    button_clicked = QtCore.Signal(object)

    def __init__(self, parent=None, title='Title', message="message",
                 buttons=None, line_edit=False, line_edit_text=False, combo_box_items=None,
                 combo_box2_items=None, regex=None, name_example=None):
        """
        Meant to be a catch all dialog for handling just about anything.  It can handle 3 buttons
        :param parent:
        :param message:
        """
        LJDialog.__init__(self, parent)
        if buttons is None:
            buttons = ['Cancel', 'Ok', '']
        layout = QtWidgets.QFormLayout()
        button_box = QtWidgets.QHBoxLayout()
        self.name_example = name_example
        self.regex = regex
        self.values = ''
        self.button = ''
        self.input_text = ''
        self.message = QtWidgets.QLabel(message)
        self.combo_box = AdvComboBox(self)
        self.combo_box2 = AdvComboBox(self)
        self.line_edit = QtWidgets.QLineEdit()
        if line_edit_text:
            self.line_edit.setText(line_edit_text)
        layout.addRow(self.message)
        layout.addRow(self.combo_box)
        self.combo_box.hide()
        layout.addRow(self.combo_box2)
        self.combo_box2.hide()
        if combo_box_items:
            self.combo_box.addItems(combo_box_items)
            self.combo_box.show()
        if combo_box2_items:
            self.combo_box2.addItems(combo_box2_items)
            self.combo_box2.show()
        if line_edit:
            layout.addRow(self.line_edit)
        if buttons:
            i = len(buttons)
            while i < 3:
                buttons.append('')
                i += 1
            self.btn1 = QtWidgets.QPushButton(buttons[0])
            self.btn2 = QtWidgets.QPushButton(buttons[1])
            self.btn3 = QtWidgets.QPushButton(buttons[2])
            button_box.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))

            button_box.addWidget(self.btn1)
            if buttons[1]:
                button_box.addWidget(self.btn2)
            if buttons[2]:
                button_box.addWidget(self.btn3)
            layout.addRow(button_box)
        self.setLayout(layout)
        self.setWindowTitle(title)

        self.btn1.clicked.connect(self.on_button_clicked)
        self.btn1.clicked.connect(self.close)
        self.btn2.clicked.connect(self.on_button_clicked)
        self.btn2.clicked.connect(self.close)
        self.btn3.clicked.connect(self.on_button_clicked)
        self.btn3.clicked.connect(self.close)
        if regex:
            self.line_edit.textChanged.connect(self.on_text_changed_regex)

    def on_button_clicked(self):
        self.button = self.sender().text()
        self.input_text = self.line_edit.text()

    def on_text_changed_regex(self):
        if self.line_edit.text():
            if re.match(self.regex, self.line_edit.text()):
                message = '%s Passes! Click Rename' % self.line_edit.text()
            else:
                bad_name = '%s does not pass' % (self.line_edit.text())
                message = '%s\n%s' % (bad_name, self.name_example)
            self.message.setText(message)


class PlaylistDialog(InputDialog):
    def __init__(self, parent=None, project_name=None):
        InputDialog.__init__(self, parent, title='Add To Playlist', message='Choose a day for review',
                             combo_box_items=['Today', 'Tomorrow'])
        self.day = "Today"
        self.project_name = project_name
        self.playlist_name = None
        self.playlist = {}
        self.on_day_chosen()
        self.combo_box.currentIndexChanged.connect(self.on_day_chosen)

    def on_day_chosen(self):
        self.day = self.combo_box.currentText()
        if self.day == 'Today':
            self.playlist_name = '%s_%s' % (self.project_name, datetime.date.today())
        if self.day == 'Tomorrow':
            tomorrow_date = datetime.date.today() + datetime.timedelta(days=1)
            self.playlist_name = '%s_%s' % (self.project_name, tomorrow_date)


class ReportBugDialog(LJDialog):

    def __init__(self, parent=None, title='Report A Bug'):
        LJDialog.__init__(self, parent)
        self.title_ = parent.windowTitle()
        layout = QtWidgets.QFormLayout()
        self.attachments = []
        icon_path = os.path.join(app_config()['paths']['code_root'], 'resources', 'images')
        # define the user name area
        h_box_layout_username = QtWidgets.QHBoxLayout()
        self.label_username = QtWidgets.QLabel('Username')
        self.lineEdit_username = QtWidgets.QLineEdit()
        h_box_layout_username.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        h_box_layout_username.addWidget(self.label_username)
        h_box_layout_username.addWidget(self.lineEdit_username)

        # define the email area
        h_box_layout_email = QtWidgets.QHBoxLayout()
        self.label_email = QtWidgets.QLabel('Email')
        self.lineEdit_email = QtWidgets.QLineEdit()
        h_box_layout_email.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        h_box_layout_email.addWidget(self.label_email)
        h_box_layout_email.addWidget(self.lineEdit_email)

        # define the software area
        h_box_layout_software = QtWidgets.QHBoxLayout()
        self.label_messaging = QtWidgets.QLabel('*All fields must have valid values')
        self.label_messaging.setStyleSheet('color: red')
        self.label_software = QtWidgets.QLabel('Software')
        self.label_description = QtWidgets.QLabel('Description of Issue:')
        self.lineEdit_software = QtWidgets.QLineEdit()
        h_box_layout_software.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        h_box_layout_software.addWidget(self.label_software)
        h_box_layout_software.addWidget(self.lineEdit_software)

        h_box_layout_subject = QtWidgets.QHBoxLayout()
        self.label_subject = QtWidgets.QLabel('Subject')
        self.lineEdit_subject = QtWidgets.QLineEdit()
        h_box_layout_subject.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        h_box_layout_subject.addWidget(self.label_subject)
        h_box_layout_subject.addWidget(self.lineEdit_subject)

        self.text_edit = QtWidgets.QTextEdit()
        self.screengrabs_layout = QtWidgets.QVBoxLayout()

        button_bar = QtWidgets.QHBoxLayout()
        self.paperclip_icon = os.path.join(icon_path, 'paperclip.png')
        self.screen_grab_icon = os.path.join(icon_path, 'screen_grab24px.png')
        self.button_add_screen_grab = QtWidgets.QPushButton('')
        self.button_attachment = QtWidgets.QPushButton('')
        self.button_attachment.setIcon(QtGui.QIcon(self.paperclip_icon))
        self.button_attachment.setIconSize(QtCore.QSize(24, 24))

        self.button_add_screen_grab.setIcon(QtGui.QIcon(self.screen_grab_icon))
        self.button_add_screen_grab.setIconSize(QtCore.QSize(24, 24))
        # self.button_add_screen_grab.setEnabled(False)
        self.button_submit = QtWidgets.QPushButton('Submit')
        button_bar.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        button_bar.addWidget(self.button_add_screen_grab)
        button_bar.addWidget(self.button_attachment)
        button_bar.addWidget(self.button_submit)

        layout.addRow(h_box_layout_username)
        layout.addRow(h_box_layout_email)
        layout.addRow(h_box_layout_software)
        layout.addRow(h_box_layout_subject)
        layout.addRow(self.label_description)
        layout.addRow(self.text_edit)
        layout.addRow(self.screengrabs_layout)
        layout.addRow(self.label_messaging)
        layout.addRow(button_bar)
        self.setLayout(layout)
        self.setWindowTitle(title)

        self.button_submit.setEnabled(False)
        self.lineEdit_username.setText(current_user())
        self.lineEdit_software.setText(self.title_)
        self.button_submit.clicked.connect(self.send_email)
        self.button_attachment.clicked.connect(self.add_attachments)
        self.lineEdit_username.textChanged.connect(self.ok_to_send)
        self.lineEdit_subject.textChanged.connect(self.ok_to_send)
        self.lineEdit_email.textChanged.connect(self.ok_to_send)
        self.lineEdit_software.textChanged.connect(self.ok_to_send)
        self.text_edit.textChanged.connect(self.ok_to_send)
        self.button_add_screen_grab.clicked.connect(self.screen_grab)

    def get_username(self):
        return self.lineEdit_username.text()

    def get_email(self):
        return self.lineEdit_email.text()

    def get_software(self):
        return self.lineEdit_software.text()

    def get_subject(self):
        return self.lineEdit_subject.text()

    def get_message(self):
        return self.text_edit.toPlainText()

    def add_attachments(self, file_paths=None):
        if not file_paths:
            default_folder = os.path.expanduser(r'~/Desktop')
            file_paths = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose a File to Attach', default_folder, "*")
        for each in file_paths:
            if os.path.isfile(each):
                filename = os.path.split(each)
                self.attachments.append(each)
                label = QtWidgets.QLabel("<html><img src=%s> %s </html>" % (self.paperclip_icon, (filename[-1])))
                self.screengrabs_layout.addWidget(label)
        return file_paths

    def ok_to_send(self):
        message = self.get_message()
        software = self.get_software()
        username = self.get_username()
        email = self.get_email()
        subject = self.get_subject()
        parameters = [username, email, software, subject, message]
        if '' not in parameters:
            self.button_submit.setEnabled(True)
            self.label_messaging.hide()
        else:
            self.label_messaging.show()
            self.button_submit.setEnabled(False)
            self.label_messaging.setText('*All fields must have valid values')

    def send_email(self):
        message = 'Reporter: %s\nContact Email: %s\nSoftware: %s\nMessage: \n%s' % (self.get_username(),
                                                                                    self.get_email(),
                                                                                    self.get_software(),
                                                                                    self.get_message())
        lj_mail.slack_notification_email(type_='bugs', subject=self.get_subject(), message=message,
                                         attachments=self.attachments)
        for each in self.attachments:
            if 'screen_grab' in each:
                os.remove(each)
        self.close()

    def screen_grab(self):
        output_path = screen_grab.run()
        self.add_attachments(file_paths=[output_path])
        return output_path


class ConfirmPublishFiles(LJDialog):
    def __init__(self, parent=None, path_dict=None, title='Confirm Publish Files'):
        from cglcore.path import return_source_render
        self.dict = path_dict
        LJDialog.__init__(self, parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        source, render = return_source_render(path_dict, add_filename=False,
                                              with_root=True)
        self.renamed = False
        self.gui_d = {}
        self.source_files = os.listdir(source)
        self.render_files = os.listdir(render)
        self.channels = ['', 'Specular', 'Base_Color']
        v_layout = QtWidgets.QVBoxLayout()
        self.folder_name = 'bob'
        self.proper_name = 'this_thing'
        self.source_layout = QtWidgets.QVBoxLayout()
        self.render_layout = QtWidgets.QVBoxLayout()
        self.rename_button = QtWidgets.QPushButton('Rename Textures')
        self.button_layout = QtWidgets.QVBoxLayout()
        self.button_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                         QtWidgets.QSizePolicy.Minimum))
        self.button_layout.addWidget(self.rename_button)
        v_layout.addLayout(self.source_layout)
        v_layout.addLayout(self.render_layout)
        v_layout.addLayout(self.button_layout)
        self.load_files(source, self.source_files, self.source_layout, 'Source Files:')
        self.load_files(render, self.render_files, self.render_layout, 'Render Files:', combo=True)
        self.setLayout(v_layout)
        self.setWindowTitle(title)
        self.compare_file_names()
        self.rename_button.clicked.connect(self.on_rename_clicked)
        self.check_rename()

    def on_rename_clicked(self):
        for type_ in self.gui_d:
            for label in self.gui_d[type_]:
                src = os.path.join(type_, self.gui_d[type_][label][0])
                dst = os.path.join(type_, self.gui_d[type_][label][-1])
                if src != dst:
                    os.rename(src, dst)
        self.renamed = True
        self.accept()

    def check_rename(self):
        rename = False
        for type_ in self.gui_d:
            for label in self.gui_d[type_]:
                src = os.path.join(type_, self.gui_d[type_][label][0])
                dst = os.path.join(type_, self.gui_d[type_][label][-1])
                if src != dst:
                    rename = True
        if not rename:
            self.rename_button.setText('All Names Passed - Skip')
            self.renamed = True
            self.close()

    def on_text_changed(self):
        try:
            text = self.sender().text()
        except AttributeError:
            text = self.sender().currentText()
        if text:
            test_string_against_rules(text, 'texture_channel', self.sender().label)
            if text == 'source':
                new_label_text = '%s%s' % (self.dict['shot'], self.sender().ext)
            else:
                new_label_text = '%s_%s%s' % (self.dict['shot'], text, self.sender().ext)
        else:
            new_label_text = self.sender().file
        self.sender().label.setText(new_label_text)
        self.reset_dict_label(self.sender().label, new_label_text)
        self.compare_file_names()

    def load_files(self, folder, files, layout, label, combo=False):
        invalid = ['.thumb']
        label_layout = QtWidgets.QHBoxLayout()
        label_layout.addWidget(QtWidgets.QLabel(label))
        label_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                          QtWidgets.QSizePolicy.Minimum))
        label_layout.addWidget(QtWidgets.QLabel('Custom Name'))
        layout.addLayout(label_layout)
        combo_items = ['']
        texture_dict = {'diffuse': ['diffuse', 'basecolor', 'albedo', 'color'],
                        'specColor': ['speccolor', 'specularcolor', 'specgain'],
                        'specRough': ['specrough', 'specular', 'specularroughness', 'roughness'],
                        'normal': ['normal'],
                        'metallic': ['metallic', 'reflectance'],
                        'height': ['height', 'displacement', 'disp', 'bump'],
                        'occlusion': ['occl', 'occlusion', 'ambientocclusion'],
                        'rmo': ['rmo'],
                        'material': ['.sbsar'],
                        'source': ['.sbs', '.resources']}
        for key in texture_dict:
            combo_items.append(key)
        d = {}
        for s in files:
            default_channel = ''
            if s not in invalid:
                channel = os.path.splitext(s.split('_')[-1])[0]
                ext = os.path.splitext(s.split('_')[-1])[-1]
                for key in texture_dict:
                    if channel.lower() in texture_dict[key]:
                        default_channel = key
                    elif ext.lower() in texture_dict[key]:
                        default_channel = key
                ext = os.path.splitext(s)[-1]
                file_layout = QtWidgets.QHBoxLayout()
                file_checkbox = QtWidgets.QCheckBox()
                file_checkbox.setCheckState(QtCore.Qt.Checked)
                file_label = QtWidgets.QLabel('%s  -->>    ' % s)
                custom_line_edit = QtWidgets.QLineEdit()
                combo_box = AdvComboBox()
                combo_box.addItems(combo_items)
                new_name_label = QtWidgets.QLabel('   %s' % s)
                # d['%s%s' % (proper_name, ext)] = new_name_label
                d[new_name_label] = [s, s]
                #custom_line_edit.proper_name = proper_name
                custom_line_edit.ext = ext
                custom_line_edit.label = new_name_label
                custom_line_edit.checkBox = file_checkbox
                custom_line_edit.file = s
                combo_box.ext = ext
                combo_box.label = new_name_label
                combo_box.checkBox = file_checkbox
                combo_box.file = s
                custom_line_edit.textChanged.connect(self.on_text_changed)
                #combo_box.currentIndexChanged.connect(self.on_text_changed)
                combo_box.editTextChanged.connect(self.on_text_changed)
                file_layout.addWidget(file_checkbox)
                file_layout.addWidget(file_label)
                file_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                          QtWidgets.QSizePolicy.Minimum))
                file_layout.addWidget(new_name_label)
                file_layout.addWidget(custom_line_edit)
                file_layout.addWidget(combo_box)
                layout.addLayout(file_layout)
                if combo:
                    custom_line_edit.hide()
                    combo_box.show()
                    if default_channel:
                        index = combo_box.findText(default_channel)
                        combo_box.setCurrentIndex(index)
                        d[new_name_label] = [s, new_name_label.text()]
                else:
                    if default_channel:
                        custom_line_edit.setText(default_channel)
                        d[new_name_label] = [s, new_name_label.text()]
                    combo_box.hide()
                    custom_line_edit.show()
        self.gui_d.update({folder: d})

    def compare_file_names(self):
        """
        compares the file names of all the textures in the GUI in order to see if there are duplicates.
        :return:
        """
        for key in self.gui_d:
            labels = []
            for k in self.gui_d[key]:
                if self.gui_d[key][k][-1] not in labels:
                    labels.append(self.gui_d[key][k][-1])
                else:
                    k.setStyleSheet("color: rgb(255, 50, 50);")

    def reset_dict_label(self, label, new_text):
        for folder in self.gui_d:
            for k in self.gui_d[folder]:
                if k == label:
                    self.gui_d[folder][k][-1] = new_text


class ShaderSetup(LJDialog):

    def __init__(self, parent=None, material=None, tex_root=None, tx_only=False, default_shader=None):
        LJDialog.__init__(self, parent)
        from tools.maya.base import get_maya_window

        main_maya_window = get_maya_window()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.parent = main_maya_window
        self.material = material
        self.width = 500
        self.shader_dict = app_config()['shaders']
        textures = []
        tex_root_material = r'%s' % os.path.join(tex_root, self.material.split(':')[-1].split('_')[0])
        if os.path.exists(tex_root_material):
            tex_root = tex_root_material
        for t in os.listdir(tex_root):
            if tx_only:
                if t.endswith('tx'):
                    textures.append(t)
            else:
                textures.append(t)
        self.tex_root = tex_root
        shaders = ['']
        for each in self.shader_dict:
            shaders.append(each)
        if len(shaders) == 2:
            shaders.pop(0)
        self.create_shader = QtWidgets.QPushButton('Create Shader')
        v_layout = QtWidgets.QVBoxLayout()
        self.button_row = QtWidgets.QHBoxLayout()
        self.button_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                      QtWidgets.QSizePolicy.Minimum))
        self.button_row.addWidget(self.create_shader)
        self.material_row = QtWidgets.QHBoxLayout()
        if ":" in material:
            material = material.split(':')[-1]
        self.mat_name = QtWidgets.QLabel("<b>%s</b>" % material)
        self.mat_label = QtWidgets.QLabel("Choose a Shader:")
        self.textures_label = QtWidgets.QLabel("<b>Connect Textures</b>")
        self.mat_combo = AdvComboBox()
        self.mat_shaders = shaders
        self.mat_combo.addItems(self.mat_shaders)

        self.material_row.addWidget(self.mat_name)
        self.material_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum))
        self.material_row.addWidget(self.mat_label)
        self.material_row.addWidget(self.mat_combo)
        v_layout.addLayout(self.material_row)
        v_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        v_layout.addWidget(self.textures_label)
        self.row_dict = {}
        for each in textures:
            self.label = QtWidgets.QLabel('%s' % each)
            combo = AdvComboBox()
            # combo.currentIndexChanged.connect(self.on_parameter_changed)
            if len(shaders) == 1:
                combo.addItems(shaders)
            # find a match in shaders for to_match
            item_row = QtWidgets.QHBoxLayout()
            item_row.addWidget(self.label)
            item_row.addWidget(combo)
            self.row_dict.update({self.label: combo})
            v_layout.addLayout(item_row)
        v_layout.addLayout(self.button_row)
        self.setLayout(v_layout)
        self.setWindowTitle("Assign Textures to Shader Attr")
        self.mat_combo.currentIndexChanged.connect(self.on_shader_changed)
        self.mat_combo.setCurrentIndex(default_shader)
        self.create_shader.clicked.connect(self.on_create_shader)
        if default_shader:
            self.on_shader_changed()
        else:
            self.hide_textures()

    def hide_textures(self, show=False):
        if show:
            self.textures_label.show()
            self.create_shader.show()
        else:
            self.textures_label.hide()
            self.create_shader.hide()
        for key in self.row_dict:
            if show:
                key.show()
                self.row_dict[key].show()
            else:
                key.hide()
                self.row_dict[key].hide()

    def on_shader_changed(self):

        shader_name = self.mat_combo.currentText()
        params = self.shader_dict[shader_name]['parameters']
        for key in self.row_dict:
            item_num = 'Null'
            to_match = key.text().split("_")[-1].split('.')[0]
            self.row_dict[key].clear()
            i = -1
            for p in params:
                i += 1
                try:
                    if str(to_match) in params[p]['name_match']:
                        item_num = i
                except KeyError:
                    pass
                self.row_dict[key].addItem(p)
            if item_num != 'Null':
                self.row_dict[key].setCurrentIndex(item_num)
            else:
                self.row_dict[key].insertItem(0, '')
                self.row_dict[key].setCurrentIndex(0)
        self.hide_textures(show=True)

    def on_parameter_changed(self):
        text = self.sender().currentText()
        for key in self.row_dict:
            if self.row_dict[key] == self.sender():
                print key.text().split(':  ')[-1], text

    def on_create_shader(self):
        from tools.maya.util import connect_texture, apply_shader_attrs
        import pymel.core as pm
        source_shader = self.mat_combo.currentText()
        shader_name = '%s_shd' % self.material.name().split(':')[-1].split('_mtl')[0]
        if pm.objExists(shader_name):
            shader = shader_name
        else:
            shader = pm.shadingNode(str(source_shader), asShader=True, name=shader_name)
        default_attrs = app_config()['shaders'][self.mat_combo.currentText()]['default_shader_attrs']
        if default_attrs:
            apply_shader_attrs(shader, shader_attrs=default_attrs)
        for key in self.row_dict:
            file_name = key
            attr = self.row_dict[key]
            if attr.currentText() != '':
                full_path = os.path.join(self.tex_root, file_name.text())
                channel_ = app_config()['shaders'][self.mat_combo.currentText()]['parameters'][attr.currentText()]

                attr_ = channel_['attr']
                try:
                    normal = channel_['normal']
                except KeyError:
                    normal = False
                try:
                    channel = channel_['channel']
                except KeyError:
                    channel = None
                try:
                    shader_attrs = channel_['shader_attrs']
                except KeyError:
                    shader_attrs = None
                try:
                    color_space = channel_['colorspace']
                except KeyError:
                    color_space = None

                connect_texture(shader, shader_name, full_path, attr_, geo=self.material, channel=channel,
                                normal=normal, color_space=color_space, shader_attrs=shader_attrs)

        self.accept()


class LoginDialog(LJDialog):

    def __init__(self, parent=None):
        LJDialog.__init__(self, parent)
        self.user_name = ''
        self.user_email = ''
        self.company = ''
        self.user_config = user_config()
        self.parent = parent
        uname_layout = QtWidgets.QHBoxLayout()
        email_layout = QtWidgets.QHBoxLayout()
        company_layout = QtWidgets.QHBoxLayout()
        self.uname_label = QtWidgets.QLabel('User Name:')
        self.email_label = QtWidgets.QLabel('Email:')
        self.company_label = QtWidgets.QLabel('Company:')
        self.uname_line_edit = QtWidgets.QLineEdit()
        self.email_line_edit = QtWidgets.QLineEdit()
        self.company_line_edit = QtWidgets.QLineEdit()
        self.uname_line_edit.setMinimumWidth(160)
        self.uname_line_edit.setMaximumWidth(160)
        self.email_line_edit.setMaximumWidth(160)
        self.email_line_edit.setMinimumWidth(160)
        self.company_line_edit.setMaximumWidth(160)
        self.company_line_edit.setMinimumWidth(160)
        uname_layout.addWidget(self.uname_label)
        uname_layout.addWidget(self.uname_line_edit)
        email_layout.addWidget(self.email_label)
        email_layout.addWidget(self.email_line_edit)
        company_layout.addWidget(self.company_label)
        company_layout.addWidget(self.company_line_edit)
        buttons_layout = QtWidgets.QHBoxLayout()
        self.ok_button = QtWidgets.QPushButton('Ok')
        self.cancel_button = QtWidgets.QPushButton('Cancel')
        buttons_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                     QtWidgets.QSizePolicy.Minimum))
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.ok_button)
        self.ok_button.setEnabled(False)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(uname_layout)
        layout.addLayout(email_layout)
        layout.addLayout(company_layout)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        self.setWindowTitle('Login')
        self.load_user_defaults()

        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.email_line_edit.textChanged.connect(self.on_text_changed)
        self.uname_line_edit.textChanged.connect(self.on_text_changed)
        self.company_line_edit.textChanged.connect(self.on_text_changed)

    def on_text_changed(self):
        uname = self.uname_line_edit.text()
        email = self.email_line_edit.text()
        company = self.company_line_edit.text()
        if uname and email and company:
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)

    def on_ok_clicked(self):
        self.save_user_defaults()
        self.accept()

    def on_cancel_clicked(self):
        self.accept()
        print 'Cancel Clicked'

    def load_user_defaults(self):
        if os.path.exists(self.user_config):
            with open(self.user_config, 'r') as stream:
                try:
                    result = yaml.load(stream)
                    self.uname_line_edit.setText(result['user_name'])
                    self.email_line_edit.setText(result['user_email'])
                    self.company_line_edit.setText(result['company'])
                    self.user_email = result['user_email']
                    self.user_name = result['user_name']
                    self.company = result['company']
                except yaml.YAMLError as exc:
                    print(exc)
                    sys.exit(99)
        else:
            pass

    def save_user_defaults(self):
        print 'Saving user config: %s' % self.user_config
        self.user_name = self.uname_line_edit.text()
        self.user_email = self.email_line_edit.text()
        self.company = self.company_line_edit.text()
        d = {'user_name': self.user_name,
             'user_email': self.user_email,
             'company': self.company
             }
        with open(self.user_config, 'w') as outfile:
            yaml.dump(d, outfile, default_flow_style=False)



