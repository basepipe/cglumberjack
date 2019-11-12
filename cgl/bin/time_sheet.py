import cgl.core.startup as startup


def load_time_sheet(app_, splash_=None):
    print 'No Time Log Found - Enter Time for yesterday'
    from cgl.ui.widgets.dialog import TimeTracker
    import datetime
    gui = TimeTracker()
    try:
        gui.set_date(datetime.datetime.today() - datetime.timedelta(days=1))
        gui.show()
        gui.raise_()
        if splash_:
            splash_.finish(gui)
        app_.exec_()
    except AttributeError:
        print 'The Time Tracker GUI could not load'


if __name__ == "__main__":
    app, splash = startup.app_init()
    project_management, user_info = startup.user_init()
    load_time_sheet(app, splash)
