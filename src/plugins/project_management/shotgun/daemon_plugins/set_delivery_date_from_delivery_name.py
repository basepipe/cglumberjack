# Copyright 2018 Autodesk, Inc.  All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license agreement
# provided at the time of installation or download, or which otherwise accompanies
# this software in either electronic or hard copy form.
#

# See docs folder for detailed usage info.

import os
import shotgun_api3


def registerCallbacks(reg):
    """
    Register our callbacks.

    :param reg: A Registrar instance provided by the event loop handler.
    """

    # Grab authentication env vars for this plugin. Install these into the env
    # if they don't already exist.
    server = os.environ["SG_SERVER"]
    script_name = os.environ["SGDAEMON_TSUES_NAME"]
    script_key = os.environ["SGDAEMON_TSUES_KEY"]

    # User-defined plugin args, change at will.
    args = {
        "asset_delivery_field": "sg_asset_delivery",
        "entity_type": "Asset"
    }

    # Grab an sg connection for the validator.
    sg = shotgun_api3.Shotgun(server, script_name=script_name, api_key=script_key)

    # Bail if our validator fails.
    if not is_valid(sg, reg.logger, args):
        reg.logger.warning("Plugin is not valid, will not register callback.")
        return

    # Register our callback with the Shotgun_%s_Change event and tell the logger
    # about it.
    reg.registerCallback(
        script_name,
        script_key,
        update_entity_status,
        {"Shotgun_Asset_Change": "sg_asset_delivery"},
        args,
    )
    reg.logger.debug("Registered callback.")


def is_valid(sg, logger, args):
    """
    Validate our args.

    :param sg: Shotgun API handle.
    :param logger: Logger instance.
    :param args: Any additional misc arguments passed through this plugin.
    :returns: True if plugin is valid, None if not.
    """

    # Make sure we have a valid sg connection.
    try:
        sg.find_one("Project", [])
    except Exception, e:
        logger.warning(e)
        return

    return True


def update_entity_status(sg, logger, event, args):
    """
    Updates an entity's status if the conditions are met.

    :param sg: Shotgun API handle.
    :param logger: Logger instance.
    :param event: A Shotgun EventLogEntry entity dictionary.
    :param args: Any additional misc arguments passed through this plugin.
    """
    delivery_dict = {'Asset Delivery 1': 'sg_asset_delivery_1',
                     'Asset 50% Delivery': 'sg_asset_50__delivery',
                     'Asset Final Delivery': 'sg_asset_final_delivery'
                     }

    if (not event.get("meta", {}).get("entity_id") and
        not event.get("meta", {}).get("old_value") and
        not event.get("meta", {}).get("new_value")):
            return

    # Make some vars for convenience.
    entity_id = event["meta"]["entity_id"]
    new_value = event["meta"]["new_value"]
    if new_value in delivery_dict.keys():
        delivery_field = delivery_dict[new_value]
        entity = sg.find_one("Asset", [["id", "is", entity_id]], ["code", 'sg_asset_delivery', 'project',
                                                                  'project.Project.%s' % delivery_field])
        if entity:
            sg.update('Asset',
                      entity['id'],
                      {'sg_delivery_date': entity['project.Project.%s' % delivery_field]}
                      )