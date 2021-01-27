import cgl.plugins.maya.alchemy as alc

def run():
    """
    Build for a model sets up the model hierarchy for the artist.
    :return:
    """
    alc.build()  # "lm.build()" uses the smart task system.  you can find the code in cgl_tools/tasks/$TASKNAME.py in the build() method.

