from cgl.plugins.preflight.preflight_check import PreflightCheck
import pymel.core as pm
# there is typically a lumbermill.py, and utils.py file in the plugins directory.
# look here for pre-built, useful functions
# from cgl.plugins.SOFTWARE import lumbermill


class OrganizeAnim(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        if not pm.objExists('ANIM'):
            pm.select(d=True)
            pm.group(name='ANIM')

        if not pm.objExists('unreferenced_ANIM'):
            pm.select(d=True)
            pm.group(name='unreferenced_ANIM')

        refs = []
        layout_refs = []
        geo = {}
        sel = pm.ls(dag=True)
        bad = False
        bundles = pm.ls('*:bndl')
        for each in sel:
            if pm.keyframe(each, query=True):
                try:
                    top_group = pm.referenceQuery(each, nodes=True)[0]
                    # check if it's a bundle
                    try:
                        parent_ = each.listRelatives(parent=True)[0]
                        if parent_ in bundles:
                            top_group = parent_
                    except IndexError:
                        pass
                    if top_group not in refs:
                        refs.append(top_group)
                except RuntimeError:
                    try:
                        if not isinstance(each.getChildren()[0], pm.nodetypes.Camera):
                            # allows us to publish bndl files as animation
                            if not each.endswith('bndl'):
                                geo.update({str(each): ''})
                    except IndexError:
                        pass

        for r in refs:
            try:
                pm.parent(r, 'ANIM')
            except RuntimeError:
                message = "%s is a nested reference, i can't publish this the normal way" % r
                pm.windows.confirmDialog(title="Found Nested Reference", message=message, button=['Ok'])
                bad = True
                self.fail_check('Check Failed: Nested References have been found')

        for anim in geo:
            if not bad:
                self.pass_check('Check Passed: All Animation has been organized!')
            pm.parent(anim, 'unreferenced_ANIM')
        if not bad:
            self.pass_check('Check Passed: All Animation has been organized!')
        else:
            self.fail_check('Check Failed: Nested References have been found')

