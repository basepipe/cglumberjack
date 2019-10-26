import logging
import os
import time
import signal
from os.path import dirname, join
from Qt import QtWidgets, QtCore
import Qt
from cglcore.startup import do_app_init
from cglui.util import UISettings


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
    Returns: QtWidgets.Application

    """
    app = QtWidgets.QApplication([])
    return app


# noinspection PyUnresolvedReferences
def _load_resources():
    """
    load the resource file

    Returns:

    """
    # noinspection PyUnresolvedReferences
    if Qt.__binding__ in ["PySide", "PySide2"]:
        import cglui.testytest


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
        # print QtWidgets.QApplication.libraryPaths()


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
    print 1
    do_app_init()
    print 2
    do_freeze_fix()
    print 3
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    print 4
    app = _do_qt_init()
    print 5
    _load_resources()
    print 6
    _load_ui_themes()
    print 7
    _load_ui_settings()
    print 8
    _load_lang()
    print 9
    return app


def do_maya_gui_init(gui):
    _load_ui_themes(gui)
    _load_ui_settings()


def do_nuke_gui_init(gui):
    _load_ui_themes(gui)
    _load_ui_settings()
