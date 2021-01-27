from cgl.plugins.preflight.preflight_check import PreflightCheck
import pymel.core as pm
import cgl.plugins.maya.utils as utils
import cgl.plugins.maya.tasks.bndl as task_bndl
reload(task_bndl)


class OrganizeLayoutAssets(PreflightCheck):

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
        anim_children = pm.listRelatives('ANIM', children=True)
        refs = pm.listReferences(refNodes=True)
        layout_refs = []
        bundle_children = task_bndl.get_bundle_children()

        for r in refs:
            node = utils.select_reference(r[-1])
            if node not in anim_children and node not in bundle_children:
                layout_refs.append(node)

        pm.select(d=True)
        if layout_refs:
            if not pm.objExists('LAYOUT'):
                pm.group(name='LAYOUT')
            for lr in layout_refs:
                pm.parent(lr, 'LAYOUT')
            self.pass_check('Layout Assets Organized')
        else:
            self.pass_check('No Layout Assets to Organize')
