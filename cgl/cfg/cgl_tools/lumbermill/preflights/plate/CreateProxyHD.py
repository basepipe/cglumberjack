from cgl.plugins.preflight.preflight_check import PreflightCheck
from cgl.core.convert import create_hd_proxy


class CreateProxyHD(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        # get the sequence to be converted
        frange = self.shared_data['frange']
        sframe, eframe = frange.split('-')
        self.shared_data['hdProxy'] = create_hd_proxy(self.shared_data['proxy'], start_frame=sframe)
        self.pass_check('Finished Creating Proxies')
        # self.fail_check('Check Failed')

