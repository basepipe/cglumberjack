from Qt import QtCore

BACKGROUND_THREADS = []
THREAD_MANAGER = None


class BackGroundResult(object):
    def __init__(self, data):
        self.data = data


class BackgroundThread(QtCore.QThread):
    result_complete = QtCore.Signal(object)
    delete_able = QtCore.Signal(object)

    def __init__(self, p, *args, **kwargs):
        QtCore.QThread.__init__(self)
        self.process = p
        self.args = args
        self.kwargs = kwargs
        BACKGROUND_THREADS.append(self)  # protect against the GC
        self.finished.connect(self.cleanup)

    def cleanup(self):
        BACKGROUND_THREADS.remove(self)  # im done I can die now
        self.deleteLater()

    def run(self):
        data = self.process(*self.args, **self.kwargs)
        self.result_complete.emit(BackGroundResult(data))


def process(notify, method, *args, **kwargs):
    bg = BackgroundThread(method, *args, **kwargs)
    if notify:
        bg.result_complete.connect(notify)
    bg.start()


