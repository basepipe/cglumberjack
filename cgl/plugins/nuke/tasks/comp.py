from cgl.plugins.nuke.tasks.smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
import cgl.plugins.nuke.alchemy as alc

import nuke
from cgl.core.path import PathObject, lj_list_dir, find_latest_publish_objects
from cgl.core.config import app_config
from cgl.plugins.nuke.alchemy import PathObject, import_directory, import_media, set_comp_default_settings
import os
class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.nuke.alchemy import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        1. Reference the latest model for this asset
        2. Import latest textures for this asset (and assemble a shader network)
        :return:
        """
        print('building comp')
        if alc.scene_object().asset:

            dependencies = import_dependencies()
            if dependencies:

                set_comp_default_settings()
            else:
                print('no dependencies imported ')
    def _import(self, filepath):
        pass


def get_dependencies():
    current_shot = PathObject(nuke.root().name())
    all_tasks = current_shot.glob_project_element('task')
    publish_objects = []

    for task in all_tasks:

        task_object = current_shot.copy(filename='',
                                        task=task,
                                        user='publish',
                                        context='render').latest_version()
        if os.path.isdir(task_object.copy(filename='').path_root):
            publish_objects.append(task_object)

    return (publish_objects)


def import_dependencies():
    current_shot = PathObject(nuke.root().name())
    publish_objects = get_dependencies()
    spread = 0

    for task_object in publish_objects:

        if task_object.task != current_shot.task:

            filename = lj_list_dir(task_object.path_root)[0]
            sequence_path = task_object.copy(filename=filename)

            print(task_object.path)
            readNode = import_media(sequence_path.path_root, name=task_object.task)
            readNode.setSelected(True)

            color_dic = {'plate': 1278818815.0, 'elem': 1230983935.0, 'cam': 1264526079.0, 'default': 825305599.0}

            if task_object.task in color_dic.keys():
                tile_color = color_dic[task_object.task]
            else:
                tile_color = color_dic['default']

            n = nuke.nodes.BackdropNode(xpos=readNode.xpos() - 20,
                                        bdwidth=120,
                                        ypos=readNode.ypos() - 80,
                                        bdheight=170,
                                        tile_color=tile_color,
                                        note_font_size=42,
                                        z_order=0,
                                        name='{} BACKDROP'.format(
                                            task_object.task.upper()),
                                        label=task_object.task.upper())

    return(publish_objects)