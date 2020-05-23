"""
AWS S3 Sync Tool

ASSUMPTIONS

A.  This tools assumes API Keys have been set as described here:
http://boto3.readthedocs.io/en/latest/guide/configuration.html
Often the easiest method is to export the API Keys in the Environment.

On OS X/Linux:

```
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
```
on Windows:

```
set AWS_ACCESS_KEY_ID=xxx
set AWS_SECRET_ACCESS_KEY=xxx
```

B.  YOU HAVE INSTALLED VIA requirements-cli.txt

```
pip install -r requirements-cli.txt
```


To use this as a Library would be something like this:

In [1]: from syncs3 import list_bucket_objects

In [2]: list_bucket_objects()
{"message": "Creating s3 client"}
{"message": "Found credentials in environment variables."}
{"message": "List bucket objects [cgl-test-folder]"}
{"message": "Starting new HTTPS connection (1): cgl-test-folder.s3.amazonaws.com"}
Out[2]:
[s3.ObjectSummary(bucket_name='cgl-test-folder', key=u'level1.txt'),
 s3.ObjectSummary(bucket_name='cgl-test-folder', key=u'level2/level2.txt'),
 s3.ObjectSummary(bucket_name='cgl-test-folder', key=u'stuff-for-tom.txt')]


NEW BUCKET SYNC WORKFLOW FROM LIBRARY

1. Make a versioned bucket

```
create_versioned_bucket(bucket_name="cgl-your-new-bucket-name")
```

2.  Sync from directory on file system

```
sync_bucket(delete=False, folder="test-folder", bucket="s3://cgl-your-new-bucket-name")
```

3.  Verify assets synced by listing objects in bucket

```
list_bucket_objects(bucket_name="cgl-your-new-bucket-name")
```

NEW BUCKET SYNC WORKFLOW FROM COMMANDLINE

1.  Make a versioned bucket

```

{"message": "Creating s3 resource"}
{"message": "Found credentials in environment variables."}
{"message": "Creating bucket with name [cgl-your-new-bucket-name]"}
{"message": "Starting new HTTPS connection (1): cgl-your-new-bucket-name.s3.amazonaws.com"}
{"message": "s3.Bucket(name=u'cgl-your-new-bucket-name')"}
{"message": "Enabling Bucket Version for bucket_name [cgl-your-new-bucket-name]"}

```

2. Sync folder to bucket

```
python syncs3.py sync --bucket s3://cgl-your-new-bucket-name --folder test-folder
```


3.  Verify assets in bucket (Note s3:// not in name)

```
python syncs3.py listbucket --bucket cgl-your-new-bucket-name
```

"""

import logging
import subprocess
import platform
import os

import boto3
import click
from pythonjsonlogger import jsonlogger
import pandas as pd

VERSION = "1"
LOG = logging.getLogger()
LOG_HANDLER = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
LOG_HANDLER.setFormatter(formatter)
LOG.addHandler(LOG_HANDLER)
LOG.setLevel(logging.INFO)
VERSION_MSG = "VERSION %s" % (VERSION)
LOG.info(VERSION_MSG)


### START:  Local File System Utils ####

def local_tree_dataframe(folder):
    """Converts a local tree on disk to a Pandas DataFrame
    In [1]: from syncs3 import local_tree_dataframe

    In [2]: pd = local_tree_dataframe("test-folder/")

    In [3]: print(pd)
    Out[3]:
         filename                                           fullpath
    0  level1.txt  /Users/noahgift/src/core_tools/test-folder/lev...
    1  level2.txt  /Users/noahgift/src/core_tools/test-folder/lev...

    """
    
    data = []
    msg = "Generating Pandas DataFrame from folder: %s" % folder
    LOG.info(msg)
    for root,_, files in os.walk("test-folder"):
        for filename in files:
            fullpath = os.path.join(os.path.abspath(root), filename)
            last_modified = os.path.getmtime(fullpath)
            data.append((filename,fullpath, last_modified))
    return pd.DataFrame(data, columns=['filename', 'fullpath', "last-modified"])


def local_tree_describe(folder):
    """Generates descriptive statistics about local file system
    In [2]: from syncs3 import local_tree_describe

    In [3]: out = local_tree_describe("test-folder/")

    In [4]: print(out)
              filename                                           fullpath
    count            2                                                  2
    unique           2                                                  2
    top     level1.txt  /Users/noahgift/src/core_tools/test-folder/lev...
    freq             1                                                  1

    
    """

    df = local_tree_dataframe(folder)
    description = df.describe()
    return description

### END:  Local File System Utils ####


def run(cmd):
    """Run command"""

    p = subprocess.Popen(cmd)
    log_msg = "Running CMD: %s" % cmd
    LOG.info(log_msg)
    return p.wait()


def create_versioned_bucket(bucket_name="cgl-test-folder"):
    """Creates an S3 bucket with Versioning Enabled"""

    LOG.info("Creating s3 resource")
    s3 = boto3.resource("s3")
    log_msg = "Creating bucket with name [%s]" % bucket_name
    LOG.info(log_msg)
    result = s3.create_bucket(Bucket=bucket_name)
    LOG.info(result)
    bucket_versioning = s3.BucketVersioning(bucket_name)
    log_bucket_msg = "Enabling Bucket Version for bucket_name [%s]" % bucket_name
    LOG.info(log_bucket_msg)
    version_result = bucket_versioning.enable()
    LOG.info(version_result)
    return result


def list_bucket_objects(bucket_name="cgl-test-folder"):
    """List contents of bucket"""

    LOG.info("Creating s3 client")
    s3 = boto3.resource("s3")
    log_msg = "List bucket objects [%s]" % bucket_name
    LOG.info(log_msg)
    bucket = s3.Bucket(bucket_name)
    files = list(bucket.objects.all())
    return files


def list_bucket_versions(bucket_name="cgl-test-folder"):
    """List versions of bucket as pandas DataFrame

    Usage Example:

    In [2]: df = list_bucket_versions()
    {"message": "Creating s3 client"}
    {"message": "Found credentials in environment variables."}
    {"message": "List bucket versions [cgl-test-folder]"}
    {"message": "Starting new HTTPS connection (1): cgl-test-folder.s3.amazonaws.com"}

    In [3]: print(df)
            bucket_name               file                        version_id  \
    0   cgl-test-folder       level1-2.txt  166yjqw7Q9HH4ZFOdpvgrc.sABGtlHyC
    1   cgl-test-folder         level1.txt  JajZatpA.W00HMZoDZn81uIMHiU76noX
 
                   last_modified
    0   Mon May 14 20:10:24 2018
    1   Mon May 14 20:55:32 2018
    
    """

    data = []
    LOG.info("Creating s3 client")
    s3 = boto3.resource("s3")
    log_msg = "List bucket versions [%s]" % bucket_name
    LOG.info(log_msg)
    bucket = s3.Bucket(bucket_name)
    versions = list(bucket.object_versions.all())
    for version in versions:
        data.append((version.bucket_name, version.object_key, version.id, version.last_modified.ctime()))
    return pd.DataFrame(data, columns=['bucket_name', 'file', "version_id", "last_modified"])


def sync_bucket(folder="test-folder",
        bucket="s3://cgl-test-folder",
        delete=False,
        pull=False):
    """Syncs Directory to S3 Bucket
    
    Handles Windows by finding AWS Executable and giving it a different path
    """
    #Log message designating delete or non-delete sync
    delete_msg = "DESTRUCTIVE SYNC ENABLED: [%s]" % delete
    non_delete_msg = "NON-DESTRUCTIVE SYNC ENABLED: [%s]" % delete

    #Detect if windows
    if platform.system() == "Windows":
        LOG.info("Running Windows Sync Version")
        import win32api #pylint: disable=import-error
        _, aws_executable = win32api.FindExecutable("aws")  # requires aws-cli windows installer.
        if delete:
            LOG.info(delete_msg)
            result = run([aws_executable, "s3", "sync", "--delete", folder, bucket])
        else:
            LOG.info(non_delete_msg)
            if not pull:
                result = run([aws_executable, "s3", "sync", folder, bucket])
            #Pull local
            else:
                LOG.info("PULL LOCAL MODE")
                result = run([aws_executable, "s3", "sync", bucket, folder])
    #If not windows assume OS X or Linux
    else:
        if delete:
            LOG.info(delete_msg)
            result = run(["aws", "s3", "sync", "--delete", folder, bucket])
        else:
            LOG.info(non_delete_msg)
            if not pull:
               result = run(["aws", "s3", "sync", folder, bucket])
            #Pull local
            else:
               LOG.info("PULL LOCAL MODE")
               result = run(["aws", "s3", "sync", bucket, folder])
    return result

@click.group()
@click.version_option(VERSION)
def cli():
    """S3 Sync Utility"""

@cli.command("sync")
@click.option("--folder", default="test-folder",
              help="Folder to sync to a bucket")
@click.option("--bucket", default="s3://cgl-test-folder",
              help="S3 Bucket Name")
@click.option("--delete", default=False,
              help="Destructive sync")
@click.option("--pull", default=False,
              help="Pull based sync")
def sync(folder, bucket, delete, pull):
    """Syncs a local folder to Amazon S3

    python syncs3.py --folder test-folder --bucket test-folder

    To run destructive sync do:
        
        python syncs3.py sync --delete=True

    To run pull:
    
        python syncs3.py sync --pull=True

    """

    result = sync_bucket(folder=folder, bucket=bucket, delete=delete, pull=pull)
    click.echo("CLI Command:  Running Sync for folder: %s to bucket: %s with result: %s" % (folder,bucket,result))

@cli.command("createbucket")
@click.option("--bucket", default="cgl-test-folder",
              help="creates versioned s3 bucket")
def createbucket(bucket):
    """Create Versioned S3 bucket

    python syncs3.py --createbucket cgl-test-folder

    """

    create_versioned_bucket(bucket_name=bucket)


@cli.command("listbucket")
@click.option("--bucket", default="cgl-test-folder",
              help="lists the contents of a s3 bucket")
def listbucket(bucket):
    """
    List contents of Amazon S3 bucket
    python syncs3.py --listbucket cgl-test-folder
    """
    items = list_bucket_objects(bucket)
    for item in items:
        click.echo("Found item: %s" % item)


@cli.command("tree")
@click.option("--describe", default="test-folder",
              help="lists the contents of a s3 bucket")
@click.option("--display", default=False,
            help="prints Tree of files and paths locally as a DataFrame")
def tree(describe, display):
    """Describe statistics about Local Tree

    python syncs3.py tree --describe test-folder

    or for stats and tree print

    python syncs3.py tree --display=True
    {"message": "VERSION 1"}
         filename                                           fullpath
    0  level1.txt  /Users/noahgift/src/core_tools/test-folder/lev...
    1  level2.txt  /Users/noahgift/src/core_tools/test-folder/lev...
    Summary Statistics for Local Tree: test-folder
               filename                                           fullpath
    count            2                                                  2
    unique           2                                                  2
    top     level1.txt  /Users/noahgift/src/core_tools/test-folder/lev...
    freq             1



    """
    if display:
        pd = local_tree_dataframe(describe)
        click.echo(pd)
    
    stats = local_tree_describe(describe)
    click.echo("Summary Statistics for Local Tree: %s \n %s" %\
        (describe, stats))

@cli.command("versions")
@click.option("--describe", default="cgl-test-folder",
              help="lists the versions of a s3 bucket")
@click.option("--display", default=False,
            help="prints Tree of files and paths locally as a DataFrame")
def versions(describe, display):
    """Describe statistics about Local Tree
    python syncs3.py versions --describe cgl-test-folder
    or for stats and versions print
    python syncs3.py versions --display=True

    """
    if display:
        pd = list_bucket_versions(describe)
        click.echo(pd.describe())
    
    stats = list_bucket_versions(describe)
    click.echo(" S3 Versions for bucket: %s \n %s" %\
        (describe, stats))

if __name__ == "__main__":
    cli()



