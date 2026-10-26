# Architecture

The cloud diagram describes the provided deployment design, not an already running deployment.

```mermaid
flowchart TD
    U[Browser: reference and candidate] --> G[AWS HTTP API]
    G --> L[AWS Lambda: Flask and OpenCV 5]
    L --> Q[Capture quality measurements]
    Q -->|Too dark or blurred| R[Request another capture]
    Q -->|Moderately dim| E[Bounded exposure correction]
    Q -->|Usable| A[ORB and RANSAC alignment]
    E --> A
    A --> D[Difference mask and local region refinement]
    D --> H[Human review or no significant change]
    H --> S[Private S3 evidence reports]
    R --> S
    S --> U
```

```mermaid
flowchart TD
    P[Measure visual evidence] --> C{Policy decision}
    C -->|Information missing| R[Ask user to retake]
    C -->|Recoverable exposure| E[Apply correction and remeasure]
    E --> P
    C -->|Image usable| A[Align and compare]
    A --> B{Changes found?}
    B -->|Yes| Z[Measure candidate regions]
    Z --> H[Request human review]
    B -->|No| N[Report no significant change]
```

The recovery branch executes at most once. The policy does not loop indefinitely. A trace contains each measurement, tool choice, and action. Human review is recorded separately and never rewrites the machine observation.

In local mode, Flask serves both UI and API on localhost and `storage.py` writes JSON under `data/reports/`. In cloud mode, the same code runs in a Lambda container and writes private S3 objects. The API adapter handles JSON, base64 multipart uploads, and static asset responses. No database, external model API or GPU is required.
