import json
import os
import re
from pathlib import Path
from botocore.exceptions import ClientError


def bucket():
    return os.getenv('REPORT_BUCKET')


def key(report_id):
    if not re.fullmatch(r'[a-f0-9]{32}',report_id):
        raise ValueError('Invalid report ID.')
    return f'reports/{report_id}.json'


def save(report):
    name = key(report['id'])
    if bucket():
        import boto3
        boto3.client('s3').put_object(Bucket=bucket(),Key=name,Body=json.dumps(report).encode(),ContentType='application/json',ServerSideEncryption='AES256')
    else:
        target = Path(os.getenv('DATA_DIR','data'))/name
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps(report),encoding='utf-8')
        temporary.replace(target)


def read(report_id):
    name = key(report_id)
    if bucket():
        import boto3
        try:
            return json.loads(boto3.client('s3').get_object(Bucket=bucket(),Key=name)['Body'].read())
        except ClientError as e:
            if e.response['Error']['Code'] in ('NoSuchKey','404'):
                raise FileNotFoundError from e
            raise
    return json.loads((Path(os.getenv('DATA_DIR','data'))/name).read_text(encoding='utf-8'))
