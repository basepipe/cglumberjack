from Qt import QtCore, QtWidgets, QtGui
import logging
from cglcore.path import image_path


class ProgressGif(QtWidgets.QWidget):

    def __init__(self, title='CG Lumberjacking...', height=150):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QVBoxLayout(self)
        self.gif_height = QtCore.QSize(height, height)

        self.message = QtWidgets.QLabel(title)
        self.message.setProperty('class', 'ultra_title')
        self.message.setAlignment(QtCore.Qt.AlignCenter)
        self.progress_bar = QtWidgets.QLabel()
        self.progress_bar.setAlignment(QtCore.Qt.AlignCenter)
        self.movie = QtGui.QMovie(image_path('chopping_wood.gif'))
        self.movie.setScaledSize(self.gif_height)
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
        logging.info(self.movie.scaledSize())


class ProgressDialog(QtWidgets.QDialog):

    def __init__(self, message, gif_name):
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle("Gif Tester")

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
    form = ProgressDialog(message='test', gif_name='')
    form.show()
    app.exec_()
