import os
from vfxwindow import VFXWindow
from cgl.core.config import app_config, UserConfig, user_config
from cgl.plugins.blender.cgl_browser_widget import BrowserWidget
from PySide2 import QtWidgets, QtCore, QtGui
import logging

USERCONFIG = UserConfig().d
ICON_WIDTH = 24
CONFIG = app_config()


class CGLumberjack(VFXWindow):
    def __init__(self, show_import=True, user_info=None, start_time=None, previous_path=None, sync_enabled=True):
        VFXWindow.__init__(self)

        if start_time:
            logging.debug('Finished Loading Lumbermill in %s seconds' % (time.time() - start_time))
        self.user_config = UserConfig().d
        if previous_path:
            self.previous_path = previous_path
            self.previous_paths = []
        else:
            self.previous_path = self.user_config['previous_path']
            self.previous_paths = self.user_config['previous_paths']
        self.filter = 'Everything'
        self.project_management = CONFIG['account_info']['project_management']
        self.user_info = ''
        self.user_email = ''
        if user_info:
            self.user_info = user_info
            if user_info['login']:
                self.user_email = user_info['login']
        self.user_name = ''
        self.company = ''
        self.pd_menus = {}
        self.menu_dict = {}
        self.menus = {}
        self.setCentralWidget(BrowserWidget(self, project_management=self.project_management,
                                                  user_email=self.user_info,
                                                  company=self.company,
                                                  path=self.previous_path,
                                                  radio_filter=self.filter,
                                                  show_import=True))
        if user_info:
            if user_info['first']:
                self.setWindowTitle('Lumbermill - Logged in as %s' % user_info['first'])
            else:
                self.setWindowTitle('Lumbermill - Logged in as %s' % user_info['login'])
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

        # Load Style Sheet and set up Styles:
        w = 400
        h = 500

        self.resize(w, h)
        self.menu_bar = self.menuBar()
        self.two_bar = self.menuBar()
        icon = QtGui.QPixmap(":/images/lumberjack.24px.png").scaled(24, 24)
        self.setWindowIcon(icon)
        self.load_syncthing = True
        login = QtWidgets.QAction('login', self)
        time_tracking = QtWidgets.QAction('time', self)
        proj_man = QtWidgets.QAction('%s' % self.project_management, self)
        update_button = QtWidgets.QAction('Check For Updates', self)
        report_bug_button = QtWidgets.QAction('Report Bug', self)
        request_feature_button = QtWidgets.QAction('Request Feature', self)
        tools_menu = self.menu_bar.addMenu('&Tools')
        self.sync_menu = self.menu_bar.addMenu('&Sync')
        if self.project_management != 'lumbermill':
            self.proj_man_link = self.two_bar.addAction(proj_man)
        self.login_menu = self.two_bar.addAction(login)
        self.two_bar.addAction(time_tracking)
        settings = QtWidgets.QAction('Settings', self)
        open_globals = QtWidgets.QAction('Go to Company Globals', self)
        open_user_globals = QtWidgets.QAction('Go to User Globals', self)
        create_project = QtWidgets.QAction('Import .csv', self)
        settings.setShortcut('Ctrl+,')
        alchemists_cookbook = QtWidgets.QAction("Alchemist's cookbook", self)
        set_up_sync_thing_server = QtWidgets.QAction('Set up Server', self)
        set_up_sync_thing_workstation = QtWidgets.QAction('Set Up Workstation', self)
        # check_machines_action = QtWidgets.QAction('Check for new Machines', self)
        # add_machines_to_folders = QtWidgets.QAction('Share Folders With Machines', self)
        # pull_from_server = QtWidgets.QAction('Pull from Server', self)
        manage_sharing_action = QtWidgets.QAction('Share Files', self)
        launch_syncthing = QtWidgets.QAction('Start Syncing', self)
        kill_syncthing = QtWidgets.QAction('Stop Syncing', self)
        show_sync_thing_browser = QtWidgets.QAction('Show Details', self)
        self.auto_launch_setting = QtWidgets.QAction('Auto-Launch: Off', self)
        self.current_processing_method = QtWidgets.QMenu('Processing Method: Local', self)
        change_to_local = QtWidgets.QAction('Set to Local', self)
        change_to_smedge = QtWidgets.QAction('Set to Smedge', self)
        change_to_deadline = QtWidgets.QAction('Set to Deadline', self)
        # fix_paths = QtWidgets.QAction('Fix File Paths', self)



        # add actions to the file menu
        tools_menu.addAction(settings)
        tools_menu.addAction(open_globals)
        tools_menu.addAction(open_user_globals)
        tools_menu.addSeparator()
        tools_menu.addMenu(self.current_processing_method)
        tools_menu.addSeparator()
        tools_menu.addAction(create_project)
        tools_menu.addAction(alchemists_cookbook)
        tools_menu.addSeparator()
        tools_menu.addAction(update_button)
        tools_menu.addAction(report_bug_button)
        tools_menu.addAction(request_feature_button)
        # connect signals and slots

        self.current_processing_method.addAction(change_to_local)
        self.current_processing_method.addAction(change_to_smedge)
        self.current_processing_method.addAction(change_to_deadline)

        self.sync_menu.addAction(manage_sharing_action)
        self.sync_menu.addSeparator()
        self.sync_menu.addAction(set_up_sync_thing_server)
        # self.sync_menu.addAction(check_machines_action)
        # self.sync_menu.addAction(add_machines_to_folders)
        self.sync_menu.addSeparator()
        self.sync_menu.addAction(set_up_sync_thing_workstation)
        # self.sync_menu.addAction(pull_from_server)
        # self.sync_menu.addAction(fix_paths)
        self.sync_menu.addSeparator()
        self.sync_menu.addAction(kill_syncthing)
        self.sync_menu.addAction(launch_syncthing)
        self.sync_menu.addAction(show_sync_thing_browser)
        self.sync_menu.addSeparator()
        self.sync_menu.addAction(self.auto_launch_setting)

        # connect signals and slots
        change_to_deadline.triggered.connect(self.change_processing_method)
        change_to_local.triggered.connect(self.change_processing_method)
        change_to_smedge.triggered.connect(self.change_processing_method)
        kill_syncthing.triggered.connect(self.on_kill_syncthing)
        launch_syncthing.triggered.connect(self.on_launch_syncthing)
        # pull_from_server.triggered.connect(self.enable_server_connection_clicked)
        # check_machines_action.triggered.connect(self.check_for_machines_clicked)
        # add_machines_to_folders.triggered.connect(self.add_machines_to_folders_clicked)
        manage_sharing_action.triggered.connect(self.manage_sharing_action_clicked)
        show_sync_thing_browser.triggered.connect(self.show_sync_details)
        self.auto_launch_setting.triggered.connect(self.toggle_auto_launch)
        set_up_sync_thing_server.triggered.connect(self.set_up_st_server_clicked)
        set_up_sync_thing_workstation.triggered.connect(self.set_up_st_workstation_clicked)
        open_globals.triggered.connect(self.open_company_globals)
        open_user_globals.triggered.connect(self.open_user_globals)
        create_project.triggered.connect(self.open_create_project_dialog)
        settings.triggered.connect(self.on_settings_clicked)
        alchemists_cookbook.triggered.connect(self.on_menu_designer_clicked)
        login.triggered.connect(self.on_login_clicked)
        proj_man.triggered.connect(self.on_proj_man_menu_clicked)
        update_button.triggered.connect(self.update_lumbermill_clicked)
        report_bug_button.triggered.connect(self.report_bug_clicked)
        request_feature_button.triggered.connect(self.feature_request_clicked)
        time_tracking.triggered.connect(self.time_tracking_clicked)
        # Load any custom menus that the user has defined
        self.load_pipeline_designer_menus()
        self.set_auto_launch_text()
        self.set_processing_method_text()
        # TODO how do i run this as a background process, or a parallell process?
        # TODO - how do i grab the pid so i can close this when lumbermill closes potentially?
        if sync_enabled:
            try:
                if CONFIG['sync']['syncthing']['sync_thing_url']:

                    # TODO - check for user config settings to use syncthing.
                    if "sync_thing_auto_launch" in USERCONFIG.keys():
                        try:
                            import cgl.plugins.syncthing.utils as st_utils
                            if USERCONFIG["sync_thing_auto_launch"] == 'True':
                                sync = False
                                st_utils.kill_syncthing()
                                if st_utils.syncthing_running():
                                    self.change_sync_icon(syncing=True)
                                    sync = True
                                else:
                                    self.change_sync_icon(syncing=False)
                                    # TODO - turn icon to not syncing
                                self.lumber_watch = launch_lumber_watch(new_window=True)
                                # TODO if syncthing is set as a feature in the globals!!!!
                                try:
                                    st_utils.launch_syncthing()
                                    self.change_sync_icon(syncing=True)
                                except:
                                    # this is a WindowsError - which doesn't seem to allow me to use in the except clause
                                    logging.debug('Sync Thing Not Found, run "Setup Workstation" to start using it.')
                            else:
                                self.load_syncthing = False
                                self.change_sync_icon(syncing=False)
                                logging.debug('sync_thing_auto_launch set to False, skipping launch')
                        except ModuleNotFoundError:
                            logging.info('problem launching syncthing - main.py line 800')
                    else:
                        self.load_syncthing = False
                        self.change_sync_icon(syncing=False)
                        USERCONFIG["sync_thing_auto_launch"] = False
                        USERCONFIG["sync_thing_machine_type"] = ""
                        logging.debug('Syncthing Auto Launch setting not set in globals.  Skipping sync operations')

            except KeyError:
                logging.debug('Skipping, Syncthing Not Set up')

    def set_processing_method_text(self, method=USERCONFIG['methodology']):
        self.current_processing_method.setTitle('Processing Method: %s' % method.title())

    def change_processing_method(self):
        if 'Local' in self.sender().text():
            logging.debug('Changing to Local')
            method = 'Local'
        elif 'Smedge' in self.sender().text():
            logging.debug('Changing to Smedge')
            method = "Smedge"
        elif 'Deadline' in self.sender().text():
            logging.debug('Changing to Deadline')
            method = "Deadline"
        else:
            return
        USERCONFIG['methodology'] = method.lower()
        save_json(user_config(), USERCONFIG)
        self.set_processing_method_text(method)

    def change_sync_icon(self, syncing=True):
        # ss = QtCore.QString("QMenu { background: black; color: red }")
        # TODO - can i change menu title color?
        # TODO - can i add an icon to the menu instead of a title?
        # self.sync_menu.setStyleSheet(ss)
        sync_button = self.centralWidget().nav_widget.sync_button
        if syncing:
            logging.debug('setting sync icon to sync_on')
            sync_icon = os.path.join(cglpath.icon_path(), 'sync_on24px.png')
            logging.debug(sync_icon)
        else:
            logging.debug('setting sync icon to sync_off')
            sync_icon = os.path.join(cglpath.icon_path(), 'sync_off24px.png')
            logging.debug(sync_icon)
        sync_button.setIcon(QtGui.QIcon(sync_icon))
        sync_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))

    def on_kill_syncthing(self):
        self.change_sync_icon(syncing=False)
        logging.debug('Killing Sync Thing')
        st_utils.kill_syncthing()

    def on_launch_syncthing(self):
        self.change_sync_icon(syncing=True)
        logging.debug('Starting Sync Thing')
        st_utils.launch_syncthing()

    def enable_server_connection_clicked(self):
        """
        connects an artist's machine to the server after the server has added them
        :return:
        """
        st_utils.process_st_config()
        self.change_sync_icon(syncing=True)
        pass

    def check_for_machines_clicked(self):
        st_utils.update_machines()
        self.change_sync_icon(syncing=True)
        pass

    def add_machines_to_folders_clicked(self):
        st_utils.update_machines()
        self.change_sync_icon(syncing=True)
        pass

    def manage_sharing_action_clicked(self):
        """
        opens a dialog where use chooses who they want to share with
        and which tasks they want to share.
        :return:
        """
        path_object = self.centralWidget().path_widget.path_object
        st_utils.share_files(path_object)

    def set_auto_launch_text(self):
        """
        reads syncthing_auto_launch setting from globals and sets text accordingly.
        :return:
        """
        if "sync_thing_auto_launch" in USERCONFIG.keys():
            if USERCONFIG["sync_thing_auto_launch"] == 'True':
                self.auto_launch_setting.setText('Auto-Launch: On')
            else:
                self.auto_launch_setting.setText('Auto-Launch: Off')

    def toggle_auto_launch(self):
        """
        Turns Auto-Launch of Lumberwatch/Syncthing on/off by toggling.
        :return:
        """
        if "sync_thing_auto_launch" in USERCONFIG.keys():
            if USERCONFIG["sync_thing_auto_launch"] == 'True':
                USERCONFIG["sync_thing_auto_launch"] = 'False'
                save_json(user_config(), USERCONFIG)
                logging.debug('Setting Auto Launch of LumberSync Off - Restart to see effects')
            else:
                USERCONFIG["sync_thing_auto_launch"] = 'True'
                save_json(user_config(), USERCONFIG)
                logging.debug('Setting Auto Launch of LumberSync On - Restart to see effects')
        self.set_auto_launch_text()

    @staticmethod
    def show_sync_details():
        """
        shows the syncthing web gui
        :return:
        """
        # st_utils.kill_syncthing()
        st_utils.show_browser()

    def set_up_st_server_clicked(self):
        """
        setups up server using client.json file from aws folder of the company's name, and a Google Sheets file that
        keeps track of all machines being used.
        :return:
        """
        st_utils.setup_server()
        self.change_sync_icon(syncing=True)

    def set_up_st_workstation_clicked(self):
        """
        Set up the local workstation to work with sync thing and register local workstation to the sheets file.
        :return:
        """
        st_utils.setup_workstation()
        self.change_sync_icon(syncing=True)

    def load_pipeline_designer_menus(self):
        import json
        #
        menus_json = os.path.join(CONFIG['paths']['cgl_tools'], 'lumbermill', 'menus.cgl')
        if os.path.exists(menus_json):
            with open(menus_json, 'r') as stream:
                self.pd_menus = json.load(stream)['lumbermill']
                software_menus = self.order_menus(self.pd_menus)
                if software_menus:
                    for menu in software_menus:
                        _menu = self.create_menu(menu)
                        self.menu_dict[menu] = _menu
                        buttons = self.order_buttons(menu)
                        self.add_menu_buttons(menu, buttons)
                else:
                    logging.debug('No Menus Found')
        else:
            logging.debug('No menu file found!')
        pass

    @staticmethod
    def order_menus(menus):
        """
        Orders the Menus from the json file correctly.  This is necessary for the menus to show up in the correct
        order within the interface.
        :return:
        """
        for menu in menus:
            menus[menu]['order'] = menus[menu].get('order', 10)
        if menus:
            return sorted(menus, key=lambda key: menus[key]['order'])

    def create_menu(self, menu):
        menu_object = self.menu_bar.addMenu(menu)
        return menu_object

    def add_menu_buttons(self, menu, buttons):
        for button in buttons:
            label = self.pd_menus[menu][button]['label']
            if 'icon' in self.pd_menus[menu][button].keys():
                icon_file = self.pd_menus[menu][button]['icon']
                if icon_file:
                    label = ''
            else:
                icon_file = ''

            if 'annotation' in self.pd_menus[menu][button].keys():
                annotation = self.pd_menus[menu][button]['annotation']
            else:
                annotation = ''
            self.add_button(menu, label=self.pd_menus[menu][button]['label'],
                            annotation=annotation,
                            command=self.pd_menus[menu][button]['module'],
                            icon=icon_file,
                            image_overlay_label=label)

    def add_button(self, menu, label='', annotation='', command='', icon='', image_overlay_label='', hot_key=''):
        module = command.split()[1]
        module_name = module.split('.')[-1]
        try:
            try:
                # Python 2.7
                loaded_module = __import__(module, globals(), locals(), module_name, -1)
            except ValueError:
                import importlib
                # Python 3.0
                loaded_module = importlib.import_module(module, module_name)
            action = QtWidgets.QAction(label, self)
            self.menu_dict[menu].addAction(action)
            function = getattr(loaded_module, 'run')
            action.triggered.connect(lambda: function(self.centralWidget()))
        except ImportError:
            pass
        pass

    def order_buttons(self, menu):
        """
        orders the buttons correctly within a menu.
        :param menu:
        :return:
        """
        buttons = self.pd_menus[menu]
        buttons.pop('order')
        try:
            # there is something weird about this - as soon as these are removed "shelves" never reinitializes
            buttons.pop('active')
        except KeyError:
            pass
        for button in buttons:
            if button:
                buttons[button]['order'] = buttons[button].get('order', 10)
        if buttons:
            return sorted(buttons, key=lambda key: buttons[key]['order'])
        else:
            return {}

    @staticmethod
    def time_tracking_clicked():
        from cgl.ui.widgets.dialog import TimeTracker
        dialog = TimeTracker()
        dialog.exec_()
        logging.debug('time tracking clicked')

    def update_lumbermill_clicked(self):
        process_method(self.centralWidget().progress_bar, self.do_update_check,
                       args=(self, self.centralWidget().progress_bar, True, True), text='Checking For Updates')

    @staticmethod
    def do_update_check(widget, progress_bar, show_confirmation=False, print_output=True):
        if not check_for_latest_master(print_output=print_output):
            # progress_bar.hide()
            # dialog = InputDialog(title='Update Lumbermill',
            #                      message='There is a new version of Lumbermill Available, would you like to update?',
            #                      buttons=['Cancel', 'Update'])
            # dialog.exec_()
            # if dialog.button == 'Update':
            print('updating master, not!')
        else:
            # progress_bar.hide()
            if show_confirmation:
                dialog = InputDialog(title='Up to date', message='Lumbermill is up to date!')
                dialog.exec_()
                if dialog.button == 'Ok' or dialog.button == 'Cancel':
                    dialog.accept()

    def report_bug_clicked(self):
        dialog = ReportBugDialog(self)
        dialog.exec_()

    def feature_request_clicked(self):
        dialog = RequestFeatureDialog(self)
        dialog.exec_()

    def open_create_project_dialog(self):
        from cgl.ui.widgets.dialog import ProjectCreator
        dialog = ProjectCreator(self)
        dialog.exec_()

    def on_proj_man_menu_clicked(self):
        link = CONFIG['project_management'][self.project_management]['api']['server_url']
        cglpath.start_url(link)

    @staticmethod
    def check_configs():
        return False

    @staticmethod
    def open_company_globals():
        logging.debug(os.path.dirname(CONFIG['paths']['globals']))
        cglpath.start(os.path.dirname(CONFIG['paths']['globals']))

    @staticmethod
    def open_user_globals():
        logging.debug(os.path.dirname(user_config()))
        cglpath.start(os.path.dirname(user_config()))

    def load_user_config(self):
        user_config = UserConfig()
        if 'd' in user_config.__dict__:
            config = user_config.d
            self.user_name = str(config['user_info']['local'])
            self.user_email = str(config['user_info'][self.project_management]['login'])
            self.company = str(config['company'])
            try:
                self.previous_path = str(config['previous_path'])
            except KeyError:
                self.previous_path = '%s%s/source' % (CONFIG['paths']['root'], self.company)
            if self.user_name in self.previous_path:
                self.filter = 'My Assignments'
            elif 'publish' in self.previous_path:
                self.filter = 'Publishes'
            else:
                self.filter = 'Everything'

    def on_login_clicked(self):
        dialog = LoginDialog(parent=self)
        dialog.exec_()

    @staticmethod
    def on_settings_clicked():
        logging.debug('settings clicked')

    def on_designer_clicked(self):
        pm = CONFIG['account_info']['project_management']
        def_schema = CONFIG['project_management'][pm]['api']['default_schema']
        schema = CONFIG['project_management'][pm]['tasks'][def_schema]
        from cgl.apps.pipeline.designer import Designer
        dialog = Designer(self, pm_tasks=schema)
        dialog.setMinimumWidth(1200)
        dialog.setMinimumHeight(500)
        dialog.exec_()

    def on_menu_designer_clicked(self):
        self.on_designer_clicked()

    def closeEvent(self, event):
        # set the current path so that it works on the load better.
        user_config = UserConfig(current_path=self.centralWidget().path_widget.text)
        user_config.update_all()