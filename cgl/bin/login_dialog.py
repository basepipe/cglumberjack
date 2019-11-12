import cgl.core.startup as startup


def load_login_dialog(app, splash):
    from cgl.ui.widgets.dialog import LoginDialog
    mw = LoginDialog()
    # mw = Designer(type_='menus')
    mw.setWindowTitle('New User Login')
    mw.setMinimumWidth(300)
    mw.setMinimumHeight(300)
    mw.show()
    mw.raise_()
    if splash:
        splash.finish(mw)
    app.exec_()


if __name__ == "__main__":
    app, splash = startup.app_init()
    project_management, user_info = startup.user_init()
    load_login_dialog(app, splash)