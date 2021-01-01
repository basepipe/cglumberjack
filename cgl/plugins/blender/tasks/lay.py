import os
import glob
from cgl.core.utils.read_write import load_json
from .smart_task import SmartTask
from cgl.plugins.blender.alchemy import PathObject, scene_object
from cgl.ui.widgets.dialog import InputDialog
import cgl.core.assetcore as assetcore
import bpy


TASKNAME = os.path.basename(__file__).split('.py')[0]


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            self.path_object = scene_object()

    def _import(self, filepath, import_rigs = True,reference = True ,task=None,latest =False, **kwargs):
        """
        imports a bundle file
        :param filepath:
        :param layout_group:
        :return:
        """
        from cgl.plugins.blender.alchemy import  set_relative_paths
        main_import(filepath,import_rigs,reference=reference,latest=latest)
        set_relative_paths(True)

    def build(self):
        from cgl.plugins.blender.utils import create_shot_mask_info,set_collection_name
        create_shot_mask_info()
        set_collection_name()


    def import_latest(self, seq=None, shot= None, import_rigs = True,reference=True,latest = False,**kwargs):
        """
        imports the latest layout for a shot.
        :param seq:
        :param shot: Asset Cateogry
        :param task: Asset
        :return:
        """
        layout_path = None
        if seq == None:
            self.seq = scene_object().seq
        if shot == None:
            self.shot = scene_object().shot

        layout_obj = scene_object().copy(task='lay', seq=self.seq, shot=self.shot, context='render',
                                         user='publish', latest=True, filename='*', ext=None)

        for each in glob.glob(layout_obj.path_root):
            if '.msd' in each:
                layout_path = each
        if layout_path:
            self._import(filepath=layout_path, import_rigs= import_rigs,reference=reference, latest = latest)
        else:
            print('Could not glob layout path at {}'.format(layout_obj.path))


def get_latest(ext='msd'):
    this_obj = scene_object().copy(task=TASKNAME, context='render',
                                   user='publish', latest=True, set_proper_filename=True, ext=ext)
    return this_obj


def main_import(filepath, import_rigs = True,reference = True, latest = False):
    """

    :param filepath:
    :return:
    """
    from pprint import pprint
    from cgl.core.config import app_config
    from cgl.plugins.blender.utils import get_next_namespace, read_matrix, parent_object, create_object
    from cgl.plugins.blender.alchemy import  reference_file, import_file
    from cgl.plugins.blender.msd import set_matrix
    from .anim import make_proxy
    import bpy
    relative_path = None
    root = app_config()['paths']['root']
    d = PathObject(filepath)

    layout_data = load_json(filepath)
    layout = create_object('{}_{}:lay'.format(scene_object().seq,scene_object().asset))
    group = create_object('{}_{}:FG'.format(scene_object().seq,scene_object().asset),parent=layout)

    pprint(layout_data)
    for each in layout_data:
        if 'source_path' in layout_data[each]:
            # this is a bundle, rather than a layout - unsure why this has changed so drastically
            # TODO - look at what's going on here.
            relative_path = layout_data[each]['source_path']
            task = layout_data[each]['task']
            transforms = layout_data[each]['transform'].split(' ')
        company = scene_object().company

        if root not in relative_path:

            reference_path = "%s\%s" % (root, relative_path)
        else:
            reference_path = relative_path
        float_transforms = [float(x) for x in transforms]

        d2 = PathObject(reference_path)
        if latest:
            d2 = d2.latest_version(publish_=True)
        ns2 = get_next_namespace(d2.shot)
        #if reference == True:

        #    print('referencing files ________________')
        #    ref = reference_file(namespace=ns2, filepath=reference_path)
        #else:

        print('IMPORTING FILES________________')
        print(d2.path_root)
        if not task == 'rig':

            ref = import_file(namespace=ns2, filepath=d2.path_root)
            ref = bpy.data.objects['{}:{}'.format(ns2,d2.task)]
            layout_group = create_object(('{}_{}:FG'.format(scene_object().seq,scene_object().asset)))
            parent_object(child=ref,parent=layout_group)


        # if task == 'rig':
        #     if reference:
        #
        #         print('________IMPORTING RIG_____________')
        #         rig = make_proxy(d2, ref)
        #         rig_root = layout_data[each]['rig_root']
        #         proxy = bpy.data.objects['{}:rig_proxy'.format(ns2)]
        #         ref = proxy.pose.bones[rig_root]
        #         parent_object(proxy,group)
        #     else:
        #         print('________IMPORT Rig set to false_____________')

        set_matrix(ref, float_transforms)



def check_reference_attribute(attribute,reference_path = None):
    from cgl.plugins.blender.alchemy import scene_object,PathObject, set_relative_paths
    set_relative_paths(False)
    failed_libraries = []

    if not reference_path:
        reference_path = scene_object()

    attrib_check = eval('reference_path.{}'.format(attribute))

    for library in bpy.data.libraries:
        path_object = PathObject(library.filepath)
        lib_attribute = eval('path_object.{}'.format(attribute))
        if not lib_attribute == attrib_check:
            new_filepath = eval("path_object.copy(attibute=attrib_check).path_root")
            library.filepath = new_filepath
            library.reload()

    for library in bpy.data.libraries:
        path_object = PathObject(library.filepath)
        lib_attribute = eval('path_object.{}'.format(attribute))
        if not lib_attribute == attrib_check:
            failed_libraries.append(path_object.filename)

    set_relative_paths(True)

    return failed_libraries
