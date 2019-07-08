import glob
import os
from plugins.preflight.preflight_check import PreflightCheck
from cglcore.path import PathObject, lj_list_dir
from cglcore.convert import create_mov_hd_proxy


class CreateProxyMov(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        # get the sequence to be converted
        frange = self.shared_data['frange']
        sframe, eframe = frange.split('-')
        create_mov_hd_proxy(self.shared_data['hdProxy'], start_frame=sframe)
        self.pass_check('Movie Created!')
        
        

