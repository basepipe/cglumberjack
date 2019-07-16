import sys
from Qt import QtCore, QtWidgets, QtGui
import threading


class ProgressDialog(QtWidgets.QDialog):

    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle("Gif Testerino")

        self.message = QtWidgets.QLabel('Working...')
        self.movie_screen = QtWidgets.QLabel()

        self.movie = QtGui.QMovie('chopping_wood.gif')
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
