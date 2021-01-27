from cgl.plugins.preflight.preflight_check import PreflightCheck
import os
import cgl.plugins.maya.tasks.bndl as bndl
import cgl.plugins.maya.utils as utils
import cgl.plugins.maya.lumbermill as lm
import pymel.core as pm


class FixReferencedBundles(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        """
        script to be executed when the preflight is run.

        If the preflight is successful:
        self.pass_check('Message about a passed Check')

        if the preflight fails:
        self.fail_check('Message about a failed check')
        :return:
        """
        for ref in pm.listReferences(refNodes=True):
            if 'bndl' in (str(ref[-1])):
                object = lm.LumberObject(str(ref[-1]))
                try:
                    pm.select('{}*:bndl'.format(object.shot))
                    self.replace_selected_reference_with_bundle()
                    pm.FileReference(ref[-1]).remove()
                except:
                    self.fail_check('Something odd happened, check for false references')
        self.pass_check('Check Passed')
        # self.fail_check('Check Failed')

    def replace_selected_reference_with_bundle(self):
        old_bundle = pm.ls(sl=True)[0]
        ref_path = utils.get_selected_reference()[-1][-1]
        this = lm.LumberObject(str(ref_path)).copy(context='render', ext='json', set_proper_filename=True)
        if os.path.exists(this.path_root):
            new_bundle = bndl.bundle_import(this.path_root)

            self.super_copy_key(old_bundle, new_bundle, 'translateX')
            self.super_copy_key(old_bundle, new_bundle, 'translateY')
            self.super_copy_key(old_bundle, new_bundle, 'translateZ')
            self.super_copy_key(old_bundle, new_bundle, 'rotateX')
            self.super_copy_key(old_bundle, new_bundle, 'rotateY')
            self.super_copy_key(old_bundle, new_bundle, 'rotateZ')
            self.super_copy_key(old_bundle, new_bundle, 'scaleX')
            self.super_copy_key(old_bundle, new_bundle, 'scaleY')
            self.super_copy_key(old_bundle, new_bundle, 'scaleZ')


    @staticmethod
    def super_copy_key(from_object, to_object, attr):
        if pm.copyKey(from_object, attribute=attr, option='curve'):
            pm.pasteKey(to_object, attribute=attr)
        else:
            aa = pm.getAttr('{}.{}'.format(from_object, attr))
            pm.setAttr('{}.{}'.format(to_object, attr), aa)
