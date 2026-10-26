import base64
import io
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
import pytest
from app import app
from demo import pair
from vision import inspect
from lambda_handler import handler

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('DATA_DIR',str(tmp_path))
    monkeypatch.delenv('REPORT_BUCKET',raising=False)
    monkeypatch.delenv('INSPECT_TOKEN',raising=False)
    monkeypatch.delenv('AWS_LAMBDA_FUNCTION_NAME',raising=False)
    return app.test_client()

@pytest.mark.parametrize('scenario,expected',[('clean','clear'),('missing','review'),('scratch','review'),('shifted','clear'),('dim','review'),('blur','retake'),('dark','retake'),('wrong','retake')])
def test_decision_paths(scenario,expected):
    result=inspect(*pair(scenario,seed=17))
    assert result['status']==expected
    if scenario=='dim':
        assert 'exposure_recovery' in [s['tool'] for s in result['trace']]
    if expected=='review':
        assert result['regions']
        assert 'roi_refinement' in [s['tool'] for s in result['trace']]


def test_review_persist_export(client):
    result=client.post('/api/inspect',json={'scenario':'missing'})
    assert result.status_code==200
    report=result.get_json(); path='/api/reports/'+report['id']
    reviewed=client.post(path+'/review',json={'decision':'confirmed','note':'Component absent'})
    assert reviewed.status_code==200
    assert client.get(path).get_json()['human_review']['decision']=='confirmed'
    assert client.post(path+'/review',json={'decision':'dismissed'}).status_code==409


def test_upload(client):
    ref,test=pair('missing')
    result=client.post('/api/inspect',data={name:(io.BytesIO(cv2.imencode('.png',im)[1].tobytes()),name+'.png') for name,im in [('reference',ref),('candidate',test)]})
    assert result.status_code==200
    assert result.get_json()['status']=='review'


def test_bad_inputs(client):
    assert client.post('/api/inspect',json={'scenario':'nonexistent'}).status_code==400
    assert client.post('/api/inspect',json=[]).status_code==400
    assert client.post('/api/inspect',data={'reference':(io.BytesIO(b'bad'),'bad.png'),'candidate':(io.BytesIO(b'bad'),'bad.png')}).status_code==400
    assert client.get('/api/reports/not-an-id').status_code==400
    assert client.get('/api/reports/'+'0'*32).status_code==404
    assert client.post('/api/inspect',data=b'x'*(4*1024*1024+1),content_type='application/json').status_code==413


def test_auth(client,monkeypatch):
    monkeypatch.setenv('INSPECT_TOKEN','test-token')
    assert client.post('/api/inspect',json={}).status_code==401
    assert client.post('/api/inspect',json={},headers={'X-Inspect-Token':'test-token'}).status_code==200
    assert client.get('/api/reports/'+'0'*32).status_code==401


def test_cloud_fails_closed(client,monkeypatch):
    monkeypatch.setenv('AWS_LAMBDA_FUNCTION_NAME','test')
    assert client.post('/api/inspect',json={}).status_code==503


def test_lambda_json_and_assets(client):
    for path in ['/','/static/style.css','/static/app.js','/api/health']:
        result=handler({'rawPath':path,'requestContext':{'http':{'method':'GET'}}},None)
        assert result['statusCode']==200
        assert base64.b64decode(result['body'])
    result=handler({'rawPath':'/api/inspect','requestContext':{'http':{'method':'POST'}},'headers':{'content-type':'application/json'},'body':json.dumps({'scenario':'scratch'})},None)
    assert json.loads(base64.b64decode(result['body']))['status']=='review'


def test_lambda_multipart(client):
    from werkzeug.test import EnvironBuilder
    ref,test=pair('clean')
    b=EnvironBuilder(method='POST',data={n:(io.BytesIO(cv2.imencode('.png',im)[1].tobytes()),n+'.png') for n,im in [('reference',ref),('candidate',test)]})
    env=b.get_environ()
    result=handler({'rawPath':'/api/inspect','requestContext':{'http':{'method':'POST'}},'headers':{'content-type':env['CONTENT_TYPE']},'body':base64.b64encode(env['wsgi.input'].read()).decode(),'isBase64Encoded':True},None)
    assert result['statusCode']==200
    assert json.loads(base64.b64decode(result['body']))['status']=='clear'
    b.close()


def test_bad_reference_and_shape():
    ref,test=pair('clean')
    assert inspect(cv2.GaussianBlur(ref,(25,25),7),test)['status']=='retake'
    assert inspect(ref,np.zeros((300,300,3),np.uint8))['status']=='retake'
