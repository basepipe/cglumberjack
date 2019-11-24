from apps.pipeline.designer import Designer


class PreflightDesigner(Designer):

    def __init__(self, parent=None, type_='preflights', pm_tasks=None):
        Designer.__init__(self, parent, type_=type_, pm_tasks=pm_tasks)


if __name__ == "__main__":
    from cgl.ui.startup import do_gui_init
    from cgl.core.util import load_style_sheet
    app = do_gui_init()
    mw = PreflightDesigner()
    mw.setWindowTitle('Preflight Designer')
    mw.setMinimumWidth(1200)
    mw.setMinimumHeight(500)
    mw.show()
    mw.raise_()
    style_sheet = load_style_sheet()
    app.setStyleSheet(style_sheet)
    app.exec_()
