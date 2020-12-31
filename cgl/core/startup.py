import logging
import os
import time
import signal
from os.path import dirname, join
from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.ui.util import UISettings


class ThemeFileWatcher(QtCore.QFileSystemWatcher):
    def __init__(self, theme_file):
        self.theme_file = theme_file
        QtCore.QFileSystemWatcher.__init__(self, [theme_file])
        self.fileChanged.connect(self.reread_theme)

    def reread_theme(self):
        logging.info("Theme file changed reloading")

        time.sleep(0.5)
        _read_theme_file(self.theme_file)
        if not self.files():
            # PYCHARM will remove the file and replace it, so we need to put it back
            self.addPath(self.theme_file)


def _do_qt_init():
    """
    set up the QT app
    Returns: QtGui.Application

    """
    app = QtWidgets.QApplication([])
    return app


# # noinspection PyUnresolvedReferences
# def _load_resources():
#     """
#     load the resource file
#
#     Returns:
#
#     """
#     # noinspection PyUnresolvedReferences
#     if Qt.__binding__ in ["PySide", "PySide2"]:
#         import ui.PySide_rc


# noinspection SpellCheckingInspection
def _load_ui_themes(gui=None):
    """
    load the ui theme from the css

    Returns:

    """

    theme = ":theme.css"
    # look for development files
    theme_env = "LUMBERJACK_THEME_DEV"
    if theme_env in os.environ and os.environ[theme_env] == "1":
        logging.debug("THEME DEV MODE")
        rsc_dir = join(dirname(dirname(dirname(__file__))), "resources")
        if os.path.isdir(rsc_dir):
            theme = join(rsc_dir, "theme.css")
            app = QtWidgets.QApplication.instance()
            # need to stash this some where so it doesnt get GCC'd
            app.theme_watcher = ThemeFileWatcher(theme)

        else:
            logging.warning("Cant find the development files for resources at %s", rsc_dir)
            logging.warning("FALLING BACK")

    logging.debug("Using theme %s", theme)
    _read_theme_file(theme, gui)


def _read_theme_file(theme, gui=None):
    logging.debug("theme: %s", theme)
    css_f = QtCore.QFile(theme)
    css_f.open(QtCore.QIODevice.ReadOnly)
    theme_data = ""
    in_ = QtCore.QTextStream(css_f)
    theme_dev = False
    if ":" not in theme:
        # theme dev mode, fix the file
        theme_dev = True
        logging.info("in theme dev mode")
    while not in_.atEnd():
        line = in_.readLine()  # A QByteArray
        if theme_dev:
            rsc_dir = join(dirname(dirname(dirname(__file__))), "resources")
            line = line.replace("url(:", "url(%s/" % rsc_dir)
        theme_data += line
    css_f.close()

    app = QtWidgets.QApplication.instance()
    logging.info('setting theme: %s' % gui)
    if gui:
        gui.setStyleSheet(theme_data)
    else:
        app.setStyleSheet(theme_data)


def do_freeze_fix():
    import sys
    if getattr(sys, 'frozen', False) and sys.platform == "darwin":
        os.environ["QT_PLUGIN_PATH"] = "."
        QtWidgets.QApplication.setLibraryPaths([os.path.dirname(sys.executable)+"/plugins",
                                                os.path.dirname(sys.executable)])
        # logging.debug(QtWidgets.QApplication.libraryPaths())


def _load_ui_settings():
    UISettings.settings()


def _load_lang():
    locale = QtCore.QLocale()
    full_locale = locale.bcp47Name()
    if "LUMBERJACK_LOCALE" in os.environ:
        full_locale = os.environ["LUMBERJACK_LOCALE"]
        logging.info("LOCAL OVERRIDE %s" % full_locale)
    if "-" in full_locale:
        lang, _ = full_locale.split("-")
    else:
        lang = full_locale
    if lang == "en":  # we write in english by default, maybe one day we will deal with British/US english
        logging.info("English language")
        return
    region_lang = ":i18n/%s.qm" % full_locale
    lang_lang = ":i18n/%s.qm" % lang
    lang_file = QtCore.QFile(region_lang)
    if not lang_file.exists():
        logging.debug("language %s does not exist" % region_lang)
        lang_file.close()
        lang_file = QtCore.QFile(lang_lang)
        if not lang_file.exists():
            logging.info("language %s does not exist" % lang_lang)
            lang_file.close()
            logging.debug("falling back to english")
            return
    logging.debug("found lang file %s " % lang_file.fileName())
    app = QtWidgets.QApplication.instance()
    trans = QtCore.QTranslator(app)
    trans.load(lang_file.fileName())
    app = QtWidgets.QApplication.instance()
    app.installTranslator(trans)


def do_gui_init():
    # do_app_init()
    do_freeze_fix()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = _do_qt_init()
    _load_resources()
    _load_ui_themes()
    _load_ui_settings()
    _load_lang()
    return app


def do_maya_gui_init(gui):
    _load_ui_themes(gui)
    _load_ui_settings()


def do_nuke_gui_init(gui):
    _load_ui_themes(gui)
    _load_ui_settings()


def load_style_sheet():
    root_ = __file__.split('cglumberjack')[0]
    style_file = os.path.join(root_, 'cglumberjack', 'resources', 'stylesheet.css')
    f = open(style_file, 'r')
    data = f.read()
    data.strip('\n')
    return data


def user_init():
    """
    Initializes needed User information
    :return:
    """
    from cgl.core.config.config import ProjectConfig
    from cgl.core.utils.general import current_user
    from cgl.ui.widgets.dialog import LoginDialog
    current = current_user().lower()
    logging.debug(current)
    cfg = ProjectConfig()
    CONFIG = cfg.project_config
    proj_man = CONFIG['account_info']['project_management']
    logging.debug(proj_man)
    users = CONFIG['project_management'][proj_man]['users']
    logging.debug(users)
    if users:
        logging.debug(1)
        if current in users.keys():
            logging.debug('Found user: %s in company globals' % current)
            return proj_man, users[current]
        else:
            dialog = LoginDialog()
            dialog.exec_()
            if dialog.button == 'Ok':
                return proj_man, dialog.user_info
    else:
        logging.debug('ERROR: %s not found in company globals file' % current)
        dialog = LoginDialog()
        dialog.exec_()
        if dialog.button == 'Ok':
            return proj_man, dialog.user_info
        return False


def check_time_log(project_management):
    if project_management == 'ftrack':
        import plugins.project_management.ftrack.util as ftrack_util
        logging.debug('Checking Ftrack Time Log')
        if ftrack_util.check_for_timelog():
            return True
        else:
            return False


def app_init(splash_image='lubmermill.jpg', cfg=None):
    app_ = QtWidgets.QApplication([])
    if not cfg:
        from cgl.core.config.config import ProjectConfig
        cfg = ProjectConfig()
    image_path = cfg.images_folder
    print(image_path)
    print(splash_image)
    image_path = os.path.join(image_path, splash_image)
    print(image_path)
    splash_pix = QtGui.QPixmap(image_path)
    splash_ = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash_.setMask(splash_pix.mask())
    splash_.show()
    app_.setStyleSheet(load_style_sheet())
    return app_, splash_


