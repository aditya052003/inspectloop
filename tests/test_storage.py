import io
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import boto3
from botocore.stub import Stubber, ANY
import storage


def test_private_s3_roundtrip(monkeypatch):
    client=boto3.client('s3',region_name='ap-south-1',aws_access_key_id='testing',aws_secret_access_key='testing')
    stub=Stubber(client)
    report={'id':'a'*32,'status':'review'}
    stub.add_response('put_object',{}, {'Bucket':'test-evidence','Key':'reports/'+'a'*32+'.json','Body':ANY,'ContentType':'application/json','ServerSideEncryption':'AES256'})
    stub.add_response('get_object',{'Body':io.BytesIO(json.dumps(report).encode())},{'Bucket':'test-evidence','Key':'reports/'+'a'*32+'.json'})
    monkeypatch.setenv('REPORT_BUCKET','test-evidence')
    monkeypatch.setattr(boto3,'client',lambda service:client)
    with stub:
        storage.save(report)
        assert storage.read(report['id'])==report
    stub.assert_no_pending_responses()
