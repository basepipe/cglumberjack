import os
from Qt import QtWidgets, QtCore, QtGui
import cglcore.path as cglpath


def load_style_sheet():
    root_ = __file__.split('src')[0]
    style_file = os.path.join(root_, 'resources', 'stylesheet.css')
    f = open(style_file, 'r')
    data = f.read()
    data.strip('\n')
    return data


def app_init():
    app_ = QtGui.QApplication([])
    splash_pix = QtGui.QPixmap(cglpath.image_path('lumbermill.jpg'))
    splash_ = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash_.setMask(splash_pix.mask())
    splash_.show()
    app_.setStyleSheet(load_style_sheet())
    return app_, splash_


if __name__ == "__main__":
    app, splash = app_init()
    from cglcore.config import app_config
    project_management = app_config()['account_info']['project_management']
    users = app_config()['project_management'][project_management]['users']
    time_log = True
    from cglcore.util import current_user
    if current_user() in users:
        print 'Loading user'
        user_info = users[current_user()]
        if user_info:
            print 'Found User, %s' % user_info['login']
            if project_management == 'ftrack':
                import plugins.project_management.ftrack.util as ftrack_util
                print 'Checking Ftrack Time Log'
                if ftrack_util.check_for_timelog():
                    time_log = True
                else:
                    time_log = False
            if time_log:
                import time
                start_time = time.time()
                print 'Loading Lumbermill'
                from apps.lumbermill.main import CGLumberjack
                QtWidgets.qApp.processEvents()
                gui = CGLumberjack(show_import=False, user_info=user_info, start_time=start_time)
                gui.show()
                gui.raise_()
                splash.finish(gui)
                app.exec_()
            else:
                print 'No Time Log Found - Enter Time for yesterday'
                from cglui.widgets.dialog import TimeTracker
                import datetime
                gui = TimeTracker()
                date = datetime.datetime.today()
                gui.set_date(datetime.datetime.today() - datetime.timedelta(days=1))
                gui.show()
                gui.raise_()
                app.exec_()
    else:
        from cglui.widgets.dialog import LoginDialog
        mw = LoginDialog()
        # mw = Designer(type_='menus')
        mw.setWindowTitle('New User Login')
        mw.setMinimumWidth(300)
        mw.setMinimumHeight(300)
        mw.show()
        mw.raise_()
        app.exec_()
