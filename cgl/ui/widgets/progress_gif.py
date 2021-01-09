from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
import logging
import threading
from cgl.core.config.config import ProjectConfig


class ProgressGif(QtWidgets.QWidget):

    def __init__(self, title='CG Lumberjacking...', height=150, cfg=None):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QVBoxLayout(self)
        self.gif_height = QtCore.QSize(height, height)
        if not cfg:
            print(ProgressGif)
            self.cfg = ProjectConfig()
        else:
            self.cfg = cfg
        self.message = QtWidgets.QLabel(title)
        self.message.setProperty('class', 'ultra_title')
        self.message.setAlignment(QtCore.Qt.AlignCenter)
        self.progress_bar = QtWidgets.QLabel()
        self.progress_bar.setAlignment(QtCore.Qt.AlignCenter)
        self.movie = QtGui.QMovie(self.cfg.image_path('chopping_wood.gif'))
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

    def __init__(self, message='Achieving Kickassity', gif_name='chopping_wood.gif', cfg=None):
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle("Hold My Beer")
        if not cfg:
            cfg = ProjectConfig()

        self.message = QtWidgets.QLabel(message)
        self.movie_screen = QtWidgets.QLabel()
        mov_path = cfg.image_path(gif_name)
        print(mov_path)
        self.movie = QtGui.QMovie(cfg.image_path(gif_name))
        logging.info(self.movie.isValid())
        self.movie.start()

        self.movie_screen.setMovie(self.movie)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.message)
        layout.addWidget(self.movie_screen)
        self.setLayout(layout)

    @staticmethod
    def update_gif():
        for i in range(60):
            QtGui.qApp.processEvents()


def process_method(progress_bar, target, args=(), text=None):
    orig_text = progress_bar.message.text()
    if text:
        progress_bar.message.setText(text)
    progress_bar.show()
    # QtGui.qApp.processEvents()
    p = threading.Thread(target=target, args=args)
    # QtGui.qApp.processEvents()
    p.start()
    return p


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    form = ProgressDialog()
    form.show()
    app.exec_()
