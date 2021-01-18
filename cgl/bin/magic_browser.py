import time
import logging
from cgl.core.config.config import ProjectConfig
zero_start_time = time.time()
import cgl.core.startup as startup
from cgl.apps.magic_browser.main import CGLumberjack
start_time = time.time()
logging.debug('Loaded initial modules in %s seconds: %s' % ((start_time - zero_start_time), __file__))


def load_lumbermill(app, splash=None, cfg=None):
    gui = CGLumberjack(show_import=False, user_info=user_info, start_time=start_time, cfg=cfg)
    gui.show()
    gui.raise_()
    if splash:
        splash.finish(gui)
    app.exec_()


if __name__ == "__main__":
    print('Lumbermill.py')
    cfg = ProjectConfig()
    print(cfg.project_config_file)
    app, splash = startup.app_init(cfg=cfg)
    project_management, user_info = startup.user_init(cfg=cfg)
    # TODO tell them to run the setup script if there's not globals file.
    # TODO make this value a globals value
    time_required = False
    if user_info:
        logging.debug('Found User, %s' % user_info['login'])
        if project_management == 'ftrack':
            if time_required:
                if startup.check_time_log(project_management):
                    load_lumbermill(app, splash, cfg)
                else:
                    from cgl.bin.time_sheet import load_time_sheet
                    load_time_sheet(app, splash)
            else:
                load_lumbermill(app, splash, cfg)
        else:
            load_lumbermill(app, splash, cfg)
    else:
        from cgl.bin.login_dialog import load_login_dialog
        load_login_dialog(app)

