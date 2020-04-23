import click
import time


def check_message_queue():
    import cgl.plugins.aws.cgl_sqs.utils as sqs_utils
    messages = sqs_utils.receive_messages()
    print messages


def check_syncthing_config():
    # this may end up being something we just integrate into our pyqt module
    import cgl.plugins.syncthing.utils as st_utils
    config_file = st_utils.get_config_path()
    # check for changes in this file


@click.command()
@click.option('--seconds', '-s', default=60.0,
              help='Input the time between running designated lumber watch scripts')
@click.option('--queue', '-q', default=True,
              help='Checks the CG Lumberjack message Queue for notifications every s seconds')
@click.option('--syncthing', '-st', default=False,
              help='Checks Syncthing config.xml for changes every s seconds.')
def main(seconds, queue, syncthing):
    start_time = time.time()
    while True:
        if queue:
            check_message_queue()
        if syncthing:
            check_syncthing_config()
        time.sleep(seconds - ((time.time() - start_time) % seconds))


if __name__ == '__main__':
    main()
