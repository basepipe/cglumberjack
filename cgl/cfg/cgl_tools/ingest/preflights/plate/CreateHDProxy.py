from plugins.preflight.preflight_check import PreflightCheck
from cgl.core.convert import create_hd_proxy
from cgl.core.config import UserConfig


METHODOLOGY = UserConfig().d['methodology']


class CreateHDProxy(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        print 'Converting HD Proxy %s' % METHODOLOGY
        self.shared_data['hdProxy'] = create_hd_proxy(self.shared_data['proxy']['file_out'],
                                                      methodology=METHODOLOGY,
                                                      dependent_job=self.shared_data['proxy']['job_id'])
        self.pass_check('Check Passed: HD Proxy Created!')
        # self.fail_check('Check Failed')

