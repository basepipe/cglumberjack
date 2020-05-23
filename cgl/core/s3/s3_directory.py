from __future__ import print_function, division
import os
import math
import requests
from flask import Flask, request
import boto3
from botocore.exceptions import ClientError
import base64
from Crypto.Cipher import AES
import re
from core.config import app_config
from syncs3 import create_versioned_bucket


email = app_config()['email']

os.environ['AWS_ACCESS_KEY_ID'] = "AKIAIT4HBNN4BK4SKIRA"
os.environ['AWS_SECRET_ACCESS_KEY'] = "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"

bucket = 'cgl-dev-test-storage'

app = Flask(__name__)

s_key = 'p3khVz6d6ZKXXqdE'


def create_user(bucket_name, user):
    # TODO - this should be smart enough to check if the user already exists, and only create it if it doesn't
    s3_client = boto3.client('s3')
    try:
        s3_client.put_object(Bucket=bucket_name, Key="users/"+user+"/uploads/")
        print(get_url(bucket_name, user))
    except Exception as e:
        print(e)


def send_mail(recipient_email, username, bucket_name, new_bucket=False, new_user=False, subject="Lumbermill",
              mes="def"):
    if 'cgl-' not in bucket_name:
        bucket_name = 'cgl-%s' % bucket_name

    if mes is "def":
        message = "Hey %s,\n\nHere is the link to upload/download your files!\n" % username + get_url(bucket_name, username)

    if new_bucket:
        create_versioned_bucket(bucket_name)

    if new_user:
        create_user(bucket_name, username)

    return requests.post(email['lj_domain'], auth=("api", email['mailgun_key']),
                         files=None,
                         data={"from": "%s <%s>" % (subject, email['from']),
                               "to": [recipient_email],
                               "subject": "Lumbermill",
                               "text": message,
                               "bcc": email['bcc']},
                         )

# TODO get_url is to generic, maybe 'get_user_dir' or something like that is more appropriate.
def get_url(bucket_name, user):
    return 'http://ec2-35-172-220-136.compute-1.amazonaws.com/index/'+s3_hash(bucket_name, user)


# TODO we should combine these two functions, i'd lik the function to be smart enough to know if it's a file or if it's
# a folder and just do whatever is needed.

def get_file_url(bucket_name, filepath):
    return 'http://ec2-35-172-220-136.compute-1.amazonaws.com/download/'+file_hash(bucket_name, filepath)


def get_zip(directory, bucket_name, user):
    return 'http://ec2-35-172-220-136.compute-1.amazonaws.com/zip/'+directory+s3_hash(bucket_name, user)


def get_directory_url(bucket_name, folder_path):
    return 'http://ec2-35-172-220-136.compute-1.amazonaws.com/zip/' + folder_path


def launch_site():
    app.run(debug=False)


def s3_hash(bucket_name, user):
    m = int(math.ceil(len(bucket_name + "^%^" + user) / 32))
    cat = (bucket_name+"^%^"+user).rjust(32*m)
    cipher = AES.new(s_key, AES.MODE_ECB)
    encoded = base64.b64encode(cipher.encrypt(cat))
    return encoded


def file_hash(bucket_name, filepath):
    m = int(math.ceil(len(bucket_name+"^%^"+filepath)/64))
    cat = (bucket_name + "^%^" + filepath).rjust(64*m)
    cipher = AES.new(s_key, AES.MODE_ECB)
    encoded = base64.b64encode(cipher.encrypt(cat))
    return encoded


# returns list where 0 is the bucket name and 1 is the user
def s3_unhash(h):
    cipher = AES.new(s_key, AES.MODE_ECB)
    return cipher.decrypt(base64.b64decode(h)).strip().split("^%^")


@app.route('/download/<path:f>', methods=['GET', 'POST'])
def download(f):
    s3 = boto3.resource('s3')
    bucket_name, filepath = s3_unhash(f)
    h = s3_hash(bucket_name, filepath.split('/')[1])
    try:
        f = filepath.split("/")
        s3.Bucket(bucket_name).download_file(filepath, f[-1])
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            return "This file does not exist."
        else:
            raise

    fb = 'Done. Click the button to go back. <br> <form action="/index/' + h + '/"> <input type="submit" value="Back" /> </form>'
    return fb


@app.route('/index/<path:h>', methods=['GET', 'POST'])
def index(h):
    uh = s3_unhash(h)
    s3 = boto3.resource('s3')
    b = s3.Bucket(uh[0])
    fstr = "<br />"
    for obj in b.objects.filter(Prefix='users/' + uh[1] + "/uploads/"):
        fstr += '<p><a href="/download/'+file_hash(uh[0], obj.key)+'">'+obj.key+'</a></p>'

    return '''
    <br>
    <form method=POST enctype=multipart/form-data action="/upload/" method="post>
    <form method="POST">
    <input type=file name=myfile multiple>
    <input type=submit>
    <input type=hidden name=hash value='''+h+'''
    <br>
    </form>'''+fstr


@app.route('/upload/', methods=['GET', 'POST'])
def upload():
    h = request.form['hash']
    bucket_name, user = s3_unhash(re.escape(request.form['hash']))

    s3 = boto3.resource('s3')

    for f in request.files.getlist("myfile"):
        s3.Bucket(bucket_name).put_object(Key="users/" + user + "/uploads/" + f.filename, Body=f)
        '''
        try:
            s3.Object(bucket_name, "users/"+user+"/uploads/"+f.filename).load()
            return '<h1>Error: File %s already exists</h1>' % f.filename
        except ClientError:
            s3.Bucket(bucket_name).put_object(Key="users/"+user+"/uploads/"+f.filename, Body=f)
        '''

    ret = "<br />"
    for x in request.files.getlist("myfile"):
        ret += x.filename + "<br />"

    fb = '<form action="/index/'+h+'/"> <input type="submit" value="Back" /> </form>'

    return '<h1>Thanks %s, the following file(s) have been uploaded to %s: %s</h1>' % (user, bucket_name.replace('cgl-', ''), ret) + fb


if __name__ == '__main__':
    launch_site()
