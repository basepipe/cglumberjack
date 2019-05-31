import os
import yaml
import sys
import logging
from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config
from cglcore.path import icon_path
from cglui.widgets.containers.table import LJTableWidget
from cglui.startup import do_gui_init
from cglui.widgets.containers.model import ListItemModel
from preflight_check import PreflightCheck


class FileTableModel(ListItemModel):
    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == QtCore.Qt.DisplayRole:
            return self.data_[row][col]
        if role == QtCore.Qt.DecorationRole:
            data = self.data_[row][col]
            if data == 'Untested':
                ip = icon_path('checkbox_unchecked.png')
                return QtGui.QIcon(ip)
            if data == 'Pass':
                ip = icon_path('checkbox_checked.png')
                return QtGui.QIcon(ip)
            if data == 'Fail':
                ip = icon_path('checkbox_unchecked.png')
                return QtGui.QIcon(ip)


class ItemTable(LJTableWidget):
    item_selected = QtCore.Signal(object)
    nothing_selected = QtCore.Signal()

    def __init__(self, parent):
        LJTableWidget.__init__(self, parent)

        self.clicked.connect(self.row_selected)

    def mouseReleaseEvent(self, e):
        super(ItemTable, self).mouseReleaseEvent(e)
        self.row_selected()

    def row_selected(self):
        selected = []
        for index in self.selectedIndexes():
            mdl_index = self.model().mapToSource(index)
            mdl = self.model().sourceModel()
            row = mdl_index.row()
            sel = mdl.data_[row]
            data = {'Check': sel[0],
                    'Status': sel[1],
                    'Path': sel[2],
                    'Order': sel[3],
                    'Required': sel[4]}
            selected.append(data)
        if selected:
            self.item_selected.emit(selected)
        else:
            self.nothing_selected.emit()


class Preflight(QtWidgets.QWidget):

    def __init__(self, parent=None, software='maya', task='', model=None, **kwargs):
        QtWidgets.QWidget.__init__(self, parent)
        self.preflight_dir = os.path.join(app_config()['paths']['code_root'], 'src', 'tools', software, 'preflight')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.yaml_file = os.path.join(self.preflight_dir, task, 'order.yaml')
        self.modules = {}
        self.ignore = ['__init__.py']
        self.selected_checks = []
        self.function_d = {}
        self.table_data = []

        # for publishing single model from layout
        PreflightCheck.shared_data['preflight_dialog'] = self
        for key, value in kwargs.iteritems():
            PreflightCheck.shared_data[key] = value
        if model:
            PreflightCheck.shared_data['parent'] = parent
            PreflightCheck.shared_data['mdl'] = model
        # create the lay
        v_layout = QtWidgets.QVBoxLayout(self)
        combo_layout = QtWidgets.QHBoxLayout(self)

        # create the widgets
        self.preflights = ItemTable(self)
        self.software_label = QtWidgets.QLabel('Software')
        self.software_selector = QtWidgets.QComboBox(self)
        self.preflight_label = QtWidgets.QLabel('Preflight')
        self.preflight_selector = QtWidgets.QComboBox(self)
        self.run_all = QtWidgets.QPushButton('Run All')
        # self.run_all.hide()
        self.run_selected = QtWidgets.QPushButton('Run Selected')
        #self.publish_button = QtWidgets.QPushButton('Publish')

        # construct the GUI
        combo_layout.addWidget(self.software_label)
        combo_layout.addWidget(self.software_selector)
        combo_layout.addWidget(self.preflight_label)
        combo_layout.addWidget(self.preflight_selector)
        combo_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        button_bar = QtWidgets.QHBoxLayout(self)
        button_bar.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        button_bar.addWidget(self.run_selected)
        button_bar.addWidget(self.run_all)
        #button_bar.addWidget(self.publish_button)
        v_layout.addLayout(combo_layout)
        v_layout.addWidget(self.preflights)
        v_layout.addLayout(button_bar)

        # load the GUI
        self._load_yaml()
        self.populate_table()
        self.preflights.item_selected.connect(self.update_selection)
        self.run_selected.clicked.connect(self.run_selected_clicked)
        self.run_all.clicked.connect(self.run_all_clicked)
        #self.publish_button.clicked.connect(self.publish_clicked)

    def publish_clicked(self):
        pass

    def _load_yaml(self):
        print self.yaml_file
        with open(self.yaml_file, 'r') as stream:
            try:
                self.modules = yaml.load(stream)
            except yaml.YAMLError as exc:
                logging.error(exc)
                sys.exit(99)

    def populate_table(self):
        data = []
        for item in self.modules:
            print self.preflight_dir
            module = self.modules[item]['module']
            print module
            module_name = module.split('.')[-1]
            print module_name
            loaded_module = __import__(module, globals(), locals(), module_name, -1)
            class_ = getattr(loaded_module, module_name)
            c = class_()
            self.function_d.update({self.modules[item]['name']: c})
            data.append([self.modules[item]['name'],
                         'Untested',
                         self.modules[item]['module'],
                         self.modules[item]['order'],
                         self.modules[item]['required']])
        self.table_data = data
        self.preflights.set_item_model(FileTableModel(data, ["Check", "Status", "Path", "Order", "Required"]))
        self.preflights.sortByColumn(3, QtCore.Qt.SortOrder(0))
        self.preflights.hideColumn(2)
        self.preflights.hideColumn(3)

    def update_selection(self, data):
        self.selected_checks = data

    def run_selected_clicked(self, checks=None):
        if not checks:
            checks = self.selected_checks
        for each in checks:
            if self.previous_checks_passed(each):
                class_ = self.function_d[each['Check']]
                class_.run()
                if self.function_d[each['Check']].status:
                    each['Status'] = 'Passed'
                else:
                    each['Status'] = 'Failed'
                self.update_status(check=each['Check'], status=each['Status'])
            else:
                print "Can't run a check when previous required checks have not passed"

    def previous_checks_passed(self, check):
        mdl = self.preflights.model()
        if int(check["Order"]) == 1:
            return True
        for irow in range(int(check['Order'])-1):
            print irow, int(check['Order'])-1
            name = mdl.index(irow, 0)
            passed = mdl.index(irow, 1)
            required = mdl.index(irow, 4)
            if str(mdl.data(passed)) != str('Passed'):
                print '%s didnt pass' % str(mdl.data(name))
                if str(mdl.data(required)) == str(True):
                    print "Required Check Doesn't Pass: ", str(mdl.data(name)), str(mdl.data(passed)), \
                        str(mdl.data(required))
                    return False
                else:
                    print "Check Failed, Not Required, Next Check Enabled"
                    return True
        return True
        # get a list of all the checks before me
        # if any of them have "Required" as True and "Failed" send a popup

    def update_status(self, check, status):
        row = -1
        for each in self.table_data:
            row += 1
            if each[0] == check:
                self.table_data[row][1] = status
        # refresh the table with self.table_data
        self.preflights.set_item_model(FileTableModel(self.table_data,
                                                      ["Check", "Status", "Path", "Order", "Required"]))
        self.preflights.hideColumn(2)
        self.preflights.hideColumn(3)

    def run_all_clicked(self):
        model = self.preflights.model()
        all_rows = []
        for irow in range(model.rowCount()):
            data = {'Check': str(model.data(model.index(irow, 0))),
                    'Status': str(model.data(model.index(irow, 1))),
                    'Path': str(model.data(model.index(irow, 2))),
                    'Order': str(model.data(model.index(irow, 3))),
                    'Required': str(model.data(model.index(irow, 4)))}
            all_rows.append(data)

        self.run_selected_clicked(checks=all_rows)


def main():
    app = do_gui_init()
    task = 'mdl'
    mw = Preflight(software='Maya', task=task)
    mw.setWindowTitle('%s Preflight' % task)
    mw.show()
    mw.raise_()
    app.exec_()


if __name__ == "__main__":
    # execute only if run as a script
    main()
