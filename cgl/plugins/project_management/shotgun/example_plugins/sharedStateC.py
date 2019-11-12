# Copyright 2018 Autodesk, Inc.  All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license agreement
# provided at the time of installation or download, or which otherwise accompanies
# this software in either electronic or hard copy form.
#

# See docs folder for detailed usage info.

import os


class Callback(object):

    def __init__(self, state, rotate=False):
        self.rotate = rotate
        self.state = state

    def __call__(self, sg, logger, event, args):
        if self.rotate:
            self.state['rotating'] = -1

        # Here we can increment the two counters that are in shared state. Each
        # callback has played with the contents of this shared dictionary.
        self.state['sequential'] += 1
        self.state['rotating'] += 1

        # Log the counters so we can actually see something.
        logger.info(
            'Sequential #%d - Rotating #%d',
            self.state['sequential'],
            self.state['rotating'],
        )


def registerCallbacks(reg):
    """
    Register all necessary or appropriate callbacks for this plugin.
    """

    scriptName = os.environ["SGDAEMON_SHAREDSTATEC_NAME"]
    scriptKey = os.environ["SGDAEMON_SHAREDSTATEC_KEY"]

    # Prepare the shared state object
    _state = {
        'sequential': -1,
        'rotating': -1,
    }

    # Callbacks are called in registration order. So callbackA will be called
    # before callbackB and callbackC
    reg.registerCallback(scriptName, scriptKey, Callback(_state, rotate=True))
    reg.registerCallback(scriptName, scriptKey, Callback(_state))
    reg.registerCallback(scriptName, scriptKey, Callback(_state))
