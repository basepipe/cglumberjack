from Qt import QtCore
from Qt import QtWidgets
from Qt import QtGui
import os
from cglcore import lj_mail
from cglcore.config import app_config
from cglui.widgets.base import LJDialog
from cglcore.util import current_user
from cglcore import screen_grab

PROJECT_MANAGEMENT = app_config()['account_info']['project_management']


class ReportBugDialog(LJDialog):

    def __init__(self, parent=None, title='Report A Bug'):
        LJDialog.__init__(self, parent)
        self.title_ = parent.windowTitle()
        layout = QtWidgets.QVBoxLayout()
        grid_layout = QtWidgets.QGridLayout()
        self.attachments = []
        icon_path = os.path.join(app_config()['paths']['code_root'], 'resources', 'images')
        # define the user name area
        self.label_username = QtWidgets.QLabel('Username')
        self.lineEdit_username = QtWidgets.QLineEdit()
        self.lineEdit_username.setText(current_user())

        # define the email area
        self.label_email = QtWidgets.QLabel('Email')
        self.lineEdit_email = QtWidgets.QLineEdit()
        self.get_email()

        # define the software area
        self.label_messaging = QtWidgets.QLabel('*All fields must have valid values \nbefore submitting bug report')
        self.label_messaging.setStyleSheet('color: red')
        self.label_software = QtWidgets.QLabel('Software')
        self.label_description = QtWidgets.QLabel('Description of Issue:')
        self.lineEdit_software = QtWidgets.QLineEdit()
        self.label_subject = QtWidgets.QLabel('Subject')
        self.lineEdit_subject = QtWidgets.QLineEdit()

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
        button_bar.addWidget(self.button_add_screen_grab)
        button_bar.addWidget(self.button_attachment)
        button_bar.addWidget(self.label_description)

        grid_layout.addWidget(self.label_username, 0, 0)
        grid_layout.addWidget(self.lineEdit_username, 0, 1)
        grid_layout.addWidget(self.label_email, 1, 0)
        grid_layout.addWidget(self.lineEdit_email, 1, 1)
        grid_layout.addWidget(self.label_software, 2, 0)
        grid_layout.addWidget(self.lineEdit_software, 2, 1)
        grid_layout.addWidget(self.label_subject, 3, 0)
        grid_layout.addWidget(self.lineEdit_subject, 3, 1)
        layout.addLayout(grid_layout)
        layout.addLayout(button_bar)
        layout.addWidget(self.label_description)
        layout.addWidget(self.text_edit)
        layout.addLayout(self.screengrabs_layout)
        layout.addWidget(self.label_messaging)
        layout.addWidget(self.button_submit)

        self.setLayout(layout)
        self.setWindowTitle(title)

        self.button_submit.setEnabled(False)

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
        email = app_config()['project_management'][PROJECT_MANAGEMENT]['users'][self.lineEdit_username.text()]['email']
        self.lineEdit_email.setText(email)
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
        lj_mail.slack_notification_email(type_='bugs', subject="[bugs] %s" % self.get_subject(), message=message,
                                         attachments=self.attachments)
        for each in self.attachments:
            if 'screen_grab' in each:
                os.remove(each)
        self.close()
        print 'Email Sent!'

    def screen_grab(self):
        output_path = screen_grab.run()
        print 'Created Screen Grab: %s' % output_path
        self.add_attachments(file_paths=[output_path])
        # filename = os.path.split(output_path)[-1]
        # self.attachments.append(filename)
        # label = QtWidgets.QLabel("<html><img src=%s> %s </html>" % (self.paperclip_icon, filename))
        # self.screengrabs_layout.addWidget(label)
        return output_path

