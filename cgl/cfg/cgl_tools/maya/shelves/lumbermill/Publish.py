from cgl.plugins.maya import alchemy

def run():
    # task=None assumes we pull task from the lumbermill.scene_object()
    alchemy.launch_preflight(task=None)
