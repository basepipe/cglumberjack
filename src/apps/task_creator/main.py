import os
from Qt import QtGui
from cglui.widgets.help import RequestFeatureDialog
import cglcore.path as cglpath


if __name__ == "__main__":
    app = QtGui.QApplication([])
    mw = RequestFeatureDialog()
    mw.setWindowTitle('Task Creator')
    mw.setMinimumWidth(900)
    # mw.setMinimumHeight(300)
    mw.show()
    mw.raise_()
    root_ = __file__.split('src')[0]
    location = os.path.join(root_, 'resources', 'stylesheet.css')
    style_sheet = cglpath.load_style_sheet(style_file=location)
    app.setStyleSheet(style_sheet)
    app.exec_()

    # TODO - Select CG Lumberjack as the default workgroup
    # TODO - select General Development as the project
    # TODO  - Add "Tags" Button (i really want to create a tags widget for lumbermill!)
    # TODO - Add "Assignment" button (would be cool to have a dropdown like they do on Asana)
    #


