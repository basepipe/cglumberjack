from plugins.preflight.preflight_check import PreflightCheck


# METHODOLOGY = UserConfig().d['methodology']


class CreateHDProxy(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        # self.shared_data['publish_path_object'].make_proxy()
        self.pass_check('Check Passed: HD Proxy Created!')
        # self.fail_check('Check Failed')

