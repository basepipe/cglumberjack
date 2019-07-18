import sys
from Qt import QtCore, QtWidgets, QtGui
import logging
from cglcore.path import image_path
import threading


class ProgressDialog(QtWidgets.QDialog):

    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle("Gif Testerino")

        self.message = QtWidgets.QLabel('Working...')
        self.movie_screen = QtWidgets.QLabel()

        self.movie = QtGui.QMovie(image_path('chopping_wood.gif'))
        logging.info(self.movie.isValid())
        self.movie.start()

        self.movie_screen.setMovie(self.movie)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.message)
        layout.addWidget(self.movie_screen)
        self.setLayout(layout)


if __name__ == '__main__':
    app = QtGui.QApplication([])
    form = ProgressDialog()
    form.show()
    app.exec_()
