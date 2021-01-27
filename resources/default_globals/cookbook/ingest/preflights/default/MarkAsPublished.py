from plugins.preflight.preflight_check import PreflightCheck


class MarkAsPublished(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        print 'MarkAsPublished'
        # self.pass_check('Check Passed')
        # self.fail_check('Check Failed')

