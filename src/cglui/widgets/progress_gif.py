import sys
from Qt import QtCore, QtWidgets, QtGui
import logging
from cglcore.path import image_path
import threading


class ProgressGif(QtWidgets.QWidget):

    def __init__(self, title='CG Lumberjacking...'):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QVBoxLayout(self)
        self.message = QtWidgets.QLabel(title)
        self.message.setProperty('class', 'ultra_title')
        self.message.setAlignment(QtCore.Qt.AlignCenter)
        self.progress_bar = QtWidgets.QLabel()
        self.progress_bar.setAlignment(QtCore.Qt.AlignCenter)
        self.movie = QtGui.QMovie(image_path('chopping_wood.gif'))
        self.progress_bar.setMovie(self.movie)
        layout.addWidget(self.message)
        layout.addWidget(self.progress_bar)

    def hide(self):
        self.message.hide()
        self.progress_bar.hide()

    def show(self):
        self.movie.start()
        self.message.show()
        self.progress_bar.show()


class ProgressDialog(QtWidgets.QDialog):

    def __init__(self, message, gif_name):
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle("Gif Testerino")

        self.message = QtWidgets.QLabel(message)
        self.movie_screen = QtWidgets.QLabel()

        self.movie = QtGui.QMovie(image_path(gif_name))
        logging.info(self.movie.isValid())
        self.movie.start()

        self.movie_screen.setMovie(self.movie)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.message)
        layout.addWidget(self.movie_screen)
        self.setLayout(layout)

    def update_gif(self):
        for i in range(60):
            QtWidgets.qApp.processEvents()


if __name__ == '__main__':
    app = QtGui.QApplication([])
    form = ProgressDialog()
    form.show()
    app.exec_()
