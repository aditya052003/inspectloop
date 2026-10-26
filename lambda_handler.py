"""HTTP API v2 adapter; tested locally with base64 multipart and static assets."""
import base64
from app import app


def handler(event, context):
    method = event.get('requestContext',{}).get('http',{}).get('method','GET')
    path = event.get('rawPath','/')
    query = event.get('rawQueryString','')
    body = event.get('body') or ''
    body = base64.b64decode(body) if event.get('isBase64Encoded') else body.encode()
    headers = {k:v for k,v in event.get('headers',{}).items() if k.lower() not in ('host','content-length')}
    with app.test_client() as client:
        response = client.open(path+('?' + query if query else ''),method=method,headers=headers,data=body)
        return {'statusCode':response.status_code,'headers':dict(response.headers),
                'body':base64.b64encode(response.data).decode(),'isBase64Encoded':True}
