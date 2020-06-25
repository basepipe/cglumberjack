from cgl.plugins.maya import lumbermill

def run():
    # task=None assumes we pull task from the lumbermill.scene_object()
    lumbermill.launch_preflight(task=None)
