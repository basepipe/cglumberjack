import click
import time


def check_message_queue():
    import cgl.plugins.aws.cgl_sqs.utils as sqs_utils
    return sqs_utils.receive_messages()


def check_syncthing_status():
    import cgl.plugins.syncthing.utils as st_utils
    return st_utils.syncthing_running()


def check_syncthing_config():
    """
    checks timestamp of the syncthing config.  If it finds that it's changed since the last time it checked
    it returns True, if there's no Change returns False, if we haven't tracked the previous time stamp, returns False
    :return:
    """
    from os.path import getmtime
    import cgl.plugins.syncthing.utils as st_utils
    from cgl.core.config import UserConfig, user_config
    from cgl.core.utils.general import save_json
    user_config_path = str(user_config())
    config_file = st_utils.get_config_path()
    user_config_dict = UserConfig().d
    time_stamp = getmtime(config_file)
    if 'sync_thing_config_modified' in user_config_dict.keys():
        previous_time_stamp = user_config_dict['sync_thing_config_modified']
        if time_stamp != previous_time_stamp:
            print 'New Time Stamp for cgl_config, updating to %s' % time_stamp
            user_config_dict['sync_thing_config_modified'] = time_stamp
            save_json(user_config_path, user_config_dict)
            return True
        else:
            return False
    print('No previous timestamp detected, starting to track')
    user_config_dict['sync_thing_config_modified'] = time_stamp
    save_json(user_config_path, user_config_dict)
    return False


@click.command()
@click.option('--seconds', '-s', default=60.0,
              help='Input the time between running designated lumber watch scripts')
@click.option('--queue', '-q', default=True,
              help='Checks the CG Lumberjack message Queue for notifications every s seconds')
@click.option('--syncthing', '-st', default=True,
              help='Checks Syncthing config.xml for changes every s seconds.')
def main(seconds, queue, syncthing):
    start_time = time.time()
    while True:
        if queue:
            check_message_queue()
        if syncthing:
            check_syncthing_status()
            st_config_change = check_syncthing_config()
        time.sleep(seconds - ((time.time() - start_time) % seconds))


if __name__ == '__main__':
    main()
