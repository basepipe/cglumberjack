# Copyright 2018 Autodesk, Inc.  All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license agreement
# provided at the time of installation or download, or which otherwise accompanies
# this software in either electronic or hard copy form.
#

# See docs folder for detailed usage info.

import os


def registerCallbacks(reg):
    """
    Register our callbacks.

    :param reg: A Registrar instance provided by the event loop handler.
    """

    # Grab authentication env vars for this plugin. Install these into the env
    # if they don't already exist.
    script_name = os.environ["SGDAEMON_INITSHOTHANDLES_NAME"]
    script_key = os.environ["SGDAEMON_INITSHOTHANDLES_KEY"]

    args = {
        "smart_head_in": 1001,
        "smart_head_duration": 8,
        "smart_tail_duration": 8,
    }

    event_filter = {
        "Shotgun_Shot_New": None,
    }

    reg.registerCallback(
        script_name,
        script_key,
        init_shot_handles,
        event_filter,
        args,
    )


def init_shot_handles(sg, logger, event, args):
    """
    Initialize handles for a new shot
    """

    # Return if we don't have all the field values we need.
    if not event.get("meta", {}).get("entity_id"):
        return

    # Makes some vars for convenience.
    smart_head_in = args["smart_head_in"]
    smart_head_duration = args["smart_head_duration"]
    smart_tail_duration = args["smart_tail_duration"]

    # Grab the Shot.
    filters = [["id", "is", event.get("meta").get("entity_id")]]
    fields = ["code", "smart_head_in", "smart_head_duration", "smart_tail_duration"]
    shot = sg.find_one("Shot", filters, fields)

    # if the shot isn't found, exit trigger
    if shot is None:
        return

    updatedata = {}
    # Only update fields that are not set and if we have a default value
    if smart_head_in is not None and not shot.get("smart_head_in"):
        updatedata["smart_head_in"] = smart_head_in

    if smart_head_duration is not None and not shot.get("smart_head_duration"):
        updatedata["smart_head_duration"] = smart_head_duration

    if smart_tail_duration is not None and not shot.get("smart_tail_duration"):
        updatedata["smart_tail_duration"] = smart_tail_duration

    if updatedata:
        # update the Shot with the new gross
        sg.update("Shot", shot["id"], updatedata)
        logger.info("%s: shot handles initialized with %s" % (shot.get("code"), str(updatedata)))
    else:
        logger.info("Not updating %s shot handles as values are already set" % shot.get("code"))
