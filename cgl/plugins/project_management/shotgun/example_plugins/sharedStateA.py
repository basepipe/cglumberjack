# Copyright 2018 Autodesk, Inc.  All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license agreement
# provided at the time of installation or download, or which otherwise accompanies
# this software in either electronic or hard copy form.
#

# See docs folder for detailed usage info.

import os

_state = {
    'sequential': -1,
    'rotating': -1,
}


def registerCallbacks(reg):
    """
    Register all necessary or appropriate callbacks for this plugin.
    """

    scriptName = os.environ["SGDAEMON_SHAREDSTATEA_NAME"]
    scriptKey = os.environ["SGDAEMON_SHAREDSTATEA_KEY"]

    # Callbacks are called in registration order. So callbackA will be called
    # before callbackB and callbackC
    reg.registerCallback(scriptName, scriptKey, callbackA)
    reg.registerCallback(scriptName, scriptKey, callbackB)
    reg.registerCallback(scriptName, scriptKey, callbackC)


def callbackA(sg, logger, event, args):
    """
    :param sg: Shotgun API handle.
    :param logger: Logger instance.
    :param event: A Shotgun EventLogEntry entity dictionary.
    :param args: Any additional misc arguments passed through this plugin.
    """

    # We know callbackA will be called first because we registered it first.
    # As the first thing to run on each event, we can reinizialize the rotating
    # counter.
    global _state
    _state['rotating'] = -1

    # Then we pass off to our helper function... because I'm lazy.
    printIds(sg, logger, event, args)


def callbackB(*args):
    # Just an example plugin, remember... Get the ids incremented and logged.
    printIds(*args)


def callbackC(*args):
    # Just an example plugin, remember... Get the ids incremented and logged.
    printIds(*args)


def printIds(sg, logger, event, args):
    # Here we can increment the two counters that are in shared state. Each
    # callback has played with the contents of this shared dictionary.
    global _state
    _state['sequential'] += 1
    _state['rotating'] += 1

    # Log the counters so we can actually see something.
    logger.info('Sequential #%d - Rotating #%d', _state['sequential'], _state['rotating'])
