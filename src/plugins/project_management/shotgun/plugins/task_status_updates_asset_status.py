"""
Necessary Documentation of the code

Author: You
Template Author: Andrew Britton
"""

import shotgun_api3


def registerCallbacks(reg):
    # This takes the form of:
    #    matchEvents = {'Shotgun_Entity_EventType': ['list', 'of', 'field', 'names', 'you', 'need', 'sg_custom_field']}
    # the 'id' is always returned, in addition to any fields specifically requested by your callback

    server = "https://fsuada.shotgunstudio.com"
    script_name = 'core_tools'
    script_key = 'bc29cd2fd4ce9fe3c2598c4d559b09f88eaa95b05edfd12a834a23aea0797e2f'
    sg = shotgun_api3.Shotgun(server, script_name=script_name, api_key=script_key)

    args = {
        'asset_delivery_change': ['sg_asset_delivery', 'sg_delivery_date']
    }

    # Bail if our validator fails.
    if not is_valid(sg, reg.logger, args):
        reg.logger.warning("Plugin is not valid, will not register callback.")
        return
    # script_name and script_key are defined by you whenever you create a SG script
    # the entry_function_call refers to the function that performs the work of the event plugin
    reg.registerCallback('script_name', 'script_key', entry_function_call, args, None)


def is_valid(sg, logger, args):
    """
    Validate our args.

    :param sg: Shotgun API handle.
    :param logger: Logger instance.
    :param args: Any additional misc arguments passed through this plugin.
    :returns: True if plugin is valid, None if not.
    """
    return True


def entry_function_call(sg, logger, event, args):
    print event['meta']
    pass