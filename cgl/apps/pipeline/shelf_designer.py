from apps.pipeline.designer import Designer


class ShelfDesigner(Designer):

    def __init__(self, parent=None, type_='shelves'):
        Designer.__init__(self, parent, type_=type_)


if __name__ == "__main__":
    from cgl.ui.startup import do_gui_init
    from cgl.core.path import load_style_sheet

    app = do_gui_init()
    mw = ShelfDesigner()
    mw.setWindowTitle('Shelf Designer')
    mw.setMinimumWidth(1200)
    mw.setMinimumHeight(500)
    mw.show()
    mw.raise_()
    style_sheet = load_style_sheet()
    app.setStyleSheet(style_sheet)
    app.exec_()
