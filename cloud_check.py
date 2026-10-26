import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime,timezone
from pathlib import Path

base=os.environ['INSPECT_ENDPOINT'].rstrip('/')
token=os.environ['INSPECT_TOKEN']
if not base.startswith('https://'):
    raise SystemExit('Use the HTTPS deployment endpoint.')

def call(path,payload=None,authenticated=True):
    headers={'Content-Type':'application/json'}
    if authenticated:headers['X-Inspect-Token']=token
    req=urllib.request.Request(base+path,data=json.dumps(payload).encode() if payload is not None else None,headers=headers)
    with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)

health=call('/api/health')
assert health['runtime']=='aws-lambda' and health['storage']=='s3' and health['opencv'].startswith('5.')
try:
    call('/api/inspect',{'scenario':'clean'},authenticated=False)
    raise RuntimeError('Unauthenticated inspection was not rejected.')
except urllib.error.HTTPError as e:
    assert e.code==401
start=time.perf_counter()
report=call('/api/inspect',{'scenario':'missing'})
wall=round((time.perf_counter()-start)*1000,1)
assert report['status']=='review'
stored=call('/api/reports/'+report['id'])
assert stored['id']==report['id'] and stored['trace']==report['trace']
result={'verified_at':datetime.now(timezone.utc).isoformat(),'endpoint':base,'health':health,'report_id':report['id'],'unauthenticated_inspection_status':401,'persisted_report_retrieved':True,'single_request_wall_ms':wall,'note':'One synthetic cloud smoke test, not a load benchmark. S3 verified through application retrieval; separately inspect the bucket.'}
Path('evaluation').mkdir(exist_ok=True)
Path('evaluation/cloud-verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
