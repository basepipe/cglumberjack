from Qt.QtGui import QColor, QPalette



def set_color(widget, color=[]):
    print color
    palette = QPalette()
    if color:
        palette.setColor(widget.foregroundRole(), QColor(color[0], color[1], color[2]))
    else:
        palette.setColor(widget.foregroundRole(), QColor(255, 0, 0))
    widget.setPalette(palette)
