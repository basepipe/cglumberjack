from cgl.plugins.preflight.preflight_check import PreflightCheck


class ThisButtonRules(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        print('ThisButtonRules')
        # self.pass_check('Check Passed')
        # self.fail_check('Check Failed')

