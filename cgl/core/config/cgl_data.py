from cgl.core.utils.general import load_json, save_json
import logging
import click


def edit_cgl_data(job_id, key, value=None, user=None):
    if not job_id:
        logging.info('No Job ID Defined')
        click.echo('No Job ID Defined')
        return
    if not key:
        logging.info('No Key Defined')
        click.echo('No Key Defined')
    if not value:
        value = time.time()
    if not user:
        user = current_user()
    cgl_data = os.path.join(os.path.dirname(CONFIG['paths']['globals']), 'cgl_data.json')
    if os.path.exists(cgl_data):
        data = load_json(cgl_data)
        print(user, job_id, key, value)
        data[user][job_id][key] = value
        save_json(cgl_data, data)
        print('saved it probably')
    else:
        logging.info('No cgl_data.json found! Aborting')
        click.echo('No cgl_data.json found! Aborting')
        return


@click.command()
@click.option('--edit_cgl', '-e', default=False, prompt='edit cgl data file for a user, job_id, and key/value pair')
@click.option('--user', '-u', default=current_user(), prompt='File Sequence Path (file.####.ext)',
              help='Path to the Input File.  Can be Image, Image Sequence, Movie')
@click.option('--job_id', '-j', default=None,
              help='job_id object to edit')
@click.option('--key', '-k', help='key to edit')
@click.option('--value', '-v', help='value for the key')
def main(edit_cgl, user, job_id, key, value):
    if edit_cgl:
        edit_cgl_data(user, job_id, key, value)


if __name__ == '__main__':
    main()
    # check_for_latest_master()