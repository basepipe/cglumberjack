import os
from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.containers.table import LJTableWidget
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.dialog import InputDialog
from cglcore.path import PathObject, CreateProductionData


class LabelEditRow(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        self.lineEdit = QtWidgets.QLineEdit()
        self.addWidget(self.label)
        self.addWidget(self.lineEdit)


class LabelComboRow(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText('+')
        self.h_layout = QtWidgets.QHBoxLayout()
        self.h_layout.addWidget(self.label)
        self.h_layout.addWidget(self.add_button)
        self.combo = AdvComboBox()
        self.addLayout(self.h_layout)
        self.addWidget(self.combo)

    def hide(self):
        self.label.hide()
        self.combo.hide()

    def show(self):
        self.label.show()
        self.combo.show()


class FunctionButtons(QtWidgets.QHBoxLayout):
    def __init__(self):
        QtWidgets.QHBoxLayout.__init__(self)
        self.open_button = QtWidgets.QPushButton('Open')
        self.publish_button = QtWidgets.QPushButton('Publish')
        self.review_button = QtWidgets.QPushButton('Review')
        self.version_up = QtWidgets.QPushButton('Version Up')

        self.addWidget(self.open_button)
        self.addWidget(self.version_up)
        self.addWidget(self.review_button)
        self.addWidget(self.publish_button)


class AssetWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()

    def __init__(self, parent, title, filter_string=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        v_layout.setContentsMargins(0, 0, 0, 0)
        h_layout = QtWidgets.QHBoxLayout(self)
        self.tool_button_layout = QtWidgets.QHBoxLayout(self)
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title)

        self.versions = AdvComboBox()
        self.versions.setMinimumWidth(500)
        self.versions.hide()

        self.users_label = QtWidgets.QLabel("  User:")
        self.users = AdvComboBox()
        self.users_layout = QtWidgets.QHBoxLayout(self)
        self.users_layout.addWidget(self.users_label)
        self.users_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum))
        self.users_layout.addWidget(self.users)

        self.resolutions = AdvComboBox()
        self.resolutions_layout = QtWidgets.QHBoxLayout(self)
        self.resolutions_label = QtWidgets.QLabel("  Resolution:")
        self.resolutions_layout.addWidget(self.resolutions_label)
        self.resolutions_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                              QtWidgets.QSizePolicy.Minimum))
        self.resolutions_layout.addWidget(self.resolutions)

        self.message = QtWidgets.QLabel("")
        self.search_box = LJSearchEdit(self)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText("+")
        self.show_button = QtWidgets.QToolButton()
        self.show_button.setText("more")
        self.hide_button = QtWidgets.QToolButton()
        self.hide_button.setText("less")
        self.data_table = LJTableWidget(self)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.data_table.setMinimumWidth(340)

        # build the tool button row
        self.open_button = QtWidgets.QToolButton()
        self.open_button.setText('Open')
        self.new_version_button = QtWidgets.QToolButton()
        self.new_version_button.setText('New Version')
        self.review_button = QtWidgets.QToolButton()
        self.review_button.setText('Review')
        self.publish_button = QtWidgets.QToolButton()
        self.publish_button.setText('Publish')
        self.tool_button_layout.addWidget(self.open_button)
        self.tool_button_layout.addWidget(self.new_version_button)
        self.tool_button_layout.addWidget(self.review_button)
        self.tool_button_layout.addWidget(self.publish_button)

        # this is where the filter needs to be!
        h_layout.addWidget(self.title)
        h_layout.addWidget(self.versions)
        h_layout.addWidget(self.search_box)
        h_layout.addWidget(self.show_button)
        h_layout.addWidget(self.hide_button)
        h_layout.addWidget(self.add_button)

        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.message)
        v_layout.addLayout(self.users_layout)
        v_layout.addLayout(self.resolutions_layout)
        v_layout.addWidget(self.data_table, 1)
        v_layout.addLayout(self.tool_button_layout)
        self.hide_combos()

        self.message.hide()
        self.add_button.hide()
        self.hideall()
        self.show_button.clicked.connect(self.on_show_button_clicked)
        self.hide_button.clicked.connect(self.on_hide_button_clicked)
        self.add_button.clicked.connect(self.on_add_button_clicked)
        self.hide_tool_buttons()

    def hide(self):
        self.hide_button.hide()
        self.add_button.hide()
        self.data_table.hide()
        self.search_box.hide()
        self.show_button.hide()
        self.hide_button.hide()
        self.title.hide()
        self.users.hide()
        self.users_label.hide()
        self.resolutions.hide()
        self.resolutions_label.hide()

    def show(self, combos=False):
        self.show_button.show()
        self.data_table.show()
        self.search_box.show()
        self.show_button.show()
        self.hide_button.show()
        self.title.show()
        if combos:
            self.show_combos()

    def hide_tool_buttons(self):
        self.open_button.hide()
        self.new_version_button.hide()
        self.publish_button.hide()
        self.review_button.hide()

    def show_tool_buttons(self):
        self.open_button.show()
        self.new_version_button.show()
        self.publish_button.show()
        self.review_button.show()

    def show_combos(self):
        self.users.show()
        self.users_label.show()
        self.resolutions.show()
        self.resolutions_label.show()

    def hide_combos(self):
        self.users.hide()
        self.users_label.hide()
        self.resolutions.hide()
        self.resolutions_label.hide()

    def hideall(self):
        self.hide_button.hide()
        self.data_table.hide()

    def showall(self):
        self.hide_button.show()
        self.show_button.hide()
        self.data_table.show()

    def setup(self, mdl):
        self.data_table.set_item_model(mdl)
        self.data_table.set_search_box(self.search_box)

    def on_add_button_clicked(self):
        self.add_clicked.emit()

    def on_show_button_clicked(self):
        self.show_combos()
        self.hide_button.show()
        self.show_button.hide()

    def on_hide_button_clicked(self):
        self.hide_combos()
        self.hide_button.hide()
        self.show_button.show()

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())


class LineEditWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, read_only=True, label='Label'):
        QtWidgets.QWidget.__init__(self, parent)
        # create the current path
        self.label = QtWidgets.QLabel(label)
        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setReadOnly(read_only)
        self.row = QtWidgets.QHBoxLayout()
        self.row.addWidget(self.label)
        self.row.addWidget(self.line_edit)
        self.row.setContentsMargins(0,0,0,0)
        self.setLayout(self.row)

    def hide_all(self):
        self.label.hide()
        self.line_edit.hide()

    def show_all(self):
        self.label.show()
        self.line_edit.show()


class ProjectControlCenter(QtWidgets.QWidget):
    project_changed = QtCore.Signal(object)

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        # Create the Left Panel
        self.project = None
        self.root = app_config()['paths']['root']
        self.company = app_config()['account_info']['company']
        self.user_root = app_config()['cg_lumberjack_dir']
        self.user_default = 'tmikota'
        self.filter_layout = QtWidgets.QVBoxLayout(self)
        self.user_widget = LabelComboRow('User')
        self.user_widget.combo.addItem(self.user_default)
        # company
        self.company_widget = LabelComboRow('Company')
        # filters
        self.project_filter = AssetWidget(self, title="Project")
        self.project_filter.showall()
        self.project_filter.add_button.show()
        self.project_filter.hide_button.hide()
        self.radio_label = QtWidgets.QLabel('<b>Filter</b>')
        self.radio_layout = QtWidgets.QHBoxLayout(self)
        self.radio_user = QtWidgets.QRadioButton('User Assignments')
        self.radio_everyone = QtWidgets.QRadioButton('Everything')
        self.radio_publishes = QtWidgets.QRadioButton('Publishes')

        self.radio_layout.addWidget(self.radio_user)
        self.radio_user.setChecked(True)
        self.radio_layout.addWidget(self.radio_publishes)
        self.radio_layout.addWidget(self.radio_everyone)
        self.radio_layout.addItem(QtWidgets.QSpacerItem(340, 0, QtWidgets.QSizePolicy.Maximum,
                                                        QtWidgets.QSizePolicy.Minimum))
        # assemble the filter_panel
        self.filter_layout.addLayout(self.user_widget)
        self.filter_layout.addLayout(self.company_widget)
        self.filter_layout.addWidget(self.radio_label)
        self.filter_layout.addLayout(self.radio_layout)
        self.filter_layout.addWidget(self.project_filter)

        self.load_companies()
        self.load_projects()

        # TODO - Create Company Button
        # TODO - Create Project Button
        # TODO - Create User Button
        self.project_filter.data_table.selected.connect(self.on_project_changed)
        self.company_widget.add_button.clicked.connect(self.on_create_company)
        self.project_filter.add_button.clicked.connect(self.on_create_project)
        self.company_widget.combo.currentIndexChanged.connect(self.on_company_changed)

    def hide_filters(self):
        self.radio_label.hide()
        self.radio_user.hide()
        self.radio_everyone.hide()
        self.radio_publishes.hide()

    def load_companies(self, company=None):
        self.company_widget.combo.clear()
        companies_dir = os.path.join(self.user_root, 'companies')
        if os.path.exists(companies_dir):
            companies = os.listdir(companies_dir)
            print 'Companies: %s' % companies
            if not companies:
                dialog = InputDialog(buttons=['Create Company', 'Find Company'], message='No companies found in Config'
                                                                                         'location %s:' % companies_dir)
                dialog.exec_()
                if dialog.button == 'Create Company':
                    print 'Create Company pushed'
                elif dialog.button == 'Find Company':
                    company_paths = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                               'Choose existing company(ies) to add to '
                                                                               'the registry', self.root,
                                                                               QtWidgets.QFileDialog.ShowDirsOnly)
                    company = os.path.split(company_paths)[-1]
                    companies.append(company)
                    os.makedirs(os.path.join(companies_dir, company))
                # ask me to type the name of companies i'm looking for?
                # ask me to create a company if there are none at all.
                # Open the location and ask me to choose folders that are companies
        else:
            return

        self.company_widget.combo.addItem('')
        for each in companies:
            c = os.path.split(each)[-1]
            self.company_widget.combo.addItem(c)
        if not company:
            company = self.company
        index = self.company_widget.combo.findText(company)
        if index:
            self.company_widget.combo.setCurrentIndex(index)
        else:
            self.company_widget.combo.setCurrentIndex(0)

    def load_projects(self):
        d = {'root': self.root,
             'company': self.company,
             'project': '*',
             'context': 'source'}
        path_object = PathObject(d)
        projects = path_object.glob_project_element('project')
        if not projects:
            print 'no projects'
            self.project_filter.search_box.setEnabled(False)
            self.project_filter.data_table.setEnabled(False)
            self.radio_user.setEnabled(False)
            self.radio_everyone.setEnabled(False)
            self.radio_publishes.setEnabled(False)
            self.radio_label.setEnabled(False)
            self.project_filter.add_button.setText('Create First Project')
        else:
            self.project_filter.search_box.setEnabled(True)
            self.project_filter.data_table.setEnabled(True)
            self.project_filter.add_button.setText('+')
            self.radio_user.setEnabled(True)
            self.radio_everyone.setEnabled(True)
            self.radio_publishes.setEnabled(True)
            self.radio_label.setEnabled(True)
        self.project_filter.setup(ListItemModel(self.prep_list_for_table(projects, split_for_file=True), ['Name']))
        # self.update_location()

    @staticmethod
    def prep_list_for_table(list_, path_filter=None, split_for_file=False):
        # TODO - would be awesome to make this smart enough to know what to do with a dict, list, etc...
        list_.sort()
        output_ = []
        for each in list_:
            if path_filter:
                filtered = PathObject(each).data[path_filter]
                output_.append([filtered])
            else:
                if split_for_file:
                    each = os.path.split(each)[-1]
                output_.append([each])
        return output_

    def on_project_changed(self, data):
        self.project_changed.emit(data[0][0])


    def on_create_company(self):
        dialog = InputDialog(title='Create Company', message='Type a Company Name', line_edit=True)
        dialog.exec_()
        if dialog.button == 'Ok':
            self.company = '%s' % dialog.line_edit.text()
            d = {'root': self.root,
                 'company': self.company}
            self.create_company_globals(dialog.line_edit.text())
            CreateProductionData(d)
            self.load_companies(company=self.company)
            self.load_projects()

    def on_create_project(self):
        dialog = InputDialog(title='Create Project', message='Type a Project Name', line_edit=True)
        dialog.exec_()
        if dialog.button == 'Ok':
            project_name = dialog.line_edit.text()
            self.project = project_name
            self.update_location()
            CreateProductionData(self.current_location)
            self.load_projects()
        else:
            pass

    def on_company_changed(self):
        print 'combo changed'
        self.company = self.company_widget.combo.currentText()
        self.load_projects()
        if self.middle_layout:
            self.clear_layout(self.middle_layout)
        if self.render_layout:
            self.clear_layout(self.render_layout)

