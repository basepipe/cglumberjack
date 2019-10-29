import os

"""
A File for testing shotgun related functions as i figure out workflow for testing the daemon
"""


def get_asset_status(task, status):
    """
    give task name and status name return the status the asset should be.
    :param task:
    :param status:
    :return:
    """
    keep_same = ['rev', "omt", 'hld']
    previous_task = ['stdn', 'mdl', 'tex', 'shd']
    long_to_short = {'stdn ip': 's_ip',
                     'stdn apr': 's_apr',
                     'mdl wtg': 'wtg',
                     'mdl ip': 'm_ip',
                     'mdl apr': 'm_apr',
                     'shd ip': 'sh_ip',
                     'shd apr': 'sh_apr',
                     'tex ip': 't_ip',
                     'tex apr': 't_apr',
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
    return long_to_short[asset_status]

#
# print get_asset_status('mdl', 'wtg')
# print get_asset_status('stdn', 'ip')
# print get_asset_status('stdn', 'apr')
# print get_asset_status('stdn', 'rev')
# print get_asset_status('stdn', 'hld')
# print get_asset_status('stdn', 'omt')
#
# print get_asset_status('mdl', 'wtg')
# print get_asset_status('mdl', 'ip')
# print get_asset_status('mdl', 'apr')
# print get_asset_status('mdl', 'rev')
# print get_asset_status('mdl', 'hld')
# print get_asset_status('mdl', 'omt')
#
# print get_asset_status('tex', 'wtg')
# print get_asset_status('tex', 'ip')
# print get_asset_status('tex', 'apr')
# print get_asset_status('tex', 'rev')
# print get_asset_status('tex', 'hld')
# print get_asset_status('tex', 'omt')
#
# print get_asset_status('shd', 'wtg')
# print get_asset_status('shd', 'ip')
# print get_asset_status('shd', 'apr')
# print get_asset_status('shd', 'rev')
# print get_asset_status('shd', 'hld')
# print get_asset_status('shd', 'omt')
