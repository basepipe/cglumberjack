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
        self.work_group = 'CGLumberjack'
        self.rtf_task_text = ''
        self.requirements_list = []
        self.results_list = []
        self.links_list = []
        # This list should be connected to
        self.repo_dict = {'cglumberjack': {'guis': {'Lumbermill': ['src/apps/lumbermill/main.py'],
                                                    'Pipeline Designer': ['src/apps/pipeline/designer.py'],
                                                    'Request Feature': ['src/cglui/widgets/help.py',
                                                                        'RequestFeatureDialog()'],
                                                    'Time Tracker': ['src/cglui/widgets/dialog.py', 'TimeTracker()'],
                                                    'Report Bug': ['src/cglui/widgets/help.py', 'ReportBugDialog()']
                                                    },
                                           'language': 'Python 2.7'
                                           },
                          'core_tools': {'guis': {'None': ['']},
                                         'language': ''},
                          'onboarding': {'guis': {'None': ['']},
                                         'language': ''},
                          'None': {'guis': {'None': ['']},
                                   'language': ''}
                          }
        workspace_data = AsanaJack().find_workspaces()
        workspace_names = []
        ignore = ['Personal Projects']
        for w in workspace_data:
            if w['name'] not in ignore:
                workspace_names.append(w['name'])

        workgroup_list = sorted(workspace_names)
        workgroup_list.insert(0, '')
        software_list = sorted(['Smedge', 'Deadline', 'Maya', 'Nuke', 'Unreal Engine', 'Unity', 'Adobe Premiere',
                                'Lumbermill', 'Github', 'Slack', 'S3', 'EC2', 'Asana'])
        software_list.insert(0, '')
        language_list = sorted(['', 'Python 2.7', 'C++', 'C#', '.bat', 'wordpress', 'CMD', 'Bash script'])
        language_list.insert(0, '')
        deliverable_list = sorted(['CMD shell command', 'Batch script', '.bat script', 'Function (new)',
                                   'Function (existing)', 'Gui', 'Class', 'File (new)', 'File (existing)', 'Tutorial'])
        deliverable_list.insert(0, '')
        delivery_method_list = ['Github Pull Request', 'Send to Slack Channel']
        self.reference_dict = {'smedge': {'documentation': {'user manual': 'https://www.uberware.net/User_Manual.pdf',
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
                          'python 2.7': {'documentation': {},
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
        right_layout = QtWidgets.QVBoxLayout()
        left_layout = QtWidgets.QVBoxLayout()
        h_layout = QtWidgets.QHBoxLayout()
        grid = QtWidgets.QGridLayout()
        self.setMinimumWidth(400)

        # all the labels
        self.label_details = QtWidgets.QLabel('Details:')
        self.label_details.setProperty('class', 'ultra_title')
        self.label_code_info = QtWidgets.QLabel('Code Info:')
        self.label_code_info.setProperty('class', 'ultra_title')
        self.label_task_info = QtWidgets.QLabel('Task Info:')
        self.label_task_info.setProperty('class', 'ultra_title')
        label_description = QtWidgets.QLabel('Description:')
        self.label_software = QtWidgets.QLabel('External Product(s):')
        self.label_language = QtWidgets.QLabel("Language:")
        self.label_deliverable = QtWidgets.QLabel('Deliverable:')
        self.label_code_location = QtWidgets.QLabel('Code Location:')
        self.label_delivery_method = QtWidgets.QLabel('Delivery Method:')
        self.label_requirements = QtWidgets.QLabel('Other Requirements:')
        self.label_expected_results = QtWidgets.QLabel('Expected Results:')
        self.label_expected_results.setProperty('class', 'ultra_title')
        self.label_resources = QtWidgets.QLabel('Resources:')
        self.label_resources.setProperty('class', 'ultra_title')
        self.label_repo = QtWidgets.QLabel('Repo:')
        self.label_gui = QtWidgets.QLabel('GUI:')
        self.label_files = QtWidgets.QLabel('File(s):')
        self.label_attachments = QtWidgets.QLabel('Attachments:')
        self.label_task_text = QtWidgets.QLabel('Task Text:')
        self.label_task_text.setProperty('class', 'ultra_title')
        self.label_task_title = QtWidgets.QLabel("Title")
        self.label_functions = QtWidgets.QLabel("Function(s)")
        self.label_workgroup = QtWidgets.QLabel("Workgroup:")
        self.workgroup = QtWidgets.QHBoxLayout()
        self.message_files = QtWidgets.QLabel()
        self.message_functions = QtWidgets.QLabel()
        self.message_requirements = QtWidgets.QLabel()
        self.message_expected_results = QtWidgets.QLabel()
        self.message_software = QtWidgets.QLabel()

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
        self.combo_files = AdvComboBox()
        self.combo_repo = AdvComboBox()
        self.combo_repo.addItems(self.repo_dict.keys())
        ind = self.combo_repo.findText('cglumberjack')
        self.combo_repo.setCurrentIndex(ind)
        self.combo_gui = AdvComboBox()
        self.combo_workgroup_list = AdvComboBox()
        self.combo_workgroup_list.addItems(workgroup_list)
        ind2 = self.combo_workgroup_list.findText(self.work_group)
        self.combo_workgroup_list.setCurrentIndex(ind2)

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
        self.line_edit_functions = QtWidgets.QLineEdit()
        self.widget_dict = {self.requirements_line_edit: self.message_requirements,
                            self.expected_results_line_edit: self.message_expected_results,
                            self.combo_gui: self.message_files
                            }
        self.bullet_dict = {self.requirements_line_edit: self.requirements_list,
                            self.expected_results_line_edit: self.results_list,
                            }

        grid.addWidget(self.label_workgroup, 0, 0)
        grid.addWidget(self.combo_workgroup_list, 0, 1)

        grid.addWidget(self.label_task_title, 1, 0)
        grid.addWidget(self.title_line_edit, 1, 1)
        grid.addWidget(label_description, 2, 0)
        grid.addWidget(self.description_line_edit, 2, 1)
        grid.addWidget(self.label_code_info, 4, 0)

        grid.addWidget(self.label_repo, 10, 0)
        grid.addWidget(self.combo_repo, 10, 1)
        grid.addWidget(self.label_language, 11, 0)
        grid.addWidget(self.combo_language, 11, 1)
        grid.addWidget(self.label_gui, 12, 0)
        grid.addWidget(self.combo_gui, 12, 1)

        grid.addWidget(self.label_files, 13, 0)
        grid.addWidget(self.combo_files, 13, 1)
        grid.addWidget(self.message_files, 14, 1)

        grid.addWidget(self.label_functions, 15, 0)
        grid.addWidget(self.line_edit_functions, 15, 1)
        grid.addWidget(self.message_functions, 16, 1)
        grid.addWidget(self.label_delivery_method, 17, 0)
        grid.addWidget(self.combo_delivery_method, 17, 1)
        grid.addWidget(self.label_deliverable, 18, 0)
        grid.addWidget(self.combo_deliverable_list, 18, 1)

        grid.addWidget(self.label_details, 20, 0)
        grid.addWidget(self.label_software, 21, 0)
        grid.addWidget(self.combo_software, 21, 1)
        grid.addWidget(self.message_software, 22, 1)
        grid.addWidget(self.label_requirements, 23, 0)
        grid.addWidget(self.requirements_line_edit, 23, 1)
        grid.addWidget(self.message_requirements, 24, 1)

        grid.addWidget(self.label_expected_results, 26, 0)
        grid.addWidget(self.expected_results_line_edit,  27, 1)
        grid.addWidget(self.message_expected_results, 28, 1)
        # grid.addWidget(self.label_code_location, 28, 0)
        # grid.addWidget(self.location_line_edit, 28, 1)

        #layout.addLayout(task_layout)
        right_layout.addWidget(self.label_task_info)
        right_layout.addLayout(grid)
        right_layout.addStretch(1)
        left_layout.addWidget(self.label_task_text)
        left_layout.addWidget(self.text_edit)
        h_layout.addLayout(right_layout)
        h_layout.addLayout(left_layout)
        layout.addLayout(h_layout)
        layout.addLayout(button_row)


        self.setLayout(layout)
        self.setWindowTitle(title)

        self.combo_deliverable_list.currentIndexChanged.connect(self.show_code_location)
        self.combo_gui.currentIndexChanged.connect(self.on_gui_chosen)
        self.requirements_line_edit.returnPressed.connect(self.add_bullets)
        self.requirements_line_edit.textChanged.connect(self.update_text_edit)
        self.expected_results_line_edit.returnPressed.connect(self.add_bullets)
        self.expected_results_line_edit.textChanged.connect(self.update_text_edit)
        self.combo_workgroup_list.currentIndexChanged.connect(self.on_workgroup_changed)
        self.combo_software.currentIndexChanged.connect(self.update_text_edit)
        self.combo_software.currentIndexChanged.connect(self.show_stuff)
        self.combo_software.currentIndexChanged.connect(self.on_software_chosen)
        self.combo_language.currentIndexChanged.connect(self.update_text_edit)
        self.combo_deliverable_list.currentIndexChanged.connect(self.update_text_edit)
        self.combo_delivery_method.currentIndexChanged.connect(self.update_text_edit)
        self.description_line_edit.textChanged.connect(self.update_text_edit)
        self.description_line_edit.returnPressed.connect(self.show_stuff)
        self.location_line_edit.textChanged.connect(self.update_text_edit)
        self.submit_task_button.clicked.connect(self.on_submit_clicked)
        self.combo_repo.currentIndexChanged.connect(self.on_repo_chosen)
        self.on_repo_chosen()
        self.show_code_location()
        self.update_text_edit()
        # self.submit_task_button.setEnabled(False)
        self.hide_all()

        # TODO: add bullets underneath External Products
        # pull in files and functions to the "requirements"
        # pull in Repo to the requirements
        # pull in external products to the requirements
        # placeholder text on filescombo
        # placeholder text on functionscombo
        # add links to the task text

    def on_workgroup_changed(self):
        self.work_group = self.combo_workgroup_list.currentText()

    def choose_deliverable(self):
        if self.message_functions or self.message_files:
            index = self.combo_deliverable_list.findText('File (existing)')
            self.combo_deliverable_list.setCurrentIndex(index)

    def show_stuff(self):
        if self.sender() == self.description_line_edit:
            self.label_code_info.show()
            self.label_language.show()
            self.label_repo.show()
            self.label_gui.show()
            self.combo_repo.show()
            self.combo_gui.show()
            self.combo_language.show()
            # change focus to the combo_gui.
            self.combo_gui.setFocus()
        elif self.sender() == self.combo_gui:
            self.label_files.show()
            self.combo_files.show()
            self.message_files.show()
            self.label_functions.show()
            self.line_edit_functions.show()
            self.message_functions.show()
            self.label_details.show()
            self.label_software.show()
            self.combo_software.show()
            self.label_delivery_method.show()
            self.combo_delivery_method.show()
            self.label_deliverable.show()
            self.combo_deliverable_list.show()
            self.choose_deliverable()
            self.combo_software.setFocus()
        elif self.sender() == self.combo_software:
            self.label_requirements.show()
            self.requirements_line_edit.show()
            #self.label_code_location.show()
            #self.location_line_edit.show()
            self.label_task_info.show()
            self.label_task_text.show()
            self.label_expected_results.show()
            self.expected_results_line_edit.show()
            self.text_edit.show()
            self.setMinimumWidth(1200)
            self.expected_results_line_edit.setFocus()
            self.submit_task_button.setEnabled(True)
        else:
            pass
            # self.label_resources.show()
            # self.label_attachments.show()
            # self.message_expected_results.show()
            # self.text_edit.show()
            # self.documentation_line_edit.show()
            # self.videos_line_edit.show()
            # self.cgl_line_edit.show()

    def hide_all(self):
        self.message_software.hide()
        self.label_details.hide()
        self.label_details.hide()
        self.label_code_info.hide()
        self.label_code_info.hide()
        self.label_task_info.hide()
        self.label_software.hide()
        self.label_language.hide()
        self.label_deliverable.hide()
        self.label_code_location.hide()
        self.label_delivery_method.hide()
        self.label_requirements.hide()
        self.label_resources.hide()
        self.label_repo.hide()
        self.label_gui.hide()
        self.label_files.hide()
        self.label_attachments.hide()
        self.label_task_text.hide()
        self.label_functions.hide()
        self.label_expected_results.hide()
        self.expected_results_line_edit.hide()

        self.location_line_edit.hide()
        self.requirements_line_edit.hide()
        self.documentation_line_edit.hide()
        self.videos_line_edit.hide()
        self.cgl_line_edit.hide()
        self.line_edit_functions.hide()
        self.message_files.hide()
        self.message_functions.hide()
        self.message_requirements.hide()
        self.message_expected_results.hide()
        self.message_requirements.hide()
        self.message_expected_results.hide()
        self.message_files.hide()
        self.message_functions.hide()

        # all the combo boxes:
        self.combo_software.hide()
        self.combo_language .hide()
        self.combo_deliverable_list.hide()
        self.combo_delivery_method.hide()
        self.text_edit.hide()
        self.combo_files.hide()
        self.combo_repo.hide()
        self.combo_gui.hide()

        self.submit_task_button.setEnabled(False)

    def on_repo_chosen(self):
        repo = self.combo_repo.currentText()
        self.combo_gui.clear()
        self.combo_gui.insertItem(0, '')
        self.combo_gui.addItems(self.repo_dict[repo]['guis'].keys())
        language = self.repo_dict[repo]['language']
        index = self.combo_language.findText(language)
        self.combo_language.setCurrentIndex(index)

    def on_submit_clicked(self):
        # workgroup_chosen = self.combo_workgroup_list().currentText()
        AsanaJack(work_space=self.work_group).create_project('General Development')
        AsanaJack(work_space=self.work_group).create_task(project_name='General Development', section_name='Backlog',
                                                          task_name=self.title_line_edit.text(), notes=self.rtf_task_text)
        self.accept()

    def update_text_edit(self):
        """
        """
        rtf_repo = self.rtf_label('Repo', self.combo_repo.currentText())
        rtf_language = self.rtf_label('Language', self.combo_language.currentText())
        rtf_deliverable = self.rtf_label("Deliverable", self.combo_deliverable_list.currentText())
        rtf_delivery_method = self.rtf_label("Delivery Method", self.combo_delivery_method.currentText())

        rtf_task_description = "<strong>Task Description:</strong>\n\t%s\n\n" % self.description_line_edit.text()
        self.requirements_list = [rtf_repo, rtf_language]
        self.requirements_list.extend(self.list_from_bullets(self.message_software))
        self.requirements_list.extend(self.list_from_bullets(self.message_files))
        self.requirements_list.extend(self.list_from_bullets(self.message_functions))
        self.requirements_list.extend(self.list_from_bullets(self.message_requirements))
        self.results_list = [rtf_deliverable, rtf_delivery_method]
        self.results_list.extend(self.list_from_bullets(self.message_expected_results))
        rtf_requirements = self.rtf_bullet_list('Requirements:', self.requirements_list)
        rtf_expected_results = self.rtf_bullet_list('Expected Results:', self.results_list)
        links = self.get_relevant_links()
        rtf_links = ''
        if links:
            rtf_links = self.rtf_bullet_list('Resources:', links)
        self.rtf_task_text = "<body>%s%s%s%s</body>" % (rtf_task_description, rtf_requirements, rtf_expected_results,
                                                        rtf_links)
        self.text_edit.setAcceptRichText(True)
        self.text_edit.setText(self.rtf_task_text)

    def get_relevant_links(self):
        links = []
        for s in self.list_from_bullets(self.message_software):
            print s.lower()
            if s.lower() in self.reference_dict.keys():
                for link_type in self.reference_dict[s.lower()]:
                    for link in self.reference_dict[s.lower()][link_type]:
                        text = '%s - %s: <a href="%s">%s</a>' % (s, link, self.reference_dict[s.lower()][link_type][link], link)
                        links.append(text)
        return links


    @staticmethod
    def list_from_bullets(message_widget):
        text = message_widget.text()
        text = text.replace('\n', '')
        return text.split(r'    * ')

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

    def on_software_chosen(self):
        bullet_text = self.sender().currentText()
        if bullet_text:
            if bullet_text not in str(self.message_software.text()):
                self.new_bullet_text(self.message_software, bullet_text)
                self.list_from_bullets(self.message_software)
                self.sender().setCurrentIndex(0)
            else:
                self.sender().setCurrentIndex(0)
        else:
            print 'No Text'

    def on_gui_chosen(self):
        self.show_stuff()
        self.message_files.setText('')
        self.message_files.hide()
        gui = self.sender().currentText()
        if gui:
            bullets = self.repo_dict[self.combo_repo.currentText()]['guis'][gui]
            for each in bullets:
                if '()' in each:
                    self.new_bullet_text(self.message_functions, each)
                else:
                    self.new_bullet_text(self.message_files, each)

    @staticmethod
    def new_bullet_text(message_widget, bullet_item):
        new_text = message_widget.text()
        if not new_text:
            new_text = '    * %s' % bullet_item
        else:
            new_text = '%s\n    * %s' % (new_text, bullet_item)
        message_widget.setText(new_text)
        message_widget.show()

    def add_bullets(self):
        if isinstance(self.sender(), QtWidgets.QLineEdit):
            current_text = self.sender().text()
            bullet_text = self.widget_dict[self.sender()].text()
            list_ = self.bullet_dict[self.sender()]
            list_.append(current_text)
            self.update_text_edit()
            if not bullet_text:
                requirements_text = '    * %s' % current_text
            else:
                requirements_text = '%s\n    * %s' % (bullet_text, current_text)
            self.widget_dict[self.sender()].setText(requirements_text)
            self.sender().setText('')
            self.widget_dict[self.sender()].show()


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

