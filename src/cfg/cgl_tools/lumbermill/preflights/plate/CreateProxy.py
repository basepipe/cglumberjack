import glob
import os
from plugins.preflight.preflight_check import PreflightCheck
from cglcore.path import PathObject, CreateProductionData
from cglcore.convert import create_proxy, create_proxy


class CreateProxy(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        # get the sequence to be converted
        print self.shared_data['published_seq']
        frange = self.shared_data['frange']
        sframe, eframe = frange.split('-')
        self.shared_data['proxy'] = create_proxy(self.shared_data['published_seq'], start_frame=sframe)
        self.pass_check('Finished Creating Proxies')
        # self.fail_check('Check Failed')