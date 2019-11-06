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
    # server = os.environ["SG_SERVER"]
    script_name = os.environ["SGDAEMON_UVTF_NAME"]
    script_key = os.environ["SGDAEMON_UVTF_KEY"]

    args = {
        "matched_version_field": "user",
        "matched_task_field": "task_assignees",
        "matched_task_step_value": ["ART"],
    }

    task_event_filter = {
        "Shotgun_Task_Change": [args["matched_task_field"], "step"]
    }

    version_event_filter = {
        "Shotgun_Version_Change": ["entity", args["matched_version_field"]]
    }

    reg.registerCallback(
        script_name,
        script_key,
        find_task_versions,
        task_event_filter,
        args,
    )

    reg.registerCallback(
        script_name,
        script_key,
        update_version_task_field,
        version_event_filter,
        args,
    )
    reg.logger.debug("Registered callbacks.")


def find_task_versions(sg, logger, event, args):
    """
    If we have a Task, get all the Versions linked to that Task's Shot and
    check them to see if they link to our Task. If they do, then we have a
    Version (or multiple Versions) we should run the trigger on.

    :param sg: Shotgun API handle.
    :param logger: Logger instance.
    :param event: A Shotgun EventLogEntry entity dictionary.
    :param args: Any additional misc arguments passed through this plugin.
    """

    # Return if we don't have all the field values we need.
    if not event.get("meta", {}).get("entity_id"):
        return

    # Make some vars for convenience.
    entity_id = event["meta"]["entity_id"]

    # Re-query our Task to get the linked Shot.
    task = sg.find_one(
        "Task",
        [["id", "is", entity_id]],
        ["entity"],
    )

    # Get all Versions linked to the same Shot as our Task.
    versions = sg.find(
        "Version",
        [["entity", "is", task["entity"]]],
    )

    # If a Version is linked to our Task, run the trigger on it.
    for version in versions:
        fake_event = {
            "meta": {
                "entity_id": version["id"],
            }
        }
        update_version_task_field(sg, logger, fake_event, args)


def update_version_task_field(sg, logger, event, args):
    """
    This is a trigger to set the Version.sg_task (Task entity) field based on
    the linked entity's Tasks.

    Trigger action:
        When activated the Version.[version_task_field] should be updated to be
        the Task that matches the following criteria (or set to None if no Task
        is found):

            (Task.entity = Version.entity AND
            Task.["matched_task_field"] = Version.user AND
            Task.step.Step.short_name = args["matched_task_step_value"]

        If there's more than one match, just use any of them.

    :param sg: Shotgun API handle.
    :param logger: Logger instance.
    :param event: A Shotgun EventLogEntry entity dictionary.
    :param args: Any additional misc arguments passed through this plugin.
    """

    # Return if we don't have all the field values we need.
    if not event.get("meta", {}).get("entity_id"):
        return

    # Make some vars for convenience.
    entity_id = event["meta"]["entity_id"]

    # Re-query our Verison to gather additional field values.
    version = sg.find_one(
        "Version",
        [["id", "is", entity_id]],
        ["entity", "entity.Shot.sg_shot_type", args["matched_version_field"], "project"],
    )

    # Return if we are missing necessary field data.
    if not version:
        logger.debug("No Version with id %d, skipping." % entity_id)
        return
    elif not version["entity"]:
        logger.debug("Version %s not linked to an entity, skipping." % entity_id)
        return
    elif not version[args["matched_version_field"]]:
        logger.debug(
            "Version %s not linked to %s field, skipping." % (
                entity_id,
                args["matched_version_field"]
            )
        )
        return
    elif not version["project"]:
        logger.debug("Version %s not linked to a Project, skipping." % entity_id)
        return

    step_filter = ["step.Step.short_name", "in", args["matched_task_step_value"]]

    # Find any Task that matches the Version's entity, user, and step_filter.
    # From the Python API docs: "when used on multi_entity, "is" functions as
    # you would expect 'contains' to function." This is used below to filter the
    # matched_task_field against the version["matched_version_field"] value.
    linked_task = sg.find_one(
        "Task",
        [
            ["entity", "is", version["entity"]],
            [args["matched_task_field"], "is", version[args["matched_version_field"]]],
            ["project", "is", version["project"]],
            step_filter
        ],
    )

    # Return if our linked Task doesn't exist.
    if not linked_task:
        logger.debug(
            "No Task attached to Version with linked entity %s and %s field value, Skipping." % (
                entity_id,
                args["matched_version_field"],
                )
            )
        return

    # Update our Version with the linked Task.
    sg.update(
        "Version",
        entity_id,
        {"sg_task": linked_task},
    )
    logger.debug("Updated \"sg_task\" for Version with id %s" % entity_id)
