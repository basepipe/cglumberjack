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
from cgl.core.utils.general import save_json
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
