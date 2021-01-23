from plugins.preflight.preflight_check import PreflightCheck


class ClosePreflight(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        print 'ClosePreflight'
        self.pass_check('Check Passed')
        # self.fail_check('Check Failed')
        print self.parent
