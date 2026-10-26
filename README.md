# InspectLoop: Evidence Before Action

### See the change. Check the evidence. Keep people in control.

**InspectLoop turns a reference photo and a candidate photo into an explainable inspection report—with OpenCV 5, human review, and AWS evidence storage.**

A missing part can be easy to overlook. A shadow or a shifted camera can also look like a defect. InspectLoop checks capture quality, attempts exposure recovery and alignment, highlights candidate changes, and gives a reviewer the evidence needed to decide what happened.

**[Try the live application](https://620mowl7mj.execute-api.ap-south-1.amazonaws.com)** · **[Explore the source](https://github.com/aditya052003/inspectloop)** · **[Technical report](docs/TECHNICAL_REPORT.md)** · **[Architecture](docs/ARCHITECTURE.md)**

**Built with:** OpenCV 5 · Python · Flask · Docker · AWS Lambda · API Gateway · Amazon S3 · AWS SAM

## The problem and intended impact

Small workshops and assembly teams need a practical way to compare an item against a known reference and document what a reviewer found. An inspection result is more useful when it includes the location of a change, the quality of the input images, and the final human decision.

InspectLoop explores that workflow without requiring a trained defect model. Its intended benefit is more consistent review and clearer records of suspected missing parts or visible changes. Measuring time savings and manufacturing impact requires a future field study; this submission is a working research prototype.

## What makes InspectLoop useful

| Design choice | Why it matters |
| --- | --- |
| Capture-quality checks before comparison | An unsuitable image can trigger a retake instead of a misleading comparison |
| Exposure recovery and geometric alignment | Addresses common capture variation before looking for changes |
| Measured evidence for each decision | Reviewers can inspect the basis for a result rather than receiving an unexplained label |
| Human confirmation linked to the report | Connects a visual finding to a recorded review decision |
| Local execution and AWS deployment | Supports a local demonstration and a hosted inspection workflow using the same core pipeline |

The contribution is the integration of capture checks, recovery, comparison, and documented human review. It uses established computer-vision methods; it does not claim a new detection algorithm.

## Evidence at a glance

- **Deployed:** AWS Lambda application with API Gateway and S3 report storage.
- **Access checked:** an unauthenticated inspection request returned HTTP 401.
- **Persistence checked:** a stored cloud report was retrieved through the application.
- **Real-photo demonstration:** the removed eraser area was highlighted; additional background and alignment flags remained.
- **Human review demonstrated:** a confirmation was saved and recorded in the exported report.
- **Reproducible source:** pinned dependencies, Docker build, SAM template, automated tests, and synthetic evaluation fixtures are included.

See [verification and observed results](#verification-and-observed-results) for measurements and their limits. Synthetic demonstrations and the development photo pair are not an independent industrial accuracy study.

## Judge walkthrough — about two minutes

1. Open the live application.
2. Expand **Protected deployment access** and enter the inspection access token supplied separately by the project owner.
3. Select **Sample inspection → Missing component**, then click **Run inspection**.
4. Compare the reference and candidate using **Overlay**, **Original**, and **Difference mask**.
5. Expand the measured evidence under **How the decision was made**.
6. Add a review note, choose **Confirm defect** or **Dismiss as acceptable**, and download the JSON evidence report.

The hosted inspection, report retrieval, and review endpoints require a shared demo token. Do not publish this token in GitHub, screenshots, or videos. For competition access, supply it through the private Devpost testing instructions.

The included assembly demonstrations are procedurally generated synthetic images. They demonstrate workflow behavior, not real-world accuracy.

## What it does

- Compares reference and candidate JPEG/PNG uploads, with file-size and content validation.
- Measures reference and candidate capture quality before comparison.
- Attempts moderate underexposure recovery when appropriate.
- Aligns images using OpenCV ORB features and RANSAC-based affine estimation.
- Produces difference masks and bounding boxes around candidate change regions.
- Routes results to **No significant change**, **Needs review**, or **Retake required**.
- Shows the measured evidence behind inspection decisions.
- Records human review and exports JSON reports containing normalized images, measurements, timing, and review information.
- Stores reports locally or in private Amazon S3 storage.

The application does not identify semantic defect types or automatically reject products. A highlighted region is a visual difference that needs interpretation.

## How the inspection works

1. **Reference quality:** check that the reference is suitable for comparison.
2. **Capture quality:** measure brightness, sharpness, and clipping; recover exposure or request a retake where appropriate.
3. **Alignment:** match ORB features and estimate a partial affine transform with RANSAC. Check alignment quality and shared image coverage.
4. **Difference map:** compare aligned grayscale images with brightness correction and filtering, excluding invalid overlap areas.
5. **Region refinement:** group supported changes into candidate regions.
6. **Decision and review:** present evidence, request human review when changes are found, and persist the review outcome.

The decision controller is deterministic. There is no LLM, trained neural network, or downloaded model in this implementation.

## Local setup

Use **Python 3.12**. Local use does not require Node.js, MongoDB, Docker, or an AWS account.

Clone the repository, or download and extract its source:

```bash
git clone https://github.com/aditya052003/inspectloop.git
cd inspectloop
```

### Windows — PowerShell

Run these commands in the folder containing `app.py`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:5000** and keep the terminal running. Press **Ctrl+C** to stop the server. Virtual-environment activation is unnecessary when using the explicit Python path above.

For later launches:

```powershell
.\.venv\Scripts\python.exe app.py
```

If the Python launcher cannot find version 3.12, install Python 3.12 before creating the environment.

### macOS / Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Open **http://127.0.0.1:5000**. The local Flask development server is intended for local use.

## Sample scenarios

| Scenario | Purpose |
| --- | --- |
| Clean | Demonstrate comparison without an introduced defect |
| Missing component | Highlight an intentionally removed component |
| Scratch | Demonstrate a visible surface change |
| Camera shifted | Demonstrate registration for small camera movement |
| Dim capture + defect | Demonstrate exposure recovery before comparison |
| Out of focus | Demonstrate a capture-quality retake decision |
| Extreme darkness | Demonstrate rejection of an unsuitable capture |
| Wrong reference | Demonstrate an unsuitable comparison pair |

For uploads, use the same scene and product arrangement with consistent framing and lighting. A fixed camera and textured fixture help alignment. Unrelated stock images are not a valid evaluation of this comparison method.

## AWS deployment

The application has been deployed in **ap-south-1** using:

| Service / tool | Role |
| --- | --- |
| AWS Lambda | Runs the containerized Python/OpenCV application |
| Amazon API Gateway HTTP API | Provides the HTTPS endpoint |
| Amazon ECR | Stores the application container image |
| Amazon S3 | Stores inspection evidence reports |
| AWS SAM / CloudFormation | Defines and deploys infrastructure |
| Docker | Builds the Lambda container image |

The deployment template includes private S3 storage, encryption, a report lifecycle policy, API throttling, and application-level token protection for inspection/report operations.

See **[AWS deployment instructions](docs/AWS_DEPLOYMENT.md)** for configuration. With AWS credentials and the build tools configured, the basic workflow is:

```bash
sam build
sam validate --region ap-south-1
sam deploy --guided --region ap-south-1
```

Choose an inspection token privately when prompted. Deployment creates AWS resources and can incur charges. The shared application token is not a replacement for production identity management or per-user authorization.

## Verification and observed results

These are development checks and individual demonstrations, not independent accuracy or load benchmarks.

| Check | Observed result | Interpretation |
| --- | --- | --- |
| Cloud health | OpenCV `5.0.0`, runtime `aws-lambda`, storage `s3`, status `ok` | Confirms the reported deployed runtime |
| Unauthenticated inspection | HTTP `401` | Checked access rejection for one inspection request |
| Persisted cloud report | Successfully retrieved through the application | Application-level persistence check; not a separate bucket audit |
| Synthetic cloud smoke test | One request took `431.7 ms` wall time | A single observation, not a latency guarantee |
| Real-photo missing-eraser example | `17` flagged regions; `3.188%` changed area; `2772 ms` reported engine time | Missing-eraser area highlighted, with extra background/alignment flags |
| Human review | UI displayed `Review saved: confirmed`; exported report recorded the review | Demonstrates the review workflow |
| Identical-photo comparison | `0` flagged regions; `0%` changed area; `94.4 ms` reported engine time | A basic consistency check, not a separately captured unchanged-scene test |

**17 flagged regions does not mean 17 defects.** The real-photo example contained one intentionally removed eraser and additional nuisance flags. Changed-area percentage is not an accuracy score. Engine timing and end-to-end request timing measure different things and should not be compared directly.

The real-photo pair also exposed a portrait-image alignment limitation. The alignment check was updated to normalize translation by image diagonal and check shared overlap. This pair was used during development, so it is not a held-out evaluation example.

## Tests and development evaluation

### Windows

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe evaluate.py
```

### macOS / Linux

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/python evaluate.py
```

The automated tests cover application and storage behavior, including pipeline routing, authentication, human review, Lambda event adaptation, and mocked S3 interactions. Use the test output from your checkout for its current test count and results.

The `evaluation/` directory contains development outputs, including synthetic results, traces, explicit failure cases, and cloud verification evidence. The 80 synthetic fixtures are correlated procedural variants used during development. Their routing results must not be presented as real-world accuracy. Saved evaluation artifacts may reflect an earlier development revision; rerunning the evaluator produces results for the current checkout.

No independent held-out real-photo study, simple-comparison baseline study, load benchmark, or completed mobile-usability evaluation is claimed.

## Repository structure

| Path | Purpose |
| --- | --- |
| `app.py` | HTTP routes, upload validation, authentication, and review |
| `vision.py` | OpenCV inspection pipeline and decision policy |
| `demo.py` | Procedural demonstration generator |
| `storage.py` | Local and S3 report persistence |
| `lambda_handler.py` | API Gateway HTTP API v2 adapter |
| `templates/`, `static/` | Browser interface |
| `template.yaml`, `Dockerfile` | AWS infrastructure and container build |
| `requirements.txt` | Pinned application dependencies |
| `requirements-dev.txt` | Development/test dependencies |
| `tests/` | Automated tests |
| `evaluate.py`, `generate_samples.py` | Development evaluation and sample generation |
| `evaluation/` | Saved results, traces, failure cases, and cloud check output |
| `samples/` | Original synthetic images for demonstrations and uploads |
| `cloud_check.py` | Cloud smoke-check script |
| `docs/` | Technical report, architecture, deployment guide, demo script, and checklist |

## Storage, privacy, and responsible operation

- Local reports are stored in `data/reports/` and include normalized images. Treat them as private.
- Delete local report files when they are no longer needed. The cloud template configures report expiry after 30 days through S3 lifecycle rules.
- Reloading the page clears UI state, but does not delete persisted reports. Keep an exported report or its ID if needed; there is no report-history browser.
- Hosted inspection, report retrieval, and review require `INSPECT_TOKEN`. Local mode binds to localhost and is unauthenticated unless the token environment variable is set.
- Do not commit access tokens, AWS credentials, `.env`, `.venv`, `.aws-sam`, or local report storage.
- Human review remains necessary. No hardware actuation or automatic product rejection is performed.

## Limitations

- No certified inspection capability, production defect taxonomy, or safety guarantee.
- Grayscale comparison can miss color-only changes; tiny and low-contrast defects can also be missed.
- Shadows, reflections, camera movement, and background changes can produce nuisance flags.
- Repeated patterns, untextured surfaces, and large perspective changes can make alignment unreliable.
- The intended operating conditions are controlled views of the same scene or assembly; general handheld inspection has not been validated.
- Thresholds need calibration and independent evaluation for each intended use case.
- Concurrent review writes use last-writer-wins storage; use one reviewer during the demo.
- The shared access token provides demo access control, not individual user identity or tenant isolation.

## Next steps

1. Collect independently labeled reference/candidate photo pairs, including separately captured unchanged scenes.
2. Measure missed changes and nuisance flags against a simple image-difference baseline.
3. Improve region-of-interest selection and handling of lighting/background variation.
4. Evaluate mobile usability and cloud latency under repeatable workloads.
5. Add individual reviewer identity and conflict-safe review updates.

## Documentation

- [Technical report](docs/TECHNICAL_REPORT.md)
- [System architecture](docs/ARCHITECTURE.md)
- [AWS deployment guide](docs/AWS_DEPLOYMENT.md)
- [Demo script](docs/DEMO_SCRIPT.md)
- [Submission checklist](docs/SUBMISSION_CHECKLIST.md)

## Development disclosure

ChatGPT/Codex assisted with implementation, debugging, tests, and documentation. The participant performed AWS deployment, captured the real photographs, and exercised the browser workflow. Synthetic artwork is generated by the project's code; no external dataset or downloaded model is bundled.

Built for the **OpenCV AI Competition 2026 powered by AWS**. This prototype makes no claim of award eligibility or industrial validation.
