# InspectLoop
### Evidence-driven visual inspection with OpenCV 5

InspectLoop compares a reference assembly with a candidate photo, measures capture quality, corrects moderate underexposure, aligns the images, localizes visual changes, and asks a person to review flagged regions. It is a working research prototype, not a certified industrial inspection system.

**Start here:** run the app locally, try the missing-component scenario, then read `docs/AWS_DEPLOYMENT.md` before deploying.

## Windows quick start (PowerShell)
Install **Python 3.12 (64-bit)**, extract this archive, open the `inspectloop` folder in VS Code, and open Terminal → New Terminal. Run these commands in the folder containing `app.py`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:5000** in your browser. Keep the terminal running. Press Ctrl+C to stop. You do not need Node.js, MongoDB, Docker, or AWS to try it locally. Python activation is unnecessary with these commands.

For later launches, run only the final command. If `py` is unavailable, reinstall Python with the launcher enabled, or replace `py -3.12` with `python` after checking `python --version`.

## macOS / Linux
```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

## What works
- Eight labeled synthetic demos: clean, missing part, scratch, shifted camera, dim capture with missing part, blur, extreme darkness, wrong reference.
- Reference + candidate JPEG/PNG uploads; size and content validation.
- OpenCV 5 quality measurements, ORB alignment with RANSAC, difference masks and region refinement.
- Actual branching policy: recover exposure, request a new capture, inspect changed regions, or route to human review.
- Original, overlay, and mask views; measured tool-call trace; JSON export with images and timing.
- Persisted human review; local JSON storage or private AWS S3 storage.
- AWS SAM configuration for Lambda, HTTP API, private S3, encryption, throttling, and token-protected inspection/report endpoints.

## Demo sequence
1. Select **Missing component** → Run inspection. Inspect the red box and evidence trace.
2. Enter a review note, then **Confirm defect** or **Dismiss as acceptable**.
3. Run **Dim capture + defect**. The trace includes exposure recovery before comparison.
4. Run **Out of focus**. The system requests a retake instead of producing a confident inspection result.
5. Run **Camera shifted**. Registration compensates for the small movement.
6. Download the JSON evidence report.

To use your own photos, start with a fixed camera, one product type, the same framing, a textured fixture and controlled lighting. Uploading unrelated stock images is not a valid evaluation of this method.

## Tests and evaluation
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe evaluate.py
```

On Linux use `.venv/bin/python` instead. `evaluation/summary.json` and `results.csv` contain the actual local benchmark. The 80 fixtures are correlated procedural variants used during development. Routing success on them is **not real-world accuracy**. See `evaluation/failure-cases.json` for explicit misses.

## Structure
| File | Purpose |
|---|---|
| `app.py` | HTTP routes, validation, authentication, human review |
| `vision.py` | OpenCV pipeline and branching policy |
| `demo.py` | Original procedural sample generator |
| `storage.py` | Local / S3 evidence persistence |
| `lambda_handler.py` | HTTP API v2 adapter |
| `templates/`, `static/` | Responsive browser UI, no external assets |
| `template.yaml`, `Dockerfile` | AWS deployment definition |
| `evaluate.py`, `tests/` | Reproducible benchmark and automated tests |
| `docs/` | Technical report, architecture, deployment, video script, submission checklist |
| `samples/` | Downloadable original synthetic fixtures for the upload path |

## Current readiness
The app and OpenCV 5 workload have been run locally. API, pipeline, authentication, review, Lambda event adaptation and mocked S3 tests have been executed. JavaScript syntax and local HTTP asset delivery were checked. A full browser visual/interaction check was blocked by a failed browser-runtime download and remains to be completed. AWS infrastructure is supplied but **not deployed or cloud-verified**. No competition submission has been made. There is no trained neural model, LLM, COOL integration, or claim to the COOL award. The agentic path uses a deterministic controller; eligibility is for the organizers to decide.

## Storage and access
Local reports are stored in `data/reports/`. They include normalized images, so treat them as private. Delete this directory to remove local reports. Cloud reports expire after 30 days. A page reload clears the UI but reports remain stored; keep exported reports or their IDs. There is no report-history browser in this prototype.

The cloud UI is reachable over HTTPS, but inspection, report retrieval and review require `INSPECT_TOKEN`. This is a shared demo token, not production identity or per-user authorization. Do not post it in a public repository. Local mode binds only to localhost and is unauthenticated unless you set the environment variable yourself.

## Limitations
No production defect taxonomy or safety guarantee. Grayscale comparison can miss color-only changes. Tiny and low-contrast defects can be missed. Repeated patterns can confuse alignment. Large perspective changes, reflections, shadows, different products and untextured surfaces require a retake or a different approach. Thresholds need calibration against independently labeled photographs. Concurrent review writes use last-writer-wins storage, so use a single reviewer during the demo. No hardware actuation or automatic rejection is performed.

## References
- Competition: https://opencv26.devpost.com/
- Schedule: https://opencv26.devpost.com/details/dates
- OpenCV Python install: https://docs.opencv.org/5.0/py_tutorials/py_setup/py_pip_install/py_pip_install.html
- Pinned OpenCV distribution: https://pypi.org/project/opencv-python-headless/5.0.0.93/
- AWS Lambda Python images: https://docs.aws.amazon.com/lambda/latest/dg/python-image.html
- AWS SAM build: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-build.html

AI assistance was used to create this implementation and documentation. Before submission, the participant should review, understand, customize and validate it, and disclose assistance where required. Sample artwork was generated procedurally by this project's code; no external dataset or downloaded model is bundled.
