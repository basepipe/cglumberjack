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
    script_name = os.environ["SGDAEMON_USWNIC_NAME"]
    script_key = os.environ["SGDAEMON_USWNIC_KEY"]

    args = {
        "entity_type": "Version",
        "status_field": "sg_status_list",
        "trigger_statuses": ["rev"],
        "new_status": "vwd"
    }

    reg.registerCallback(
        script_name,
        script_key,
        update_status_when_note_is_created,
        {"Shotgun_Note_New": None},
        args,
    )
    reg.logger.debug("Registered callback.")


def update_status_when_note_is_created(sg, logger, event, args):
    """
    If a Note is created on an entity where the entity's Status field is set to
    a status in trigger_statuses, then set the entity's Status to new_status.

    :param sg: Shotgun API handle.
    :param logger: Logger instance.
    :param event: A Shotgun EventLogEntry entity dictionary.
    :param args: Any additional misc arguments passed through this plugin.
    """

    # Return if we don't have all the field values we need.
    if not event.get("meta", {}).get("entity_id"):
        return

    # Make some vars for convenience.
    note_id = event["meta"]["entity_id"]

    # Re-query our Note for additional field values.
    note = sg.find_one(
        "Note",
        [["id", "is", note_id]],
        ["note_links"],
    )

    # Return if the Note doesn't exist.
    if not note:
        logger.debug("Could not find Note with ID %s, skipping." % note_id)
        return

    # Find any linked entities and store them in a list.
    linked_entities = []
    for link in note["note_links"]:
        if link["type"] == args["entity_type"]:
            linked_entities.append(link)

    # Return if no linked entities were found.
    if not linked_entities:
        logger.debug(
            "No %ss linked to Note with id %s, skipping." % (args["entity_type"], note_id)
        )
        return

    # Init our batch_data list.
    batch_data = []

    # Find the entity Statuses and update them, if necessary.
    for linked_entity in linked_entities:

        # Re-query the entity for additional field values.
        entity = sg.find_one(
            args["entity_type"],
            [["id", "is", linked_entity["id"]]],
            [args["status_field"]],
        )

        # Continue if the entity is not found.
        if not entity:
            logger.debug(
                "Could not find linked %s with id %s, skipping." % (
                    args["entity_type"],
                    entity["id"],
                )
            )
            continue

        # Only update if the Status of the entity is new_status_value.
        if entity[args["status_field"]] not in args["trigger_statuses"]:
            logger.debug(
                "Linked %s with id %s does not have a status of %s, skipping update." % (
                    args["entity_type"],
                    entity["id"],
                    args["trigger_statuses"],
                )
            )
            continue

        # Add our update request to the batch_data list.
        batch_data.append({
            "request_type": "update",
            "entity_type": args["entity_type"],
            "entity_id": entity["id"],
            "data": {args["status_field"]: args["new_status"]},
        })

    # Send the Shotgun API batch request if we have stuff to update.
    if batch_data:
        result = sg.batch(batch_data)
        logger.info("Updated SG with %s" % str(result))
    else:
        logger.info("No updates necessary.")
