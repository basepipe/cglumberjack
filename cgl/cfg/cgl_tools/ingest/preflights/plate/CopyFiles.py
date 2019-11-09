from plugins.preflight.preflight_check import PreflightCheck

class CopyFiles(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        print 'CopyFiles'
        # self.pass_check('Check Passed')
        # self.fail_check('Check Failed')

