# InspectLoop: evidence-driven inspection with OpenCV 5

## Problem and intended users
Small assembly teams may need help spotting visible differences between a known-good unit and a new unit. Image comparison can flag changes, but blur, low exposure and camera movement can make results unreliable. InspectLoop focuses on controlled photographs of the same assembly and makes capture quality and uncertainty visible before requesting a human decision.

Intended users are workshop operators, electronics assembly demonstrators and quality engineers prototyping a fixed-camera inspection station. This prototype has not been tested in a factory or shown to reduce operational cost.

## Implementation
Python 3.12, Flask and OpenCV 5 form the application. The exact OpenCV wheel is `opencv-python-headless==5.0.0.93`; its runtime reports `5.0.0`. NumPy implements numerical array operations. No trained neural model or external dataset is used.

The pipeline resizes to 640 pixels wide while preserving reference aspect ratio, checks the reference and candidate, then uses visual evidence to select tools:

1. **Quality gate:** mean grayscale brightness, Laplacian variance and clipped-pixel fraction detect unusable captures. A bad reference is rejected too.
2. **Exposure recovery:** moderate underexposure invokes a bounded gain correction, then sharpness is rechecked. Irrecoverable darkness requests a new image.
3. **Alignment:** ORB features, Hamming descriptor matching, ratio filtering and RANSAC estimate a partial affine transform. Insufficient inliers, large movement or excessive scaling request a retake. Near-identical images skip registration.
4. **Comparison:** border validity masking, a median illumination offset, Gaussian smoothing and a fixed absolute-difference threshold produce a mask. Morphological closing joins nearby pixels.
5. **Local refinement:** contour candidates are cropped and their difference support is measured. Small and weakly supported changes are filtered. The minimum support was adjusted during development because diagonal scratches occupy a small fraction of their bounding rectangle.
6. **Action:** extensive mismatch requests a retake; supported regions request human review; no regions yield “no significant visual change.” A human can confirm or dismiss a flag. The application never actuates machinery or rejects a product automatically.

Thresholds are explicit in `vision.py`, not learned. This makes the demonstration explainable but limits generalization. The workflow is a deterministic agent/controller, not an LLM agent. It is designed to demonstrate the competition's evidence-changing-action pattern; award eligibility is not asserted.

## AWS architecture and status
See `ARCHITECTURE.md` and `template.yaml`. The deployed application runs the actual OpenCV workload in a 2 GB x86_64 Lambda container behind HTTP API. The execution role can read/write only the report prefix of its private S3 bucket. Reports include images, metrics, trace, timestamps and human-review state. S3 encryption and a 30-day lifecycle are configured. The frontend sends a shared inspection token for protected operations.

The participant successfully deployed the application in AWS Mumbai (ap-south-1) on 26 October 2026. The cloud verification script reported OpenCV 5.0.0, runtime aws-lambda, S3 storage, HTTP 401 without the token, and successful retrieval of a persisted report. One synthetic inspection request took 431.7 ms end to end; this is not a throughput or latency benchmark. See evaluation/cloud-verification.json and its provenance note. The AWS browser screenshots also show a successful missing-component inspection.

The initial deployment failed because reserving two Lambda concurrent executions conflicted with the account's unreserved concurrency minimum. Removing ReservedConcurrentExecutions resolved deployment. The function now uses account-level unreserved concurrency; API throttling remains configured. No COOL/Graviton claim is made.

Live endpoint: https://620mowl7mj.execute-api.ap-south-1.amazonaws.com


## Evaluation
The bundled evaluator runs eight scenario families across ten procedural texture seeds, producing 80 related synthetic cases. The observed routing outcomes were 80/80 expected decisions on this local run. Median local engine time was 19.75 ms and p95 was 69.4 ms on the recorded environment. Refer to `evaluation/summary.json` for the machine/software context and `results.csv` for every case. Timing includes image encoding but excludes network, storage, HTTP and Lambda cold starts.

These samples were used during development and threshold adjustment. They are neither a held-out dataset nor independent real-world trials. The routing score must not be advertised as defect-detection accuracy. The saved case traces show both the OpenCV measurements and downstream actions.

Explicit stress cases are in `evaluation/failure-cases.json`. Tiny or low-contrast changes may be missed; the benchmark should be extended with independently captured real photographs and ground-truth defect annotations. Measure false-positive rate on good units, recall by defect type, localization overlap, retake rate, and end-to-end cloud latency. Keep camera sessions and physical units separate between calibration and evaluation.

## Failure handling and observability
Invalid files, oversized requests, unsupported aspect ratios, bad references, alignment failure and poor quality are handled explicitly. A failed storage write returns an error rather than a false saved-success message. The UI exposes evidence, and each exported JSON report records the exact OpenCV runtime version and decision trace. Local tests cover decision paths, upload decoding, persistence, authorization, invalid input, duplicate review, Lambda adaptation and S3 request parameters.

## Responsible use and limitations
Use only product imagery you are authorized to upload. Reports retain normalized images; local reports must be deleted manually, while the provided AWS bucket lifecycle expires cloud reports after 30 days. The shared token suits a private demonstration, not a production multi-tenant service. There is no per-user audit identity; simultaneous human reviews can race and overwrite one another, so use one reviewer during the demo.

This is not a safety-critical quality system. Grayscale processing can miss color-only changes; specular reflections, shadows, textureless objects and repeated components can confuse matching or differences. Some subtle defects will be below thresholds. “Clear” is shorthand for no detected change, never a guarantee that a product is safe or defect-free.

## Next validation milestones
1. Capture permissioned real product pairs with a fixed camera and independently label them.
2. Freeze thresholds before evaluating a separate set of physical units.
3. Extend the successful AWS smoke test with repeated cold/warm end-to-end measurements.
4. Add per-user identity and conditional writes before multi-user deployment.
5. Explore color-sensitive comparisons and trained detectors only if the labeled data supports them.

AI assistance was used to implement and document the project. The participant must validate and understand the delivered code, add personal evidence, and make any required disclosure in the final submission.

The prototype requests retakes but does not link a follow-up photograph to the earlier inspection. That extended workflow is future work. One real-photo development pair was verified through the cloud workflow as described below. No independent real-photo benchmark or baseline comparison is claimed.


## Final real-photo and deployment update — 26 October 2026

The portrait alignment fix replaces the absolute 80-pixel translation limit with
10% of the normalized image diagonal and requires at least 75% shared image area.
The existing scale and inlier checks remain. This package includes that fix.
The earlier synthetic evaluation files predate this fix; they are historical
development evidence, not a fresh benchmark of the final code.

A separate final-package validation run passed 19 tests, including two alignment
regressions. This count applies to that package; run the tests in a repository
checkout to determine its current test count.
The participant deployed the updated Lambda image successfully and supplied an
exported cloud report. The report is included as
evaluation/real-photo-cloud-report.json in the final submission archive. It records:

- OpenCV 5.0.0; status review; 17 regions; 3.188% changed area.
- Engine time 2772 ms for this single request; not an end-to-end benchmark.
- Human decision confirmed, with the note: Eraser is missing from the candidate
  photo. Other flagged areas appear to be background or alignment differences.

The missing eraser is highlighted. Extra background and object-edge detections
remain. The pair informed the fix, so it is development data, not held-out data.
A participant-provided cloud screenshot of an identical-photo check reports
0 regions, 0% changed area, and 94.4 ms. That checks identical input handling; it
does not measure false-positive rates on independently recaptured good objects.

No factory trial, quantified user-benefit study, independent accuracy study,
baseline error comparison, or completed mobile usability test is claimed.
AI assistance from ChatGPT/Codex was used for code, tests, debugging and writing.
The participant performed setup, AWS deployment, photography and browser checks.
