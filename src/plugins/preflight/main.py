import os
import json
import sys
import logging
from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config
from cglcore.path import icon_path, image_path, get_cgl_config
from cglui.widgets.containers.table import LJTableWidget
from cglui.startup import do_gui_init
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.widgets import GifWidget
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


class Preflight(QtWidgets.QDialog):
    signal_one = QtCore.Signal(object)

    def __init__(self, parent=None, software='lumbermill', preflight='', model=None, **kwargs):
        QtWidgets.QDialog.__init__(self, parent)
        self.software = software
        self.preflight = preflight
        self.software_dir = os.path.join(app_config()['paths']['cgl_tools'], software)
        self.preflight_dir = os.path.join(self.software_dir, 'preflights')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.json_file = os.path.join(self.software_dir, 'preflights.cgl')
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
        self.preflights.setMinimumWidth(800)
        self.preflights.setMinimumHeight(250)
        self.software_label = QtWidgets.QLabel('Preflight Checks')
        self.software_label.setProperty('class', 'ultra_title')

        self.image_plane = GifWidget(gif_path=image_path('rolling_logs.gif'))
        # self.image_plane.start()
        self.image_plane.hide()

        self.run_all = QtWidgets.QPushButton('Run All')
        self.run_all.setProperty('class', 'add_button')
        self.run_selected = QtWidgets.QPushButton('Run Selected')
        self.run_selected.setProperty('class', 'basic')

        # construct the GUI
        combo_layout.addWidget(self.software_label)
        combo_layout.addStretch(1)
        ##combo_layout.addWidget(self.software_selector)
        #c#ombo_layout.addWidget(self.preflight_label)
        #c#ombo_layout.addWidget(self.preflight_selector)
        #combo_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        button_bar = QtWidgets.QHBoxLayout(self)
        button_bar.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        button_bar.addWidget(self.run_selected)
        button_bar.addWidget(self.run_all)
        v_layout.addLayout(combo_layout)
        v_layout.addWidget(self.preflights)
        v_layout.addWidget(self.image_plane)
        v_layout.addLayout(button_bar)

        # load the GUI
        self._load_json()
        self.populate_table()
        self.preflights.item_selected.connect(self.update_selection)
        self.run_selected.clicked.connect(self.run_selected_clicked)
        self.run_all.clicked.connect(self.run_all_clicked)

    def _load_json(self):
        print self.json_file
        print self.software, self.preflight
        with open(self.json_file, 'r') as stream:
            self.modules = json.load(stream)[self.software][self.preflight]

    def populate_table(self):
        import sys
        source_dir = os.path.join(app_config()['paths']['cgl_tools'])
        source_dir = os.path.dirname(source_dir)
        sys.path.insert(0, source_dir)
        data = []
        for item in self.modules:
            if item != 'order':
                module = self.modules[item]['module']
                module_name = module.split('.')[-1]
                loaded_module = __import__(module, globals(), locals(), module_name, -1)
                class_ = getattr(loaded_module, module_name)
                c = class_()
                self.function_d.update({self.modules[item]['label']: c})
                data.append([self.modules[item]['label'],
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
        # TODO - probably need to figure out how to multithread this so i can run gifs at the same time ;)
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

    def send_signal_one(self, data):
        self.signal_one.emit(data)

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
        self.image_plane.start()
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
        self.image_plane.stop()


def main():
    app = do_gui_init()
    task = 'mdl'
    mw = Preflight(software='Maya', preflight=task)
    mw.setWindowTitle('%s Preflight' % task)
    mw.show()
    mw.raise_()
    app.exec_()


if __name__ == "__main__":
    # execute only if run as a script
    main()
