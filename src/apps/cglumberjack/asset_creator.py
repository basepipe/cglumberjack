import re
import os
import glob
from core.path import CreateProductionData, PathObject
from Qt import QtWidgets, QtCore

from core.config import app_config
from cglui.widgets.base import LJDialog
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.dialog import InputDialog
from cglui.widgets.containers.table import LJTableWidget


class AssetWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()

    def __init__(self, parent, title, filter_string=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout(self)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title)
        self.message = QtWidgets.QLabel("")
        self.search_box = LJSearchEdit(self)
        self.button = QtWidgets.QToolButton()
        self.button.setText("+")
        self.data_table = LJTableWidget(self)
        self.data_table.setMinimumHeight(200)

        # this is where the filter needs to be!
        h_layout.addWidget(self.title)
        h_layout.addWidget(self.search_box)
        h_layout.addWidget(self.button)

        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.message)
        v_layout.addWidget(self.data_table, 1)

        self.message.hide()
        self.button.clicked.connect(self.on_button_clicked)

    def setup(self, mdl):
        self.data_table.set_item_model(mdl)
        self.data_table.set_search_box(self.search_box)

    def on_button_clicked(self):
        data = {'title': self.label}
        self.button_clicked.emit(data)

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())


class AssetCreator(LJDialog):
    def __init__(self, parent=None, title='Create Assets', path_dict=None):
        LJDialog.__init__(self, parent)
        self.resize(600, 60)
        if not path_dict:
            return
        self.path_object = PathObject(path_dict)
        self.company = None
        self.project = None
        self.scope = "shots"
        self.asset = None
        self.assets = []
        self.asset_message_string = ''
        self.asset_list = []
        self.shot = None
        self.seq = None
        self.full_root = None
        self.regex = ''
        self.valid_categories_string = ''
        self.valid_categories = []
        self.get_valid_categories()
        # Environment Stuff
        self.root = app_config()['paths']['root']
        self.project_management = app_config()['account_info']['project_management']
        self.asset_string_example = app_config()['rules']['path_variables']['asset']['example']
        self.v_layout = QtWidgets.QVBoxLayout(self)
        self.grid_layout = QtWidgets.QGridLayout(self)
        self.scope_row = QtWidgets.QHBoxLayout()
        self.asset_row = QtWidgets.QHBoxLayout(self)
        self.task_row = QtWidgets.QHBoxLayout(self)
        self.task_combo = AdvComboBox()

        # radio button stuff
        self.shots_radio = QtWidgets.QRadioButton('Shots')
        self.assets_radio = QtWidgets.QRadioButton('Assets')
        self.assets_radio.setChecked(True)
        self.radio_layout = QtWidgets.QHBoxLayout(self)
        self.radio_layout.addWidget(self.shots_radio)
        self.radio_layout.addWidget(self.assets_radio)
        self.radio_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum))

        # asset & shot stuff
        self.asset_message = QtWidgets.QLabel("")
        self.asset_widget = AssetWidget(self, title="")
        self.asset_row.addWidget(self.asset_widget)
        self.asset_widget.button.hide()
        # task stuff

        self.v_layout.addLayout(self.radio_layout)
        self.v_layout.addLayout(self.asset_row)
        self.on_scope_changed()

        self.assets_radio.clicked.connect(self.on_scope_changed)
        self.shots_radio.clicked.connect(self.on_scope_changed)
        self.asset_widget.search_box.textChanged.connect(self.asset_text_changed)
        self.asset_widget.search_box.returnPressed.connect(self.on_asset_text_enter)

    def on_create_company(self):
        print 'create company'
        dialog = InputDialog(title='Create Company', message='Type a Company Name', line_edit=True)
        dialog.exec_()
        self.company = dialog.line_edit.text()
        self.full_root = r'%s\cgl-%s' % (self.root, self.company)
        #os.path.mkdirs(self.full_root)  # is there a way to work this into create_production_data?

    def on_create_project(self):
        print 'create project'
        dialog = InputDialog(title='Create Project', message='Type a Project Name', line_edit=True)
        dialog.exec_()
        project_name = dialog.line_edit.text()
        print 'This (line 129) is depreciated'
        #CreateProductionData(self.current_location, project_management=self.project_management)
        #create_production_data(project=project_name, with_root=False,
        #                       custom_root=self.full_root)
        #create_production_data(project=project_name, scope='shots', with_root=False,
        #                       custom_root=self.full_root)
        #self.project_combo.insertItem(0, project_name)
        #self.get_current_location()

    def on_root_combo_changed(self):
        self.root = self.root_combo.currentText()
        self.company = None
        self.company_combo.clear()
        companies = []
        if os.path.exists(self.root_combo.currentText()):
            self.root = self.root_combo.currentText()
            for each in os.listdir(self.root_combo.currentText()):
                if 'cgl-' in each:
                    companies.append(each)
            self.company_combo.addItems(companies)
        self.get_current_location()

        # TODO - need a regex that helps me know if i have a legal root.

    def on_company_combo_changed(self):
        self.company = self.company_combo.currentText()
        if self.company:
            self.full_root = r'%s\%s' % (self.root, self.company)
            print self.full_root, 'self root'
        else:
            print "No company selected"
            return
        self.project = None
        self.project_combo.clear()
        projects = []
        path = os.path.join(self.full_root, 'source')
        if os.path.exists(path):
            for each in os.listdir(path):
                projects.append(each)
            self.project_combo.addItems(projects)
        else:
            print '%s does not exist yet' % path
        self.get_current_location()

    def asset_text_changed(self):
        string_ = self.asset_widget.search_box.text()
        if string_:
            # meat of everything happens here in process asset string
            self.process_asset_string(string_)
            self.asset_widget.message.setText(self.asset_message_string)
            self.asset_widget.message.show()
        else:
            self.asset_widget.message.hide()
        self.get_current_location()

    def check_asset_name(self, test_string):

        if re.match(self.regex, test_string):
            return test_string
        else:
            return '%s is an invalid asset name' % test_string

    def process_asset_string(self, asset_string):
        # TODO - add something here that also filters by the argument(s) given.
        asset_rules = r'^[a-zA-Z]{3,}:([a-zA-Z]{3,},\s*)*([a-zA-Z]{3,}$)|^([a-zA-Z]{3,},\s*)*([a-zA-Z]{3,}$)'
        self.regex = re.compile(r'%s' % asset_rules)
        if re.match(self.regex, asset_string):
            print '%s matches regex' % asset_string
            # if it has a :
            if ':' in asset_string:
                print 'found :'
                self.seq, asset_string = asset_string.split(':')
                # if it's a bunch of assets comma separated
                if ',' in asset_string:
                    self.asset_list = self.remove_spaces_on_list(asset_string.split(','))
                    if self.seq in self.valid_categories:
                        if self.asset_list:
                            self.asset_message_string = 'Click Enter to Create:'
                            for i, _ in enumerate(self.asset_list):
                                name = '%s:%s' % (self.seq, self.asset_list[i])
                                self.asset_list[i] = name
                                self.asset_message_string = '%s\n%s' % (self.asset_message_string, name)
                    else:
                        self.asset_message_string = '%s Not Valid Category! Try: %s' % (self.seq,
                                                                                        self.valid_categories_string)
                else:
                    self.asset_message_string = 'Click Enter to Create: \n%s:%s' % (self.seq, asset_string)
            elif ',' in asset_string:
                print 'asset_string:', asset_string
                self.asset_list = self.remove_spaces_on_list(asset_string.split(','))
                if self.asset_list:
                    self.asset_message_string = 'Click Enter to Create:'
                    for i, _ in enumerate(self.asset_list):
                        name = '%s:%s' % ('Prop', self.asset_list[i])
                        self.asset_list[i] = name
                        self.asset_message_string = '%s\n%s' % (self.asset_message_string, name)
            else:
                self.asset_list = []
                if not self.seq:
                    self.seq = 'Prop'
                self.asset_list.append('%s:%s' % (self.seq, asset_string))
                self.asset_message_string = 'Click Enter to Create: \n%s' % self.asset_list[0]

        else:
            print '%s does not match regex' % asset_string
            self.asset_message_string = '%s does not pass naming convention\n%s' % (asset_string,
                                                                                    self.asset_string_example)

    def get_valid_categories(self):
        categories = app_config()['asset_categories']
        for each in categories:
            self.valid_categories.append(each)
            self.valid_categories_string = '%s, %s' % (self.valid_categories_string, each)

    @staticmethod
    def remove_spaces_on_list(list_):
        new_list = []
        for each in list_:
            new_list.append(each.replace(' ', ''))
        return new_list

    def on_scope_changed(self):
        if self.assets_radio.isChecked():
            self.scope = 'assets'
        else:
            self.scope = 'shots'
        print self.scope
        self.asset_widget.set_title(self.scope)
        self.asset_widget.message.hide()
        self.asset_widget.search_box.clear()
        self.get_current_location()
        self.load_assets()

    def get_current_location(self):
        if self.path_object.company:
            self.path_object.new_set_attr(root=self.full_root)
        if self.project:
            self.path_object.new_set_attr(project=self.project)
            self.path_object.new_set_attr(scope=self.scope.lower())
            self.path_object.new_set_attr(context='source')
        else:
            return self.path_object.path_root
        if self.path_object.scope == 'shots':
            if self.seq:
                self.path_object.new_set_attr(seq=self.seq)
            if self.shot:
                self.path_object.new_set_attr(shot=self.shot)
        elif self.path_object.scope == 'assets':
            self.path_object.new_set_attr(type=self.seq)
            self.path_object.new_set_attr(asset=self.shot)

    def load_assets(self):
        print 'loading %s from %s' % (self.scope, self.path_object.__dict__)
        self.path_object.seq = '*'
        self.path_object.shot = '*'
        self.path_object.task = ''
        self.path_object.user = ''
        print self.path_object.path_root
        glob_path = self.path_object.path_root
        glob_path = re.sub('/+$', '', glob_path)
        print glob_path
        list_ = glob.glob(glob_path)
        print 'list %s' % list_
        self.assets = []
        for each in list_:
            asset = each.split('%s\\' % self.scope)[-1].replace('\\', ':')
            self.assets.append([asset])
        self.asset_widget.setup(ListItemModel(self.assets, ['Name']))

    def load_tasks(self):
        task_list = app_config()['pipeline_steps'][self.scope.lower()]
        tasks = ['']
        for each in task_list:
            tasks.append(each)
        print tasks
        print "I'm meant to load tasks in some kind of gui: %s" % tasks

    @staticmethod
    def is_valid_asset():
        pass

    @staticmethod
    def is_valid_shot():
        pass

    def on_asset_text_enter(self):
        if 'Click Enter' in self.asset_widget.message.text():
            if self.asset_widget.search_box.text() != '':
                self.path_object.new_set_attr(asset=self.asset_widget.search_box.text())
                self.path_object.new_set_attr(type='Prop')
                for each in app_config()['pipeline_steps']['assets']['default_steps']:
                    self.path_object.new_set_attr(task=each)
                    # self.path_object.new_set_attr(resolution='high')
                    # self.path_object.new_set_attr(version='000.000')
                    # self.path_object.new_set_attr(user='tmikota')
                    print 'Current Path With Root: %s' % self.path_object.path_root
                    CreateProductionData(self.path_object.data,
                                         project_management=self.project_management)


if __name__ == "__main__":
    from cglui.startup import do_gui_init

    app = do_gui_init()
    td = AssetCreator()
    td.setWindowTitle('Project Builder')
    td.show()
    td.raise_()
    app.exec_()