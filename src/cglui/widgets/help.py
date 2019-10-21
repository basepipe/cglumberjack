from Qt import QtCore
from Qt import QtWidgets
from Qt import QtGui
import os
from cglcore import lj_mail
from cglcore.config import app_config
from cglui.widgets.base import LJDialog
from cglcore.util import current_user
from cglcore import screen_grab
from cglui.widgets.widgets import AdvComboBox
from plugins.project_management.asana.basic import AsanaJack

PROJECT_MANAGEMENT = app_config()['account_info']['project_management']


class RequestFeatureDialog(LJDialog):
    def __init__(self, parent=None, title='Request Feature'):
        LJDialog.__init__(self, parent)
        self.rtf_task_text = ''
        self.requirements_list = []
        self.results_list = []
        software_list = sorted(['Smedge', 'Deadline', 'Maya', 'Nuke', 'Unreal Engine', 'Unity', 'Adobe Premiere',
                                'Lumbermill', 'Github', 'Slack', 'S3', 'EC2', 'Asana'])
        software_list.insert(0, '')
        language_list = sorted(['Python2.7', 'C++', 'C#', '.bat', 'wordpress', 'CMD', 'Bash script'])
        language_list.insert(0, '')
        deliverable_list = sorted(['CMD shell command', 'Batch script', '.bat script', 'Function (new)',
                                   'Function (existing)', 'Gui', 'Class', 'File (new)', 'File (existing)', 'Tutorial'])
        deliverable_list.insert(0, '')
        delivery_method_list = ['Github Pull Request', 'Send to Slack Channel']
        reference_dict = {'smedge': {'documentation': {'user manual': 'https://www.uberware.net/User_Manual.pdf',
                                                       'admin manual': 'https://www.uberware.net/Administrator_Manual.pdf',
                                                       'command line reference': 'http://dev.uberware.net/smedge2/manual/cli.shtml'},
                                     'videos': {},
                                     'CGL Examples': {}
                                     },
                          'deadline': {'documentation': {},
                                     'videos': {},
                                     'CGL Examples': {}
                                     },
                          'maya': {'documentation': {'pymel documentation': 'https://help.autodesk.com/cloudhelp/2018/JPN/Maya-Tech-Docs/PyMel/index.html',
                                                     'mel documentation': '',
                                                     'maya python documentation': ""},
                                     'videos': {},
                                     'CGL Examples': {}
                                     },
                          'nuke': {'documentation': {'command line reference': 'https://learn.foundry.com/nuke/developers/100/pythondevguide/command_line.html',
                                                     'developers guide': 'https://learn.foundry.com/nuke/developers/100/pythondevguide/index.html'},
                                     'videos': {},
                                     'CGL Examples': {}
                                     },
                          'unreal engine': {'documentation': {},
                                            'videos': {},
                                            'CGL Examples': {}
                                            },
                          'unity': {'documentation': {},
                                    'videos': {},
                                    'CGL Examples': {}
                                    },
                          'adobe premiere': {'documentation': {},
                                             'videos': {},
                                             'CGL Examples': {}
                                             },
                          'final cut pro': {'documentation': {},
                                            'videos': {},
                                            'CGL Examples': {}
                                            },
                          'lumbermill': {'documentation': {},
                                         'videos': {},
                                         'CGL Examples': {}
                                         },
                          'github': {'documentation': {},
                                     'videos': {},
                                     'CGL Examples': {}
                                    },
                          'slack': {'documentation': {},
                                    'videos': {},
                                    'CGL Examples': {}
                                     },
                          's3': {'documentation': {},
                                 'videos': {},
                                 'CGL Examples': {}
                                },
                          'ec2': {'documentation': {},
                                  'videos': {},
                                  'CGL Examples': {}
                                  },
                          'python2.7': {'documentation': {},
                                        'videos': {},
                                        'CGL Examples': {}
                                        },
                          'c++': {'documentation': {},
                                  'videos': {},
                                  'CGL Examples': {}
                                  },
                          'c#': {'documentation': {},
                                 'videos': {},
                                 'CGL Examples': {}
                                 },
                          '.bat': {'documentation': {},
                                   'videos': {},
                                   'CGL Examples': {}
                                    },
                          'wordpress': {'documentation': {},
                                        'videos': {},
                                        'CGL Examples': {}
                                        },
                          'cmd': {'documentation': {},
                                  'videos': {},
                                  'CGL Examples': {}
                                   },
                          'bash script': {'documentation': {},
                                          'videos': {},
                                          'CGL Examples': {}
                                          },
                          'pyside': {'documentation': {},
                                     'videos': {},
                                     'CGL Examples': {}
                                     },
                          'pyqt': {'documentation': {},
                                    'videos': {},
                                    'CGL Examples': {}
                                    },
                          'asana': {'documentation': {'Quick Start Guide': 'https://asana.com/developers/documentation/getting-started/quick-start',
                                                      'Task Creation Example': 'https://github.com/Asana/python-asana/blob/master/examples/example-create-task.py'
                                                      },
                                    'videos': {},
                                    'CGL Examples': {}
                                    },
                          }
        layout = QtWidgets.QVBoxLayout()
        grid = QtWidgets.QGridLayout()
        grid2 = QtWidgets.QGridLayout()
        self.setMinimumWidth(800)

        # all the labels
        label_details = QtWidgets.QLabel('Details:')
        label_details.setProperty('class', 'ultra_title')
        label_task_info = QtWidgets.QLabel('Task Info:')
        label_task_info.setProperty('class', 'ultra_title')
        label_description = QtWidgets.QLabel('Description:')
        label_software = QtWidgets.QLabel('Product:')
        label_language = QtWidgets.QLabel("Language:")
        label_deliverable = QtWidgets.QLabel('Deliverable:')
        self.label_code_location = QtWidgets.QLabel('Code Location:')
        label_delivery_method = QtWidgets.QLabel('Delivery Method:')
        label_requirements = QtWidgets.QLabel('Requirements:')
        label_expected_results = QtWidgets.QLabel('Expected Results:')
        label_resources = QtWidgets.QLabel('Resources:')
        label_resources.setProperty('class', 'ultra_title')
        label_documentation = QtWidgets.QLabel('Documentation:')
        label_videos = QtWidgets.QLabel('Videos:')
        label_cgl_examples = QtWidgets.QLabel('CGL Examples & Tutorials:')
        label_attachments = QtWidgets.QLabel('Attachments:')
        label_task_text = QtWidgets.QLabel('Task Preview Text:')
        label_task_text.setProperty('class', 'ultra_title')
        label_task_title = QtWidgets.QLabel("Title")
        self.message_requirements = QtWidgets.QLabel()
        self.message_expected_results = QtWidgets.QLabel()
        self.message_requirements.hide()
        self.message_expected_results.hide()


        # all the combo boxes:
        self.combo_software = AdvComboBox()
        self.combo_software.addItems(software_list)
        self.combo_language = AdvComboBox()
        self.combo_language.addItems(language_list)
        self.combo_deliverable_list = AdvComboBox()
        self.combo_deliverable_list.addItems(deliverable_list)
        self.combo_delivery_method = AdvComboBox()
        self.combo_delivery_method.addItems(delivery_method_list)
        self.text_edit = QtWidgets.QTextEdit()

        self.submit_task_button = QtWidgets.QPushButton('Submit Task')
        self.submit_task_button.setDefault(False)
        self.submit_task_button.setAutoDefault(False)
        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self.submit_task_button)

        # grid.addWidget(label_description, 0, 0)

        self.title_line_edit = QtWidgets.QLineEdit()
        self.description_line_edit = QtWidgets.QLineEdit()
        self.description_line_edit.setPlaceholderText('Description: Less than 140 characters')
        self.location_line_edit = QtWidgets.QLineEdit()
        self.requirements_line_edit = QtWidgets.QLineEdit()
        self.requirements_line_edit.setPlaceholderText('type requirement and hit enter')
        self.expected_results_line_edit = QtWidgets.QLineEdit()
        self.expected_results_line_edit.setPlaceholderText('type expected result and hit enter')
        self.documentation_line_edit = QtWidgets.QLineEdit()
        self.videos_line_edit = QtWidgets.QLineEdit()
        self.cgl_line_edit = QtWidgets.QLineEdit()
        
        self.widget_dict = {self.requirements_line_edit: self.message_requirements,
                            self.expected_results_line_edit: self.message_expected_results,
                            }
        self.bullet_dict = {self.requirements_line_edit: self.requirements_list,
                            self.expected_results_line_edit: self.results_list,
                            }

        grid.addWidget(label_software, 1, 0)
        grid.addWidget(self.combo_software, 1, 1)
        grid.addWidget(label_language, 1, 2)
        grid.addWidget(self.combo_language, 1, 3)
        grid.addWidget(label_deliverable, 3, 0)
        grid.addWidget(self.combo_deliverable_list, 3, 1)
        grid.addWidget(label_delivery_method, 3, 2)
        grid.addWidget(self.combo_delivery_method, 3, 3)
        grid.addWidget(self.label_code_location, 4, 0)
        grid.addWidget(self.location_line_edit, 4, 1)

        grid2.addWidget(label_task_title, 0, 0)
        grid2.addWidget(self.title_line_edit, 0, 1)
        grid2.addWidget(label_description, 0, 2)
        grid2.addWidget(self.description_line_edit, 0, 3)
        grid2.addWidget(label_requirements, 1, 0)
        grid2.addWidget(self.requirements_line_edit, 1, 1)
        grid2.addWidget(self.message_requirements, 2, 1)
        grid2.addWidget(label_expected_results, 1, 2)
        grid2.addWidget(self.expected_results_line_edit, 1, 3)
        grid2.addWidget(self.message_expected_results, 2, 3)

        #layout.addLayout(task_layout)
        layout.addWidget(label_details)
        layout.addLayout(grid)
        layout.addWidget(label_task_info)
        layout.addLayout(grid2)
        # layout.addWidget(label_resources)
        # layout.addWidget(label_documentation)
        # layout.addWidget(self.documentation_line_edit)
        # layout.addWidget(label_videos)
        # layout.addWidget(self.videos_line_edit)
        # layout.addWidget(label_cgl_examples)
        # layout.addWidget(self.cgl_line_edit)
        # layout.addWidget(label_attachments)
        layout.addWidget(label_task_text)
        layout.addWidget(self.text_edit)
        layout.addLayout(button_row)

        self.setLayout(layout)
        self.setWindowTitle(title)

        self.combo_deliverable_list.currentIndexChanged.connect(self.show_code_location)
        self.requirements_line_edit.returnPressed.connect(self.add_bullets)
        self.expected_results_line_edit.returnPressed.connect(self.add_bullets)
        self.combo_software.currentIndexChanged.connect(self.update_text_edit)
        self.combo_language.currentIndexChanged.connect(self.update_text_edit)
        self.combo_deliverable_list.currentIndexChanged.connect(self.update_text_edit)
        self.combo_delivery_method.currentIndexChanged.connect(self.update_text_edit)
        self.description_line_edit.textChanged.connect(self.update_text_edit)
        self.location_line_edit.textChanged.connect(self.update_text_edit)
        self.submit_task_button.clicked.connect(self.on_submit_clicked)
        self.show_code_location()
        self.update_text_edit()
        # self.submit_task_button.setEnabled(False)

    def on_submit_clicked(self):
        AsanaJack().create_task(project_name='Test Project A', section_name='Backlog',
                                task_name=self.title_line_edit.text(), notes=self.rtf_task_text)
        self.accept()

    def update_text_edit(self):
        """
        """
        # self.safe_to_submit()
        rtf_software = self.rtf_label('Software', self.combo_software.currentText())
        rtf_language = self.rtf_label('Language', self.combo_language.currentText())
        rtf_deliverable = self.rtf_label("Deliverable", self.combo_deliverable_list.currentText())
        rtf_delivery_method = self.rtf_label("Delivery Method", self.combo_delivery_method.currentText())
        info_line = "%s, %s\n\n" % (rtf_software, rtf_language)
        rtf_task_description = "<strong>Task Description:</strong>\n\t%s\n\n" % self.description_line_edit.text()
        rtf_code_location = "<strong>Code Location:</strong>\n\t<code>%s</code>\n\n" % self.location_line_edit.text()
        rtf_requirements = self.rtf_bullet_list('Requirements:', self.requirements_list)
        rtf_expected_results = self.rtf_bullet_list('Expected Results:', self.results_list)
        rtf_deliverables = self.rtf_bullet_list("What You'll Deliver:", [rtf_deliverable, rtf_delivery_method])
        self.rtf_task_text = "<body>%s%s%s%s%s%s</body>" % (info_line, rtf_task_description, rtf_code_location,
                                                            rtf_requirements, rtf_expected_results, rtf_deliverables)
        self.text_edit.setAcceptRichText(True)
        self.text_edit.setText(self.rtf_task_text)

    @staticmethod
    def rtf_label(bold_text, regular_text):
        if regular_text:
            return "<strong>%s: </strong>%s" % (bold_text, regular_text)
        else:
            return "<strong>%s: </strong>%s" % (bold_text, 'Not Defined')

    @staticmethod
    def rtf_bullet_list(bold_label, bullet_list):
        if bullet_list:
            rtf_ul = "<strong>%s</strong>\n<ul>" % bold_label
            for each in bullet_list:
                rtf_ul += "<li>%s</li>" % each
            rtf_ul += "</ul>\n"
            return rtf_ul
        else:
            return "<strong>%s</strong>\n\n" % bold_label

    def show_code_location(self):
        deliverable_list = ['new function', 'updated function',
                            'gui', 'class', 'new file', 'updated file', 'tutorial']
        if self.combo_deliverable_list.currentText() in deliverable_list:
            self.label_code_location.show()
            self.location_line_edit.show()
        else:
            self.label_code_location.hide()
            self.location_line_edit.hide()

    def check_description_length(self):
        pass
    
    def add_bullets(self, line_edit=None):
        if not line_edit:
            line_edit = self.sender()
        current_text = line_edit.text()
        requirements_text = self.widget_dict[line_edit].text()
        list_ = self.bullet_dict[line_edit]
        list_.append(current_text)
        self.update_text_edit()
        if not requirements_text:
            requirements_text = '    *%s' % current_text
        else:
            requirements_text = '%s\n    *%s' % (requirements_text, current_text)
        self.widget_dict[line_edit].setText(requirements_text)
        line_edit.setText('')
        self.widget_dict[line_edit].show()

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

        self.self.text_edit = QtWidgets.QTextEdit()
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
        layout.addWidget(self.self.text_edit)
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
        self.self.text_edit.textChanged.connect(self.ok_to_send)
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
        return self.self.text_edit.toPlainText()

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

