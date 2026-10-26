# Deploy the actual inspection engine to AWS

**Status: deployment instructions and infrastructure are supplied; an AWS deployment has not been executed.** Local mocks do not prove AWS operation. Deployment provisions billable AWS resources. Choose your account and region, inspect the template, and set an AWS budget before deployment. Do not share AWS access keys with an assistant or commit them.

## Prerequisites
Install AWS CLI v2, AWS SAM CLI, and Docker Desktop. Start Docker Desktop using Linux containers. A Python 3.12 local install is useful for tests. Use an AWS profile with permission to deploy CloudFormation, IAM execution roles, Lambda, API Gateway, ECR and S3.

Authenticate with your normal AWS workflow, for example `aws configure sso` then `aws sso login --profile YOUR_PROFILE`. Set `AWS_PROFILE` for the terminal or pass the profile to SAM.

```powershell
$env:AWS_PROFILE = "YOUR_PROFILE"
aws sts get-caller-identity
sam validate --lint
sam build
sam deploy --guided
```

Suggested guided answers:
- Stack name: `inspectloop-demo`
- Region: `ap-south-1` (or your preferred supported region)
- InspectToken: a unique randomly generated string of at least 24 characters; keep it private.
- Confirm changes before deploy: Yes
- Allow SAM CLI IAM role creation: Yes, after reviewing the least-privilege template.
- Image repositories: allow SAM to create/manage the ECR repository if prompted.
- The API routes have no API Gateway authorizer: this prototype intentionally authenticates inspection/report routes inside Flask using the shared token. The UI and health endpoint are public. Review this before accepting any SAM prompt about unauthenticated routes.
- Do not commit SAM configuration files containing deployment parameters.

CloudFormation prints `Endpoint`, `EvidenceBucket`, and `FunctionName`. Open the endpoint and enter the token under **Protected deployment access**. Run the missing-component and blur scenarios.

The code performs OpenCV analysis inside the Lambda container; S3 is not merely a placeholder integration. AWS SDK credentials come from the function's role, not environment secrets. HTTP API v2 events are decoded by `lambda_handler.py`.

## Verify in AWS before claiming deployment
1. Load `ENDPOINT/api/health`. It must say `runtime: aws-lambda`, `storage: s3`, and an OpenCV version beginning with `5.`.
2. Run an inspection in the browser. Check reference, overlay, mask and trace.
3. Confirm a human review and export its report.
4. Verify a corresponding `reports/ID.json` object exists in the stack's private S3 bucket. Test retrieving the same report with the token.
5. In a terminal, call an inspection without the token; it must return 401.
6. Capture AWS console evidence showing the function, configuration, successful invocation and S3 object. Redact account identifiers and tokens.
7. Run the provided `cloud_check.py` against the endpoint to save a cloud verification report.

```powershell
$env:INSPECT_ENDPOINT = "https://YOUR_API.execute-api.YOUR_REGION.amazonaws.com"
$env:INSPECT_TOKEN = "YOUR_PRIVATE_DEMO_TOKEN"
.\.venv\Scripts\python.exe cloud_check.py
```

The script does one actual inspection and retrieves its persisted report. It also checks unauthenticated inspection is rejected. It writes `evaluation/cloud-verification.json` without the token. Keep the judge token private and share it separately from your code.

## Configuration and operational limits
- x86_64 Lambda, 2 GB memory, 28-second timeout, two reserved concurrent executions.
- OpenCV uses one thread per invocation.
- HTTP API throttles to 2 requests/second with a burst of 5.
- Application upload limit is 4 MB combined, leaving room for Lambda base64 event overhead.
- Private encrypted S3 evidence, lifecycle deletion after 30 days; the bucket is retained on stack deletion.
- Request bodies are not explicitly logged. Reports contain images. Use non-sensitive images with permission.
- This is a demo deployment: no per-user identities, distributed review lock, WAF or production SLA.
- A new AWS account may lack enough concurrency quota for reserved concurrency. If CloudFormation reports that issue, request quota or remove `ReservedConcurrentExecutions` after reviewing the resulting concurrency behavior.
- Cold starts and cloud latency are unmeasured until deployment. Do not reuse the local engine timing as AWS latency.

## Troubleshooting
- `sam build` needs Docker running and network access to ECR/PyPI.
- OpenCV major version mismatch intentionally fails at import; do not downgrade to OpenCV 4 for submission.
- 401: token missing or does not match the deployed parameter.
- 413: resize/compress the images.
- 500: inspect CloudWatch logs and the bucket/IAM configuration; the app will not silently claim persistence succeeded.
- Build failures on ARM laptops: build for linux/amd64 or use an x86_64 build machine, matching the template.

## Cleanup
Run `sam delete --stack-name inspectloop-demo` after judging, when you no longer need the endpoint. Because the evidence bucket is retained, separately review and delete its objects/bucket when no longer needed. Check ECR images and CloudWatch logs too. Do not delete resources that other projects depend on.
