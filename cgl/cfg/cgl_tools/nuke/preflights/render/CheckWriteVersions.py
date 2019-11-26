from plugins.preflight.preflight_check import PreflightCheck
import plugins.nuke.cgl_nuke as cgl_nuke
from cgl.ui.widgets.dialog import InputDialog


class CheckWriteVersions(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        if cgl_nuke.check_write_node_version():
            self.pass_check('Check Passed')
        else:
            dialog = InputDialog(title='Write Version does not match Scene Version',
                                 message='Would you like to render anyway?')
            dialog.exec_()
            if dialog.button == 'Ok':
                self.pass_check('Check Passed')
            else:
                print 'I made it here somehow'
                self.fail_check('Check Failed')

