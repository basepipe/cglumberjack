import Queue
import os
from cgl.plugins.Qt import QtCore, QtGui, QtWidgets


class ImageLoadThread(QtCore.QThread):
    queue = Queue.Queue()
    image_cache = {}
    loaded_signal = QtCore.Signal(str)

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.running = True

    def run(self):
        print 'RUNNING THREAD'
        while self.running:
            try:
                image = ImageLoadThread.queue.get(True, 0.5)

                if not self.running:
                    return

                if image:
                    if os.path.exists(image):
                        print 'found image %s' % image
                        ImageLoadThread.LoadToCache(image)
                        self.loaded_signal.emit(image)
                    else:
                        print 'image %s does not exist' % image
                if not self.running:
                    return
            except Queue.Empty:
                pass

    def end_thread(self):
        self.running = False

    @classmethod
    def addQueue(cls, image):
        cls.queue.put(image)

    @staticmethod
    def return_id(path):
        return str(path.split('/')[-1].split('.')[0])

    @classmethod
    def LoadToCache(cls, path):
        img_id = cls.return_id(path)
        img_obj = cls.paintImg(path)
        cls.image_cache[img_id] = img_obj

    @classmethod
    def getImageFromCache(cls, path):
        img_id = cls.return_id(path)
        if img_id in cls.image_cache:
            return cls.image_cache[img_id]
        else:
            print 'Adding to Queue %s' % path
            return cls.addQueue(path)

    @classmethod
    def paintImg(cls, path):
        template = QtGui.QImage(128, 128, QtGui.QImage.Format_ARGB32)
        template.fill(0)
        painter = QtGui.QPainter(template)
        image = QtGui.QImage(path).scaled(template.size().width(),
                                          template.size().height(),
                                          QtCore.Qt.KeepAspectRatio)
        xstart = (template.size().width() - image.size().width()) / 2
        ystart = (template.size().height() - image.size().height()) / 2
        painter.drawImage(xstart, ystart, image)
        # painter.setCompositionMode(QtGui.QPainter.CompositionMode_DestinationOver)
        painter.end()
        return template


