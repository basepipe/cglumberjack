

def get_asset_status(task, status):
    """
    give task name and status name return the status the asset should be.
    :param task:
    :param status:
    :return:
    """
    keep_same = ['Review', "Omit", 'On Hold']
    previous_task = ['StandIn', 'Model', 'Texture', 'Shader']
    long_to_short = {'StandIn In Progress': 's_ip',
                     'StandIn Done': 's_apr',
                     'Model In Progress': 'm_ip',
                     'Model Done': 'm_apr',
                     'Shader In Progress': 'sh_ip',
                     'Shader Done': 'sh_apr',
                     'Texture In Progress': 't_ip',
                     'Texture Done': 't_apr',
                     'Waiting to Start': 'wtg',
                     'Review': 'rev',
                     'Omit': 'omt',
                     'On Hold': 'hld'
                     }
    if status == 'Waiting to Start':
        index = previous_task.index(task)
        if index:
            task = previous_task[index-1]
            status = 'Done'
            asset_status = '%s %s' % (task, status)
        else:
            asset_status = 'Waiting to Start'
    elif status in keep_same:
        asset_status = status
    else:
        asset_status = '%s %s' % (task, status)
    return asset_status, long_to_short[asset_status]


print get_asset_status('StandIn', 'Waiting to Start')
print get_asset_status('StandIn', 'In Progress')
print get_asset_status('StandIn', 'Done')
print get_asset_status('StandIn', 'Review')
print get_asset_status('StandIn', 'On Hold')
print get_asset_status('StandIn', 'Omit')

print get_asset_status('Model', 'Waiting to Start')
print get_asset_status('Model', 'In Progress')
print get_asset_status('Model', 'Done')
print get_asset_status('Model', 'Review')
print get_asset_status('Model', 'On Hold')
print get_asset_status('Model', 'Omit')

print get_asset_status('Texture', 'Waiting to Start')
print get_asset_status('Texture', 'In Progress')
print get_asset_status('Texture', 'Done')
print get_asset_status('Texture', 'Review')
print get_asset_status('Texture', 'On Hold')
print get_asset_status('Texture', 'Omit')

print get_asset_status('Shader', 'Waiting to Start')
print get_asset_status('Shader', 'In Progress')
print get_asset_status('Shader', 'Done')
print get_asset_status('Shader', 'Review')
print get_asset_status('Shader', 'On Hold')
print get_asset_status('Shader', 'Omit')

