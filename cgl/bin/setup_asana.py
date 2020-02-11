import requests
import shutil
import os
import sys
from cgl.plugins.Qt import QtGui
from cgl.core.config import app_config
from cgl.ui.widgets.base import LJDialog
from cgl.ui.widgets.widgets import AdvComboBox
from core.util import load_xml, save_xml

workspace = "1145700648005039"
CONFIG = app_config()
ROOT = CONFIG['paths']['code_root']


class SetupGUI(LJDialog):
    def __init__(self, parent=None, title='Setup'):
        LJDialog.__init__(self)
        print "hello"
        self.setWindowTitle("Setup")
        self.authorization = ""

        self.project_dict = {}
        self.project_names = self.get_projects()

        self.label_asana = QtWidgets.QLabel("Asana")
        self.edit_label = QtWidgets.QLabel("API_Key")
        self.project_label = QtWidgets.QLabel("Project")
        self.label_asana.setProperty('class', 'ultra_title')
        self.submit_button = QtWidgets.QPushButton("Submit")
        self.submit_button.setProperty('class', 'basic')
        self.user_line_edit = QtWidgets.QLineEdit()
        self.project_combo = AdvComboBox()

        self.project_combo.addItems("")
        num = self.project_combo.findText("")
        self.project_combo.setCurrentIndex(num)

        layout = QtWidgets.QFormLayout()

        user_id = QtWidgets.QHBoxLayout()
        user_id.addWidget(self.edit_label)
        user_id.addWidget(self.user_line_edit)

        project_row = QtWidgets.QHBoxLayout()
        project_row.addWidget(self.project_label)
        project_row.addWidget(self.project_combo)

        layout.addRow(self.label_asana)
        layout.addRow(user_id)
        layout.addRow(project_row)
        layout.addWidget(self.submit_button)
        self.setLayout(layout)

        self.submit_button.hide()

        self.user_line_edit.editingFinished.connect(self.set_projects)
        self.project_combo.currentIndexChanged.connect(self.get_project_id)
        self.submit_button.clicked.connect(self.submit_info)

    def get_project_id(self):
        if self.project_combo.currentText() != '':
            name = self.project_combo.currentText()
            project = self.project_dict[name]
            id = project['gid']
            return id

    def get_projects(self):
        result = []
        response = requests.get("https://app.asana.com/api/1.0/projects", headers={'Authorization': self.authorization})
        if response.status_code == 200:
            for project in response.json()['data']:
                self.project_dict[project['name']] = project
                result.append(project['name'])
            return result

    def set_projects(self):
        api_key = self.user_line_edit.text()
        self.authorization = "Bearer %s" % api_key
        if self.get_projects():
            self.project_combo.addItems(self.get_projects())
            self.submit_button.show()

    def get_line_edit_text(self):
        return self.user_line_edit.text()

    def submit_info(self):
        self.copy_settings()
        user_id = self.user_line_edit.text()
        project_id = self.get_project_id()
        self.edit_xml(user_id, project_id)
        self.close()

    def copy_settings(self):
        """
        Settings for pycharm editor will already be setup by onboarding setup script
        :return:
        """
        githook_file = os.path.join(ROOT, 'resources', 'githooks', 'post-checkout')
        destination_file = os.path.join(ROOT, '.git', 'hooks', 'post-checkout')
        shutil.copy(githook_file, destination_file)

    def edit_xml(self, user_id, project_id):
        xml_file = os.path.join(ROOT, 'resources', 'pycharm_setup', 'workspace.xml')
        docs = load_xml(xml_file)
        for item in docs['project']['component']:
            if item['@name'] == "TaskManager":
                item['servers']['Generic']['username'] = user_id
                # print item['servers']['Generic']['username']
                for element in item['servers']['Generic']['option']:
                    if element['@name'] == "templateVariables":
                        element['list']['TemplateVariable'][0]['option'][1]['@value'] = project_id
                       # print element['list']['TemplateVariable'][0]['option'][1]['@value']
        idea_xml = os.path.join(ROOT, '.idea', 'workspace.xml')
        save_xml(idea_xml, docs)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    s = SetupGUI()
    s.show()
    app.exec_()
