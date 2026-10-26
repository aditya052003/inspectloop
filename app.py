import os
# Set decoder limits before importing cv2, including on Lambda cold starts.
os.environ.setdefault('OPENCV_IO_MAX_IMAGE_PIXELS','12000000')
import hmac
import uuid
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
import cv2
from demo import SCENARIOS, pair
from vision import decode, inspect
import storage

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024


@app.before_request
def authorize():
    if not request.path.startswith('/api/') or request.path=='/api/health':
        return
    expected = os.getenv('INSPECT_TOKEN','')
    if os.getenv('AWS_LAMBDA_FUNCTION_NAME') and not expected:
        return jsonify(error='Cloud access token is not configured.'),503
    if expected and not hmac.compare_digest(request.headers.get('X-Inspect-Token',''),expected):
        return jsonify(error='Enter the inspection access token.'),401


@app.after_request
def headers(response):
    response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'"
    return response


@app.get('/')
def home():
    return render_template('index.html',scenarios=SCENARIOS)


@app.get('/api/health')
def health():
    return jsonify(status='ok',opencv=cv2.__version__,storage='s3' if storage.bucket() else 'local',
                   runtime='aws-lambda' if os.getenv('AWS_LAMBDA_FUNCTION_NAME') else 'local')


@app.post('/api/inspect')
def run():
    if request.is_json:
        payload = request.get_json()
        if not isinstance(payload,dict):
            raise ValueError('Expected a JSON object.')
        scenario = payload.get('scenario','missing')
        reference,candidate = pair(scenario)
        source = 'synthetic demo: '+scenario
    else:
        if 'reference' not in request.files or 'candidate' not in request.files:
            raise ValueError('Choose both a reference and a candidate image.')
        reference = decode(request.files['reference'].read())
        candidate = decode(request.files['candidate'].read())
        source = 'user upload; not independently validated'
    report = inspect(reference,candidate)
    report.update(id=uuid.uuid4().hex,created_at=datetime.now(timezone.utc).isoformat(),source=source,human_review=None)
    storage.save(report)
    return jsonify(report)


@app.get('/api/reports/<report_id>')
def download(report_id):
    return jsonify(storage.read(report_id))


@app.post('/api/reports/<report_id>/review')
def review(report_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload,dict) or payload.get('decision') not in ('confirmed','dismissed'):
        raise ValueError('Choose confirmed or dismissed.')
    report = storage.read(report_id)
    if report['status']!='review':
        raise ValueError('Only flagged inspections can be reviewed.')
    if report['human_review'] is not None:
        return jsonify(error='This inspection has already been reviewed.'),409
    note = payload.get('note','')
    if not isinstance(note,str) or len(note)>1000:
        raise ValueError('Review note must be text under 1,000 characters.')
    report['human_review']={'decision':payload['decision'],'note':note,'at':datetime.now(timezone.utc).isoformat()}
    storage.save(report)
    return jsonify(report)


@app.errorhandler(Exception)
def error(exc):
    if isinstance(exc,HTTPException):
        return jsonify(error=exc.description),exc.code
    if isinstance(exc,(ValueError,cv2.error)):
        return jsonify(error=str(exc) if isinstance(exc,ValueError) else 'Image could not be processed. Use a smaller JPEG or PNG.'),400
    if isinstance(exc,FileNotFoundError):
        return jsonify(error='Report not found.'),404
    app.logger.exception('Inspection failed')
    return jsonify(error='Could not complete or save the inspection. Check server logs and storage configuration.'),500


if __name__=='__main__':
    app.run(host='127.0.0.1',port=5000,debug=False)
