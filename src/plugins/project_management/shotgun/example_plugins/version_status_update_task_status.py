# Copyright 2018 Autodesk, Inc.  All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license agreement
# provided at the time of installation or download, or which otherwise accompanies
# this software in either electronic or hard copy form.
#

# See docs folder for detailed usage info.

import os
import pytz


def registerCallbacks(reg):
    """
    Register our callbacks
    :param reg: A Registrar instance provided by the event loop handler
    """

    # Grab authentication env vars for this plugin. Install these into the env
    # if they don't already exist.
    script_name = os.environ["SGDAEMON_VSUTS_NAME"]
    script_key = os.environ["SGDAEMON_VSUTS_KEY"]

    args = {
        "date_approved_field": "client_approved_at",
        "date_approved_timezone": "US/Pacific",
        "approved_status_code": "apr",
    }

    reg.registerCallback(
        script_name,
        script_key,
        version_status_changed,
        {"Shotgun_Version_Change": ["sg_status_list"]},
        args,
    )
    reg.logger.debug("Registered callback.")


def version_status_changed(sg, logger, event, args):
    """
    First, check the new Version status for an sg_task_status_mapping
    Status value to set the linked Task to. Second, update the
    Version.sg_date_approved value when a Version's status is set to
    the approved status.

    :param sg: Shotgun API instance
    :param logger: Standard Event loop logger
    :param event: ShotgunEvent this trigger is listening for
    :param args: Additional arguments registerd for this trigger.
    """

    # Return if we don't have all the field values we need.
    if (not event.get("entity", {}).get("id") or
        not event.get("entity", {}).get("name") or
        not event.get("id")):
            return

    # Make some vars for convenience.
    entity_id = event["entity"]["id"]
    entity_name = event["entity"]["name"]

    # Get information needed by this trigger for the input Version entity.
    # Re-query for the Version Status value to make sure we have an up-to-date
    # new status value. The input value from the event may be inaccurate if the
    # triggers are ever running behind.
    sg_version = sg.find_one(
        "Version",
        [["id", "is", entity_id]],
        ["sg_task", "entity", "sg_status_list", "sg_task.Task.sg_status_list"]
    )
    if not sg_version:
        logger.info("Unable to retrieve Version (%d) %s from SG for event %d!" % (
            entity_id, entity_name, event["id"])
        )
        return

    new_version_status = sg_version["sg_status_list"]
    batch_cmds = []

    # if we have a linked Task, check to see if we can update its status
    if sg_version["sg_task"]:
        cur_task_status = sg_version["sg_task.Task.sg_status_list"]

        # Determine which, if any, status to set the linked Task to.
        new_task_status = None
        if new_version_status:
            sg_status = sg.find_one(
                "Status",
                [["code", "is", new_version_status]],
                ["sg_task_status_mapping"]
            )
            new_task_status = sg_status.get("sg_task_status_mapping")
            logger.debug("Status [%s] Task Status mapping: %s" % (new_version_status, new_task_status))
            logger.debug("Task current status: %s" % sg_version["sg_task.Task.sg_status_list"])

            if new_task_status and new_task_status != cur_task_status:
                # Verify the new Task status is a valid Task status.  We need to check
                # this here rather than before we register the plugin because the
                # sg_task_status_mapping value can be changed at any time.
                task_status_list = sg.schema_field_read(
                    "Task",
                    "sg_status_list"
                )["sg_status_list"]["properties"]["valid_values"]["value"]

                if new_task_status not in task_status_list:
                    logger.info("Invalid Task status detected: %s" % new_task_status)
                    logger.info("Cannot update Version [%d] Task status." % entity_id)
                    new_task_status = None
                logger.debug("New Task status: %s" % new_task_status)

        logger.debug("Version Task: %s" % sg_version["sg_task"])
        if new_task_status and new_task_status != cur_task_status:
            # Update the linked Task's status to the value resolved from
            # Version.sg_status_list.Status.sg_task_status_mapping
            batch_cmds.append({
                "request_type": "update",
                "entity_type": sg_version["sg_task"]["type"],
                "entity_id": sg_version["sg_task"]["id"],
                "data": {"sg_status_list": new_task_status}
            })

    # Check for input Version status changed to the Approved status
    if new_version_status == args["approved_status_code"]:
        # Update the input Version's sg_date_approved value to the time
        # the event was created, localized based on the timezone specified in
        # the plugin's args.
        local_timezone = pytz.timezone(args["date_approved_timezone"])
        approved_date = event["created_at"].astimezone(local_timezone)

        # there's also a possibility the sg_date_approved field is a date instead
        # of a datetime, check that in the schema
        date_approved_field_type = sg.schema_field_read(
            "Version",
            args["date_approved_field"],
        )[args["date_approved_field"]]["data_type"]["value"]
        # if the field type is date, update the var accordingly
        if date_approved_field_type == "date":
            approved_date = approved_date.date()

        logger.debug("Setting Date Approved value to: %s" % approved_date)
        batch_cmds.append({
            "request_type": "update",
            "entity_type": "Version",
            "entity_id": entity_id,
            "data": {
                args["date_approved_field"]: approved_date,
            }
        })

    if batch_cmds:
        # Execute the batch command(s)
        logger.info("Running [%d] batch command(s) to update Version and Task values ..." % (
            len(batch_cmds))
        )
        [logger.debug("    %s" % bc) for bc in batch_cmds]
        results = sg.batch(batch_cmds)
        logger.debug("    RESULTS: %s" % results)
