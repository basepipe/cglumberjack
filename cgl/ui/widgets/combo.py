from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.ui.widgets.widgets import LJButton


class LabelComboRow(QtWidgets.QVBoxLayout):
    def __init__(self, label, button=True, bold=True, text=''):
        QtWidgets.QVBoxLayout.__init__(self)
        if bold:
            self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        else:
            self.label = QtWidgets.QLabel("%s" % label)
        self.combo = AdvComboBox()
        self.h_layout = QtWidgets.QHBoxLayout()
        self.h_layout.addWidget(self.label)
        self.h_layout.addWidget(self.combo)
        if button:
            self.button = button
            self.add_button = LJButton
            if not text:
                self.add_button.setText('+')
            else:
                self.add_button.setText(text)
            self.h_layout.addWidget(self.add_button)
            self.addLayout(self.h_layout)
            # self.addWidget(self.combo)
        else:
            self.h_layout.addWidget(self.combo)
            self.addLayout(self.h_layout)

    def hide(self):
        self.label.hide()
        self.combo.hide()
        if self.button:
            self.add_button.hide()

    def show(self):
        self.label.show()
        self.combo.show()
        if self.button:
            self.add_button.show()


class AdvComboBoxLabeled(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)


class AdvComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(AdvComboBox, self).__init__(parent)

        self.user_selected = False
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)
        self.setMinimumWidth(90)
        self.SizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        # self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        # add a filter model to filter matching items
        self.pFilterModel = QtCore.QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        # add a completer
        self.completer = QtWidgets.QCompleter(self)
        # Set the model that the QCompleter uses
        # - in PySide doing this as a separate step worked better
        self.completer.setModel(self.pFilterModel)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)

        self.setCompleter(self.completer)

        # connect signals

        def filter_(text):
            self.pFilterModel.setFilterFixedString(str(text))

        self.lineEdit().textEdited[unicode].connect(filter_)
        self.completer.activated.connect(self.on_completer_activated)
        self.set_placeholder_text()

    def set_placeholder_text(self, text='Type or Choose below...'):
        self.lineEdit().setPlaceholderText(text)

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        if text:
            index = self.findText(str(text))
            self.setCurrentIndex(index)

    # on model change, update the models of the filter and completer as well
    def setModel(self, model):
        super(AdvComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    # on model column change, update the model column of the filter and completer as well
    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(AdvComboBox, self).setModelColumn(column)

    def populate_from_project(self, keys):
        self.clear()
        # load the shading/texture assets from the library
        # clear duplicates
        obj_list = []
        for key in keys:
            if str(key) not in obj_list:
                obj_list.append(str(key))
        for item in obj_list:
            self.addItem(item)
