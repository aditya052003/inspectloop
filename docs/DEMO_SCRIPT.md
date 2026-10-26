# Five-minute demo plan and natural speaking notes

Do not read claims that you cannot demonstrate. The AWS paragraph below is conditional on successful deployment.

## 0:00–0:30 — Introduce yourself and the problem
“Hi, I'm Aditya. This is InspectLoop, a visual inspection prototype. I wanted to go beyond drawing a box around a difference. A useful inspection tool also needs to notice when the photo itself is unreliable and know when to ask a person for help.”

## 0:30–1:20 — Show a missing component
Run the missing-component sample. Show the reference and overlay, then switch to the mask.
“This is a synthetic example, so I'm not claiming factory accuracy. The system aligns the candidate with the reference, finds a changed region, and measures the evidence in that region. It flags the change for review instead of automatically rejecting the product.”

## 1:20–2:10 — Show that evidence changes the next action
Run the dim capture with defect, then open the exposure-recovery trace.
“The brightness measurement caused the controller to run exposure correction before comparison. That is a different tool path from a well-lit image.”
Run the blurry sample.
“Here, the right action is to ask for a better photo. Continuing with a blurry capture would give misleading confidence.”

## 2:10–2:45 — Human control
Return to a missing-component inspection, add a note and confirm the defect. Export the report.
“The machine observation and the person's decision are recorded separately. The report includes the images, measurements and sequence of tool calls.”

## 2:45–3:30 — Architecture
Show `docs/ARCHITECTURE.md` in Markdown preview.
“The core uses OpenCV 5: quality measurements, ORB matching, RANSAC alignment, difference masks and contour analysis. The controller is deterministic, so the decision steps are reproducible. It is not an LLM.”

**Only after deployment:** “The same OpenCV workload runs inside AWS Lambda. HTTP API exposes the application, and a private S3 bucket stores the evidence. Here is the deployed health response and a saved report.” Show actual endpoint and AWS evidence with secrets redacted.

**If deployment is incomplete:** Say that plainly. The competition requires a meaningful AWS component; local-only operation does not satisfy that requirement.

## 3:30–4:15 — Evaluation
Show summary and results CSV.
“I tested eight synthetic scenarios across ten texture variations. All 80 cases took the expected route on this local run. These are development fixtures, not a held-out industrial dataset. The local engine timing also excludes cloud networking and cold starts.”

## 4:15–4:50 — Limitations and next step
“Tiny defects, low-contrast changes and color-only changes can be missed. Lighting and viewpoint also matter. My next validation step is independent, labeled product photographs and a cloud latency benchmark. The goal is to make the evidence and uncertainty visible while keeping the final decision with a person.”

## Questions you may be asked
**Why OpenCV instead of only a generative model?** “This narrow fixed-camera task benefits from directly measurable geometry and image differences. I can show exactly which operation produced a flag.”

**Is this agentic?** “It uses a deterministic perception–decision–action controller. Image measurements change later tools and actions. I am not claiming it uses an LLM or that award qualification is guaranteed.”

**What did you train?** “Nothing in this version. It uses classical OpenCV methods and calibrated rules.”

**Did you use AI to build it?** “Yes, I used AI assistance for implementation and documentation. I am reviewing the code and validating the behavior.” Update this only to reflect what you have actually done.

**What is your accuracy?** “I don't have a real-world accuracy estimate yet. I have a reproducible synthetic routing benchmark and documented failure cases.”
