from cgl.plugins.preflight.preflight_check import PreflightCheck
import cgl.plugins.maya.tasks.bndl as bndl
import cgl.plugins.maya.tasks.anim as anim
import cgl.plugins.maya.tasks.mdl as mdl
import pymel.core as pm

class Fixbundleanim(PreflightCheck):

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
        # get bundles in scene
        bundles = bndl.get_bundles()
        # if they have animation create a proxy object (cube) that matches the bounding box.
        for b in bundles:
            if pm.keyframe(b, query=True):
                cube = mdl.create_bounding_box_cube(b)
                mdl.snap_to_origin(cube)
                mdl.freeze_transforms(cube)
                anim.copy_animation(b, cube)
                mdl.disconnect_attrs(b)
                pm.parentConstraint(cube, b)
                pm.parent(cube, 'ANIM')
                pm.hide(cube)
        self.pass_check('Bundle Animation has been removed, and anim proxies created')
