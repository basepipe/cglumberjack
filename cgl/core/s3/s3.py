from __future__ import print_function
import os
from flask import Flask, request
import boto3
import base64
from Crypto.Cipher import AES
import re


os.environ['AWS_ACCESS_KEY_ID'] = "AKIAIT4HBNN4BK4SKIRA"
os.environ['AWS_SECRET_ACCESS_KEY'] = "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"

bucket = 'cgl-dev-test-storage'

app = Flask(__name__)

s_key = 'p3khVz6d6ZKXXqdE'


def hash(bucket_name, user):
    cat = (bucket_name+"^%^"+user).rjust(32)
    cipher = AES.new(s_key, AES.MODE_ECB)
    encoded = base64.b64encode(cipher.encrypt(cat))
    return encoded


def unhash(hash):
    cipher = AES.new(s_key, AES.MODE_ECB)
    return cipher.decrypt(base64.b64decode(hash)).strip()


b = "cgl-dev-test-storage"
u = "dave"
print(hash(b, u))


@app.route('/<path:h>', methods=['GET', 'POST'])
def index(h):
    uh = unhash(h).split("^%^")
    s3 = boto3.resource('s3')
    b = s3.Bucket(uh[0])
    fstr = ""
    for obj in b.objects.filter(Prefix='users/' + uh[1] + "/uploads/"):
        fstr += obj.key + "<br />"

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
    bucket_name, user = unhash(re.escape(request.form['hash'])).split("^%^")
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

    fb = '<form action="/'+h+'/"> <input type="submit" value="Return" /> </form>'

    return '<h1>Thanks %s, the following file(s) have been uploaded to %s: %s</h1>' % (user, bucket_name.replace('cgl-', ''), ret) + fb


if __name__ == '__main__':
    app.run(debug=True)
