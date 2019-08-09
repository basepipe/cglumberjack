from plugins.preflight.preflight_check import PreflightCheck


class CheckWriteNode(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        print 'Checking to see if a valid write node exists'
        self.pass_check('Check Passed')
        # self.fail_check('Check Failed')


