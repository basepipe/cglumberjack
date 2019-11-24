from plugins.preflight.preflight_check import PreflightCheck
from cgl.core.convert import create_proxy
from cgl.core.config import UserConfig

METHODOLOGY = UserConfig().d['methodology']

class createProxy(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        print self.shared_data['publish_file'], 'create proxy publish file'
        self.shared_data['proxy'] = create_proxy(self.shared_data['publish_file'], methodology=METHODOLOGY)
        self.pass_check('Check Passed: Full Res Proxy Created!')
        # self.fail_check('Check Failed')

