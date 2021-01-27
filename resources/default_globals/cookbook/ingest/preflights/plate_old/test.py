from plugins.preflight.preflight_check import PreflightCheck

class test(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        print 'test'
        # self.pass_check('Check Passed')
        # self.fail_check('Check Failed')

