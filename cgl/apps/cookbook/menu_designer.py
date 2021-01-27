from cgl.apps.cookbook.designer import Designer


class MenuDesigner(Designer):

    def __init__(self, parent=None, type_='menus', pm_tasks=None):
        Designer.__init__(self, parent, type_=type_, pm_tasks=pm_tasks)


if __name__ == "__main__":
    from cgl.ui.startup import do_gui_init
    from cgl.core.utils.general import load_style_sheet
    app = do_gui_init()
    mw = MenuDesigner()
    mw.setWindowTitle('Menu Designer')
    mw.setMinimumWidth(1200)
    mw.setMinimumHeight(500)
    mw.show()
    mw.raise_()
    style_sheet = load_style_sheet()
    app.setStyleSheet(style_sheet)
    app.exec_()
