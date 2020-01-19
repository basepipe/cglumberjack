import os
from PySide import QtCore, QtGui
from datetime import datetime


class ScreenCapture(QtGui.QDialog):

    def __init__(self, parent=None):
        """
        Constructor
        """
        super(ScreenCapture, self).__init__(parent)

        self.click_position = None
        file_name = datetime.now().strftime('screen_grab_%Y-%m-%d_at_%H.%M.%S.png')
        self.output_path = os.path.expanduser(r'~/Desktop/%s' % file_name).replace('\\', '/')
        self.rectangle = QtCore.QRect()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint |
                            QtCore.Qt.CustomizeWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.setMouseTracking(True)
        self.set_screen_area()

        desktop = QtGui.QApplication.instance().desktop()
        desktop.resized.connect(self.set_screen_area)
        desktop.screenCountChanged.connect(self.set_screen_area)

    @classmethod
    def grab_window(cls):
        temp = ScreenCapture()
        temp.exec_()

    def get_rectangle(self):
        return self.rectangle

    def set_screen_area(self):
        desktop = QtGui.QApplication.instance().desktop()
        total_desktop = QtCore.QRect()
        for r in range(desktop.screenCount()):
            total_desktop = total_desktop.united(desktop.screenGeometry(r))
        self.setGeometry(total_desktop)

    def mousePressEvent(self, event):
        self.click_position = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.rectangle = QtCore.QRect(self.click_position, event.globalPos()).normalized()
        self.click_position = None
        pix = capture_area(self.rectangle, self.output_path)
        self.close()
        return pix

    def mouseMoveEvent(self, event):
        # repaints while moving the mouse
        self.repaint()

    def paintEvent(self, event):
        mouse_pos = self.mapFromGlobal(QtGui.QCursor.pos())
        click_pos = None
        if self.click_position is not None:
            click_pos = self.mapFromGlobal(self.click_position)

        qp = QtGui.QPainter(self)
        # initialize the crosshairs
        qp.setBrush(QtGui.QColor(0, 0, 0, 1))
        qp.setPen(QtCore.Qt.NoPen)
        qp.drawRect(event.rect())

        # Clear the capture area

        if click_pos is not None:
            self.rectangle = QtCore.QRect(click_pos, mouse_pos)
            qp.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
            qp.drawRect(self.rectangle)
            qp.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)

        pen = QtGui.QPen(QtGui.QColor('white'), 3, QtCore.Qt.SolidLine)
        qp.setPen(pen)
        # Draw cropping markers at click position
        if click_pos is not None:
            # left line
            qp.drawLine(mouse_pos.x(), click_pos.y(), mouse_pos.x(), mouse_pos.y())
            # top line
            qp.drawLine(click_pos.x(), click_pos.y(), mouse_pos.x(), click_pos.y())
            # right line
            qp.drawLine(click_pos.x(), click_pos.y(), click_pos.x(), mouse_pos.y())
            # bottom line
            qp.drawLine(click_pos.x(), mouse_pos.y(), mouse_pos.x(), mouse_pos.y())


def capture_area(rect, output_path):
    desktop = QtGui.QApplication.instance().desktop()
    print desktop.winId()
    pixmap = QtGui.QPixmap.grabWindow(desktop.winId(), rect.x()+2, rect.y()+2, rect.width()-4, rect.height()-4)
    pixmap.save(output_path)
    return output_path


def run():
    temp = ScreenCapture()
    temp.exec_()
    return temp.output_path
