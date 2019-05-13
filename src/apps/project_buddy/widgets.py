from Qt import QtWidgets, QtCore, QtGui
from cglui.widgets.base import LJMainWindow


class LJButton(QtWidgets.QAbstractButton):
    def __init__(self, pixmap, pixmap_hover=None, pixmap_pressed=None, parent=None):
        super(LJButton, self).__init__(parent)
        self.pixmap = pixmap
        self.pixmap_hover = pixmap_hover if pixmap_hover else pixmap
        self.pixmap_pressed = pixmap_pressed if pixmap_pressed else pixmap
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        self.pressed.connect(self.update)
        self.released.connect(self.update)

    def paintEvent(self, event):
        pix = self.pixmap_hover if self.underMouse() else self.pixmap
        color = QtCore.Qt.black
        if self.isDown():
            color = QtCore.Qt.blue
            pix = self.pixmap_pressed

        painter = QtGui.QPainter(self)
        painter.drawPixmap(event.rect(), pix)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(color, 4))
        painter.drawRoundedRect(0, 0, 128, 128, 16, 16)

    def enterEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self.update()

    def sizeHint(self):
        return QtCore.QSize(128, 128)


class LJImageButton(QtWidgets.QWidget):
    def __init__(self, main_image, hover_image=None, pressed_image=None, label_text='', width=128, parent=None):
        super(LJImageButton, self).__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        self.image_button = LJButton(pixmap=main_image, pixmap_hover=hover_image, pixmap_pressed=pressed_image)
        self.label = QtWidgets.QLabel('<h3>%s</h3>' % label_text.title())
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.xsize = width

        layout.addWidget(self.image_button)
        layout.addWidget(self.label)

        self.setFixedHeight(180)
        self.setFixedWidth(148)

    def hide_label(self):
        self.label.hide()

    def show_label(self):
        self.label.show()

    def sizeHint(self):
            return QtCore.QSize(self.xsize, self.xsize+30)


class SearchPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        pass


class PathPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        pass


class GUITEst(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        layout = QtWidgets.QVBoxLayout()
        image = r'C:\Users\tmiko\Creative Cloud Files\cgl_logos\logo_c_dark@.5x.png'
        image2 = r'C:\Users\tmiko\Creative Cloud Files\cgl_logos\logo_a_light@.5x.png'
        pixmap = QtGui.QPixmap(image)
        pixmap2 = QtGui.QPixmap(image2)
        pixmap_hover = QtGui.QPixmap(pixmap2)
        pixmap_pressed = QtGui.QPixmap(image)
        test_button = LJImageButton(main_image=pixmap, hover_image=pixmap2, pressed_image=pixmap2, label_text='test button')
        test_button2 = LJImageButton(main_image=pixmap, hover_image=pixmap2, pressed_image=pixmap2, label_text='test button2')
        # button = QtWidgets.QPushButton('Button2')
        layout.addWidget(test_button)
        layout.addWidget(test_button2)
        #layout.addWidget(button)
        self.setLayout(layout)
        self.setStyleSheet('stylesheet.css')


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ex = GUITEst()
    ex.show()
    # setup stylesheet
    sys.exit(app.exec_())