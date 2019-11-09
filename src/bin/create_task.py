import core.startup


def load_task_creator(app_, splash_):
    from src.ui.widgets.help import RequestFeatureDialog
    gui = RequestFeatureDialog()
    gui.setWindowTitle('Task Creator')
    gui.setMinimumWidth(900)
    gui.show()
    gui.raise_()
    if splash_:
        splash_.finish(gui)
    app_.exec_()


if __name__ == "__main__":
    app, splash = core.startup.app_init()
    load_task_creator(app, splash)





