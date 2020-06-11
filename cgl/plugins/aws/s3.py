"""
AWS Credentials need to be in ~/.aws/credentials
aws_access_key=KEY_ID
aws_secret_access_key=ACCESS_KEY
"""
from __future__ import print_function
import os
import boto3
import requests
import uuid
import time
import click
from cgl.core.utils.general import save_json, cgl_execute
from cgl.core.convert import convert_to_mp4



def upload_file(file_path, bucket_name, acl='public-read'):
    # s3 = boto3.resource('s3')
    client = boto3.client('s3')
    try:
        client.upload_file(Filename=file_path,
                           Bucket=bucket_name,
                           Key=os.path.basename(file_path),
                           ExtraArgs={'ACL': acl})
        file_url = '%s/%s/%s' % (client.meta.endpoint_url, bucket_name, os.path.basename(file_path))
        return file_url
    except Exception as exp:
        print('exp: ', exp)


# purpose: Function to format the input parameters and invoke the Transcribe service
def createTranscribeJob(bucket, mediaFile):
    # Set up the Transcribe client
    transcribe = boto3.client('transcribe')

    # Set up the full uri for the bucket and media file
    mediaUri = "https://%s.s3.amazonaws.com/%s" % (bucket, mediaFile)
    print("Creating Job: " + "transcribe" + mediaFile + " for " + mediaUri)

    # Use the uuid functionality to generate a unique job name.  Otherwise, the Transcribe service will return an error
    response = transcribe.start_transcription_job(
        TranscriptionJobName="transcribe_" + uuid.uuid4().hex + "_" + mediaFile,
        LanguageCode="en-US",
        MediaFormat="mp4",
        Media={"MediaFileUri": mediaUri},
        Settings={'ShowSpeakerLabels': True,
                  'MaxSpeakerLabels': 7}
        )
    # TODO - add film vocabulary likely         Settings={"VocabularyName": "MyVocabulary"}

    # return the response structure found in the Transcribe Documentation
    return response


# purpose: simply return the job status
def getTranscriptionJobStatus(jobName):
    transcribe = boto3.client('transcribe')
    response = transcribe.get_transcription_job(TranscriptionJobName=jobName)
    return response


# purpose: get and return the transcript structure given the provided uri
def getTranscript(transcriptURI):
    # Get the resulting Transcription Job and store the JSON response in transcript
    result = requests.get(transcriptURI)
    return result.json()


def cgl_transcribe(bucket, filename, transcript_file_out):
    # Create Transcription Job
    response = createTranscribeJob(bucket, filename)
    # loop until the job successfully completes
    print("\n==> Transcription Job: " + response["TranscriptionJob"]["TranscriptionJobName"] + "\n\tIn Progress"),
    while response["TranscriptionJob"]["TranscriptionJobStatus"] == "IN_PROGRESS":
        print("."),
        time.sleep(30)
        response = getTranscriptionJobStatus( response["TranscriptionJob"]["TranscriptionJobName"] )
    print("\nJob Complete")
    print("\tStart Time: " + str(response["TranscriptionJob"]["CreationTime"]))
    print("\tEnd Time: " + str(response["TranscriptionJob"]["CompletionTime"]))
    print("\tTranscript URI: " + str(response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]))
    # Now get the transcript JSON from AWS Transcribe
    transcript = getTranscript(response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"])
    print("\n==> Transcript: \n" + transcript_file_out)
    save_json(transcript_file_out, transcript)


def upload_and_transcribe_audio(input_file, transcript_file_out, bucket='cgl-developeronboarding',
                                processing_method='local', dependent_job=None):
    if processing_method == 'local':
        print('Uploading File %s' % input_file)
        upload_file(input_file, bucket)
        print('Upload Complete...')
        time.sleep(3)
        cgl_transcribe(bucket, os.path.basename(input_file), transcript_file_out)
    elif processing_method == 'smedge':
        filename = "%s.py" % os.path.splitext(__file__)[0]
        command = r'python %s -i %s -o %s -b %s' % (filename, input_file, transcript_file_out, bucket)
        command_name = 'Upload & Transcribe'
        process_info = cgl_execute(command, command_name=command_name, methodology='smedge',
                                   WaitForJobID=dependent_job)
        process_info['file_out'] = transcript_file_out
        return process_info


def bat_scripts_dir():
    """
    returns location of the .bat scripts folder
    :return:
    """
    directory = __file__.split('cglumberjack')[0]
    return os.path.join(directory, 'cglumberjack', 'resources', 'bat_scripts')


def zip_bat_scripts():
    """
    makes a zip file of the .bat scripts to prepare it for upload to amazon s3
    :return:
    """
    from zipfile import ZipFile
    zip_file = os.path.join(bat_scripts_dir(), 'lumbermill_installer.zip')
    if os.path.exists(zip_file):
        os.remove(zip_file)
    zip = ZipFile(zip_file, 'w')
    for f in os.listdir(bat_scripts_dir()):
        filename = os.path.join(bat_scripts_dir(), f)
        if filename != zip_file:
            zip.write(filename, f)
    zip.close()
    return zip_file


def upload_lumbermill_installer_zip():
    """
    Creates a zip file of all the .bat scripts, uploads it to the cgl-developeronboarding bucket, the removes the
    zip file.
    :return:
    """
    path_ = zip_bat_scripts()
    print(path_)
    upload_file(path_, bucket_name='cgl-developeronboarding')
    os.remove(path_)


@click.command()
@click.option('--input_file', '-i', prompt="filepath to upload",
              default=None, help='Filepath for the file to upload to s3')
@click.option('--output_file', '-o', prompt='output file', default=False,
              help='where to write the transcript file')
@click.option('--bucket', '-b', prompt="s3 bucket name", default=None,
              help="")
def main(input_file, output_file, bucket):
    upload_and_transcribe_audio(input_file, output_file, bucket)


if __name__ == '__main__':
    # main()
    upload_lumbermill_installer_zip()
