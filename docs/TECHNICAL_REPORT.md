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
See `ARCHITECTURE.md` and `template.yaml`. The proposed deployment runs the actual OpenCV workload in a 2 GB x86_64 Lambda container behind HTTP API. The execution role can read/write only the report prefix of its private S3 bucket. Reports include images, metrics, trace, timestamps and human-review state. S3 encryption and a 30-day lifecycle are configured. The frontend sends a shared inspection token for protected operations.

**Cloud deployment has not been executed.** The Lambda adapter has local event tests; the S3 path has an SDK-stub test. Neither replaces a real AWS invocation. `cloud_check.py` is supplied to produce deployment evidence after the participant deploys. No COOL/Graviton performance claim is made.

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
3. Deploy on AWS and record actual cold/warm end-to-end measurements.
4. Add per-user identity and conditional writes before multi-user deployment.
5. Explore color-sensitive comparisons and trained detectors only if the labeled data supports them.

AI assistance was used to implement and document the project. The participant must validate and understand the delivered code, add personal evidence, and make any required disclosure in the final submission.
