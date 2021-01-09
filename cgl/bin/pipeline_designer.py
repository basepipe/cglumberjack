import cgl.core.startup as startup


def load_pipeline_designer(app_, splash_):
    from cgl.apps.pipeline.designer import Designer
    mw = Designer(type_='pre_publish')
    if mw:
        # mw = Designer(type_='menus')
        mw.setWindowTitle('Preflight Designer')
        mw.setMinimumWidth(1200)
        mw.setMinimumHeight(500)
        mw.show()
        mw.raise_()
        app_.exec_()
    if splash_:
        splash_.finish(mw)


if __name__ == "__main__":
    app, splash = startup.app_init()
    project_management, user_info = startup.user_init()
    load_pipeline_designer(app, splash)