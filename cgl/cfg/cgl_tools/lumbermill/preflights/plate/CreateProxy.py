from plugins.preflight.preflight_check import PreflightCheck
from cgl.core.convert import create_proxy


class CreateProxy(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        # get the sequence to be converted
        self.shared_data['proxy'] = create_proxy(self.shared_data['published_seq'])
        self.pass_check('Finished Creating Proxies')
        # self.fail_check('Check Failed')
