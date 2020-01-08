from PySide import QtGui
import json
import os
from cgl.core.config import app_config
import ftrack_api


class TaskSetupGUI(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.previous_selection = ''
        layout = QtGui.QVBoxLayout(self)
        self.task_table = QtGui.QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.verticalHeader().hide()
        self.headers = ['Full Name', 'Short Name', 'Shots/Assets/Both', 'Schema']

        # organize layout
        # layout.addLayout(combo_layout)
        layout.addWidget(self.task_table)

        # self.schemas_combo.currentIndexChanged.connect(self.on_schema_changed)
        #self.task_table.itemClicked.connect(self.on_item_clicked)
        #self.task_table.currentItemChanged.connect(self.on_table_edited)
        #self.task_table.itemActivated.connect(self.on_table_edited)
        self.schemas = self.get_schemas()
        self.load_schemas()
        self.temp_globals = self._load_json(os.path.join(app_config()['paths']['root'], '_config', 'globals.json'))

    # def on_item_clicked(self):
    #     print self.task_table.currentItem().text()
    #     self.previous_selection = self.task_table.currentItem()
    #     self.on_table_edited()
    #
    # def on_table_edited(self):
    #     if self.previous_selection:
    #         print 1
    #         item = self.previous_selection
    #     else:
    #         print 2
    #         item = self.task_table.currentItem()
    #     longname = self.task_table.item(item.row(), 0).text()
    #     print longname
    #     #
    #     # self.schemas[longname]['long_name'] = self.task_table.item(item.row(), 0).text()
    #     # self.schemas[longname]['short_name'] = self.task_table.item(item.row(), 1).text()
    #     # self.schemas[longname]['type'] = self.task_table.item(item.row(), 2).text()
    #     # self.schemas[longname]['schema'] = self.task_table.item(item.row(), 3).text()

    def iterate_over_table(self):
        row_count = self.task_table.rowCount()

        for row in xrange(0, row_count):
            long_name = self.task_table.item(row, 0).text()
            short_name = self.task_table.item(row, 1).text()
            type_ = self.task_table.item(row, 2).text()
            # schema = self.task_table.item(row, 3).text()
            #self.schemas[long_name]['long_name'] = long_name
            self.schemas[long_name]['short_name'] = short_name
            self.schemas[long_name]['type'] = type_
            #self.schemas[long_name]['schema'] = schema

    def load_schemas(self):
        self.task_table.clear()
        row_count = len(self.schemas.keys())
        row = -1
        self.task_table.setRowCount(row_count)
        for task in self.schemas:
            row += 1
            longname = QtGui.QTableWidgetItem(self.schemas[task]['long_name'])
            shortname = QtGui.QTableWidgetItem(self.schemas[task]['short_name'])
            type_ = QtGui.QTableWidgetItem(self.schemas[task]['type'])
            schma = QtGui.QTableWidgetItem(str(self.schemas[task]['schema']))
            self.task_table.setItem(row, 0, longname)
            self.task_table.setItem(row, 1, shortname)
            self.task_table.setItem(row, 2, type_)
            self.task_table.setItem(row, 3, schma)
        self.task_table.setHorizontalHeaderLabels(self.headers)

    def get_schemas(self):
        if os.path.exists(os.path.join(app_config()['paths']['root'], '_config', 'lc_schemas.json')):
            return self._load_json(os.path.join(app_config()['paths']['root'], '_config', 'lc_schemas.json'))
        else:
            print 'Starting FTrack Session'
            session = ftrack_api.Session(server_url=app_config()['project_management']['ftrack']['api']['server_url'],
                                         api_key=app_config()['project_management']['ftrack']['api']['api_key'],
                                         api_user=app_config()['project_management']['ftrack']['api']['api_user'])
            print 'Querying Ftrack for Schemas & Tasks'
            schemas = session.query('ProjectSchema').all()
            all_tasks = {}
            for s in schemas:
                for task in s.get_types('Task'):
                    if not task['name'] in all_tasks:
                        all_tasks[task['name']] = {'long_name': task['name'],
                                                   'short_name': '',
                                                   'type': 'shots',
                                                   'schema': [s['name']]
                                                   }
                    else:
                        all_tasks[task['name']]['schema'].append(s['name'])
            session.close()
            self._write_json(os.path.join(app_config()['paths']['root'], '_config', 'lc_schemas.json'), all_tasks)
            return all_tasks

    @staticmethod
    def _write_json(filepath, data):
        print 'writing json to %s' % filepath
        with open(filepath, 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)

    @staticmethod
    def _load_json(filepath):
        with open(filepath) as jsonfile:
            data = json.load(jsonfile)
        return data

    def format_schemas(self):
        output_d = {}
        for key in self.schemas:
            long_name = self.schemas[key]['long_name']
            short_name = self.schemas[key]['short_name']
            type_ = self.schemas[key]['type']
            s_list = self.schemas[key]['schema']
            for s in s_list:
                # there needs to be a dictionary for each kind of schema
                if s not in output_d.keys():
                    output_d[s] = {}
                if 'long_to_short' not in output_d[s].keys():
                    output_d[s]['long_to_short'] = {}
                if 'short_to_long' not in output_d[s].keys():
                    output_d[s]['short_to_long'] = {}
                # there needs to be a dictionary for each type_
                if type_ == 'both':
                    if 'assets' not in output_d[s]['long_to_short'].keys():
                        output_d[s]['long_to_short']['assets'] = {}
                    if 'assets' not in output_d[s]['short_to_long'].keys():
                        output_d[s]['short_to_long']['assets'] = {}
                    if long_name not in output_d[s]['long_to_short'].keys():
                        output_d[s]['long_to_short']['assets'][long_name] = short_name
                    if long_name not in output_d[s]['short_to_long'].keys():
                        output_d[s]['short_to_long']['assets'][short_name] = long_name

                    if 'shots' not in output_d[s]['long_to_short'].keys():
                        output_d[s]['long_to_short']['assets'] = {}
                    if 'shots' not in output_d[s]['short_to_long'].keys():
                        output_d[s]['short_to_long']['shots'] = {}
                    if long_name not in output_d[s]['long_to_short'].keys():
                        output_d[s]['long_to_short']['shots'][long_name] = short_name
                    if long_name not in output_d[s]['short_to_long'].keys():
                        output_d[s]['short_to_long']['shots'][short_name] = long_name
                else:

                    if type_ not in output_d[s]['long_to_short'].keys():
                        output_d[s]['long_to_short'][type_] = {}
                    if long_name not in output_d[s]['long_to_short'].keys():
                        output_d[s]['long_to_short'][type_][long_name] = short_name

                    # there needs to be a dictionary for each type_
                    if type_ not in output_d[s]['short_to_long'].keys():
                        output_d[s]['short_to_long'][type_] = {}
                    if long_name not in output_d[s]['short_to_long'].keys():
                        output_d[s]['short_to_long'][type_][short_name] = long_name
        return output_d
        pass

    def closeEvent(self, event):
        print event
        self.iterate_over_table()
        formatted_tasks = self.format_schemas()
        self.temp_globals['project_management']['ftrack']['tasks'] = formatted_tasks
        print os.path.join(app_config()['paths']['root'], '_config', 'ftrack_tasks.json')
        self._write_json(os.path.join(app_config()['paths']['root'], '_config', 'globals.json'), self.temp_globals)
        #self._write_json(os.path.join(app_config()['paths']['root'], '_config', 'ftrack_tasks.json'), formatted_tasks)


if __name__ == "__main__":
    app = QtGui.QApplication([])
    form = TaskSetupGUI()
    form.show()
    app.exec_()

