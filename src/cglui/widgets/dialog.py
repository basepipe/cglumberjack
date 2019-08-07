from Qt import QtCore, QtWidgets
import os
import re
import datetime
from cglcore.config import app_config, user_config
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
        self.original_message = message
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
            button_box.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                     QtWidgets.QSizePolicy.Minimum))

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
            self.combo_box.textChanged.connect(self.on_text_changed_regex)

    def on_button_clicked(self):
        self.button = self.sender().text()
        self.input_text = self.line_edit.text()

    def on_text_changed_regex(self):
        message = ''
        if self.sender() == self.line_edit:
            if self.line_edit.text():
                if re.match(self.regex, self.line_edit.text()):
                    message = '%s\n%s Passes!' % (self.original_message, self.line_edit.text())
                    self.btn1.setEnabled(True)
                    self.btn2.setEnabled(True)
                    self.btn3.setEnabled(True)
                else:
                    bad_name = '%s\n%s does not pass' % (self.original_message, self.line_edit.text())
                    message = '%s\n%s' % (bad_name, self.name_example)
                    self.btn1.setEnabled(False)
                    self.btn2.setEnabled(False)
                    self.btn3.setEnabled(False)
        if self.sender() == self.combo_box:
            if self.combo_box.currentText:
                if re.match(self.regex, self.combo_box.currentText()):
                    message = '%s\n%s Passes!' % (self.original_message, self.combo_box.currentText())
                    self.btn1.setEnabled(True)
                    self.btn2.setEnabled(True)
                    self.btn3.setEnabled(True)
                else:
                    bad_name = '%s\n%s does not pass' % (self.original_message, self.combo_box.currentText())
                    message = '%s\n%s' % (bad_name, self.name_example)
                    self.btn1.setEnabled(False)
                    self.btn2.setEnabled(False)
                    self.btn3.setEnabled(False)
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
        print('Adjust Load User Defaults to handle .json')
        if os.path.exists(self.user_config):
            print self.user_config

    @staticmethod
    def save_user_defaults():
        print('Adjust user defaults to save .json')


