import logging
from cgl.ui.widgets.dialog import InputDialog


class PreflightCheck(object):
    shared_data = {}

    def __init__(self, parent=None):
        self.parent = parent
        self.status = False
        self.items = []

    def fail_check(self, feedback):
        self.status = False
        dialog = InputDialog(title='Check Failed', message=feedback)
        dialog.exec_()


    def pass_check(self, feedback):
        print(feedback)
        self.status = True

    def getName(self):
        raise NotImplementedError

    def init(self):
        self.setWindowTitle(self.getName())
        try:
            self.run()
        except Exception, error:
            logging.error(error, exc_info=True)
            self.send_feedback("SOMETHING WENT WRONG:")
            self.parent().checkError(error)

    def run(self):
        pass

    @staticmethod
    def final_check():
        message = 'Publish Successful - you can close this window'
        dialog = InputDialog(title='Publish Successful', message=message, buttons=['Ok'])
        dialog.exec_()

