import requests
import os
from PySide2 import QtWidgets, QtGui
from cgl.core.project import get_companies
from cgl.core.config import get_globals_path
from cgl.core.utils.general import cgl_execute


class GithubRegistry(QtWidgets.QDialog):
    def __init__(self,parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle("Enter Github Information")
        self.layout = QtWidgets.QVBoxLayout(self)

        github_username_layout = QtWidgets.QHBoxLayout()
        github_key_layout = QtWidgets.QHBoxLayout()
        company_layout = QtWidgets.QHBoxLayout()

        self.github_username_label = QtWidgets.QLabel("Github Username: ")
        self.github_username_line_edit = QtWidgets.QLineEdit()
        github_username_layout.addWidget(self.github_username_label)
        github_username_layout.addWidget(self.github_username_line_edit)

        self.github_key_label = QtWidgets.QLabel("Github Api Key: ")
        self.github_key_line_edit = QtWidgets.QLineEdit()
        github_key_layout.addWidget(self.github_key_label)
        github_key_layout.addWidget(self.github_key_line_edit)

        self.company_label = QtWidgets.QLabel("Company Name: ")
        self.company_combo_box = QtWidgets.QComboBox()
        company_layout.addWidget(self.company_label)
        company_layout.addWidget(self.company_combo_box)
        self.company_combo_box.addItems(get_companies())

        self.create_repo_button = QtWidgets.QPushButton("Create Repository")

        self.layout.addLayout(github_username_layout)
        self.layout.addLayout(github_key_layout)
        self.layout.addLayout(company_layout)
        self.layout.addWidget(self.create_repo_button)

        self.github_url = "https://api.github.com"

        self.create_repo_button.clicked.connect(self.create_repo)

    def create_repo(self):
        authorize = (self.github_username_line_edit.text(), self.github_key_line_edit.text())
        data = {
            "name": "_config",
            "description": "CGL_Tools Config Repo",
            "homepage": "https://github.com",
            "private": False,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": True
        }
        r = requests.post("%s/user/repos" % self.github_url, auth=authorize, json=data)
        print (r.status_code)
        print (r.content)
        self.register_local_repo()

    def register_local_repo(self):
        repo_path = get_globals_path()[:-len("\globals.json")]
        os.chdir(repo_path)
        os.system("dir")
        os.system("git init")
        os.system("git add -A")
        os.system("git commit -m Initialize")
        command = "git remote add origin https://github.com/%s/_config" % self.github_username_line_edit.text()
        os.system(command)
        os.system("git push -u origin master")
        print (repo_path)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    form = GithubRegistry()
    form.show()
    app.exec_()