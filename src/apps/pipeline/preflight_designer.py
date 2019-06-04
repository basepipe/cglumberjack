from apps.pipeline.designer import Designer


class PreflightDesigner(Designer):

    def __init__(self, parent=None, type_='preflights'):
        Designer.__init__(self, parent, type_=type_)


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    from cglcore.path import load_style_sheet
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
