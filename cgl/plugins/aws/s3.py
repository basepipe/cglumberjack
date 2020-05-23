"""
AWS Credentials need to be in ~/.aws/credentials
aws_access_key=KEY_ID
aws_secret_access_key=ACCESS_KEY
"""
import os
import boto3
import time

ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
SECRET_KEY = os.environ['AWS_SECRET_KEY']
region_name = os.environ['AWS_DEFAULT_REGION']


def upload_file(file_path, bucket_name, acl='public-read'):
    # s3 = boto3.resource('s3')
    client = boto3.client('s3',
                          aws_access_key_id=ACCESS_KEY,
                          aws_secret_access_key=SECRET_KEY,
                          region_name=region_name)
    try:
        client.upload_file(Filename=file_path,
                                   Bucket=bucket_name,
                                   Key=os.path.basename(file_path),
                                   ExtraArgs={'ACL': acl})
        file_url = '%s/%s/%s' % (client.meta.endpoint_url, bucket_name, os.path.basename(file_path))
        return file_url
    except Exception as exp:
        print('exp: ', exp)


def transcribe(wav_uri, job_name):
    transcribe = boto3.client('transcribe')
    job_uri = wav_uri

    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat='wav',
        LanguageCode='en-US'
    )

    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        print("Not ready yet...")
        time.sleep(5)
    print(status)


# uploading to a non-encripted place first off.
# print 'Uploading Wav File...'
# url = upload_file(r'F:\FSU-CMPA\COMPANIES\VFX\render\editorialTests\assets\tutorials\nuke_masks\video\publish\000.000\high\showing_royce_masks_in_nuke.wav', 'cgl-developeronboarding')
# print url

transcribe(r'https://s3.amazonaws.com/cgl-developeronboarding/showing_royce_masks_in_nuke.wav', 'showing_royce')




