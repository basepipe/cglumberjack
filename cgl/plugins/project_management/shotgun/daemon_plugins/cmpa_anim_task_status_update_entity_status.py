# Copyright 2018 Autodesk, Inc.  All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license agreement
# provided at the time of installation or download, or which otherwise accompanies
# this software in either electronic or hard copy form.
#

# See docs folder for detailed usage info.

import os
import cgl.plugins.project_management.shotgun.shotgun_api3 as shotgun_api3


def get_asset_status(task, status):
    """
    give task name and status name return the status the asset should be.
    :param task:
    :param status:
    :return:
    """
    print(task, status)
    keep_same = ['rev', "omt", 'hld', 'not', 'wtg']
    previous_task = ['stdn', 'mdl', 'tex', 'shd']
    long_to_short = {'stdn ip': 's_ip',
                     'stdn pub': 's_pub',
                     'stdn apr': 's_apr',
                     'mdl wtg': 'wtg',
                     'mdl ip': 'm_ip',
                     'mdl pub': 'm_pub',
                     'mdl apr': 'm_apr',
                     'shd ip': 'sh_ip',
                     'shd apr': 'sh_apr',
                     'shd pub': 'sh_pub',
                     'tex ip': 't_ip',
                     'tex apr': 't_apr',
                     'tex pub': 't_pub',
                     'not': 'not',
                     'wtg': 'wtg',
                     'rev': 'rev',
                     'omt': 'omt',
                     'hld': 'hld'
                     }
    if status == 'wtg':
        index = previous_task.index(task)
        if index:
            task = previous_task[index-1]
            status = 'apr'
            asset_status = '%s %s' % (task, status)
        else:
            asset_status = 'wtg'
    elif status in keep_same:
        asset_status = status
    else:
        asset_status = '%s %s' % (task, status)
    if asset_status in long_to_short.keys():
        return long_to_short[asset_status]
    else:
        print('Didnt find %s in keys' % asset_status)


def get_next_task_status(task_status):
    # these are things that *should change or at least require some kind of
    # notification when they happen.
    # a slack notification for example would be amazing.

    # TODO - it'd be great to have a check to make sure the task to be changed
    # is starting from a 'wtg' status.
    status_lookup = {'stdn pub': ['mdl', 'rdy'],
                     'mdl pub': ['tex', 'rdy'],
                     'tex pub': ['shd', 'rdy']
                     }

    if task_status in status_lookup:
        return status_lookup[task_status]
    else:
        return None


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
        "task_status_field": "sg_status_list",
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
        {"Shotgun_Task_Change": args["task_status_field"]},
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
    except Exception as e:
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

    if (not event.get("meta", {}).get("entity_id") and
        not event.get("meta", {}).get("old_value") and
        not event.get("meta", {}).get("new_value")):
            return

    # Make some vars for convenience.
    task_id = event["meta"]["entity_id"]
    new_value = event["meta"]["new_value"]
    task = sg.find_one("Task", [["id", "is", task_id]], ["entity", 'content'])
    if task:
        shortname = task['content'].split('_')[-1]
        entity = sg.find_one(task['entity']['type'], [["id", "is", task['entity']['id']]], ['sg_status_list'])
        # next_task_status = get_next_task_status('%s %s' % (shortname, new_value))
        # if next_task_status:
        #     task, status = next_task_status
        #     all_tasks = sg.find("Task", [['entity', 'is', entity]], ['content', 'sg_status_list'])
        #     for t in all_tasks:
        #         print(t)
        #         print(t['content'])
        #         print('-----------------')
        #         if task in t['content']:
        #             print('found a match for %s' % task)

        new_asset_status = get_asset_status(shortname, new_value)
        if new_asset_status:
            sg.update(entity["type"],
                      entity["id"],
                      {'sg_status_list': new_asset_status}
                      )
