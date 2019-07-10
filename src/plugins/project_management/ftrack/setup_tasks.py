from Qt import QtCore, QtWidgets, QtGui
import json
from cglcore.config import app_config
import ftrack_api



class TaskSetupGUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        layout = QtWidgets.QVBoxLayout(self)

        #combo box stuff
        combo_layout = QtWidgets.QHBoxLayout()
        schemas_label = QtWidgets.QLabel("Schemas:")
        self.schemas_combo = QtWidgets.QComboBox()
        combo_layout.addWidget(schemas_label)
        combo_layout.addWidget(self.schemas_combo)

        self.task_table = QtWidgets.QTableWidget()
        self.task_table.setColumnCount(3)
        self.task_table.setHorizontalHeaderLabels(['Full Name', 'Short Name', 'Shots/Assets/Both'])

        # organize layout

        layout.addLayout(combo_layout)
        layout.addWidget(self.task_table)

        self.schemas_combo.currentIndexChanged.connect(self.on_schema_changed)
        self.schemas = self.get_schemas()
        self.load_schemas()

    def load_schemas(self):
        for s in self.schemas:
            self.schemas_combo.addItem(s)

    def on_schema_changed(self):
        self.task_table.clear()
        row = -1
        row_count = len(self.schemas[self.schemas_combo.currentText()])
        self.task_table.setRowCount(row_count)
        for task in self.schemas[self.schemas_combo.currentText()]:
            print task
            row += 1
            print row
            self.task_table.setItem(row, 0, QtWidgets.QTableWidgetItem(task))


    @staticmethod
    def get_schemas():
        session = ftrack_api.Session(server_url=app_config()['ftrack']['server_url'],
                                     api_key=app_config()['ftrack']['api_key'],
                                     api_user=app_config()['ftrack']['api_user'])
        schemas = session.query('ProjectSchema').all()
        all_schemas = {}
        for s in schemas:
            tasks = []
            for task in s.get_types('Task'):
                tasks.append(task['name'])
            all_schemas[s['name']] = tasks
        session.close()

        return all_schemas


if __name__ == "__main__":
    app = QtGui.QApplication([])
    form = TaskSetupGUI()
    form.show()
    app.exec_()

