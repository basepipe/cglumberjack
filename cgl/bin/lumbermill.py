import time
zero_start_time = time.time()
import cgl.core.startup as startup
from apps.lumbermill.main import CGLumberjack
start_time = time.time()
print 'Loaded initial modules in %s seconds: %s' % ((start_time - zero_start_time), __file__)


def load_lumbermill(app, splash=None):
    gui = CGLumberjack(show_import=False, user_info=user_info, start_time=start_time)
    gui.show()
    gui.raise_()
    if splash:
        splash.finish(gui)
    app.exec_()



if __name__ == "__main__":
    app, splash = startup.app_init()
    project_management, user_info = startup.user_init()
    time_required = True
    if user_info:
        print 'Found User, %s' % user_info['login']
        if project_management == 'ftrack':
            if time_required:
                if startup.check_time_log(project_management):
                    load_lumbermill(app, splash)
                else:
                    from cgl.bin.time_sheet import load_time_sheet
                    load_time_sheet(app, splash)
            else:
                load_lumbermill(app, splash)
        else:
            load_lumbermill(app, splash)
    else:
        from cgl.bin.login_dialog import load_login_dialog
        load_login_dialog(app)

