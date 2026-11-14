# Build and tests

- Android APK: NOT BUILT.
- Java: OpenJDK 21 detected.
- Kotlin CLI: present (local).
- Android SDK/Gradle/AAPT2/Apksigner: not detected locally.
- Python database unit tests: PASSED in GitHub Actions run 43589361023 (SQLite, source/coordinate validation, RTree triggers, embedded asset scan, archive checks).
- Evidence artifact: phase0-road-data-evidence, GitHub artifact ID 14110994349, SHA-256 faf217ca2ce3348854cbab950951039ad6e3b5f64465ad08b2a1f00960dd1abb.
- GitHub Actions workflow: `.github/workflows/phase0-road-data.yml`, https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43589361023.
- Android device UI/screenshot tests: NOT STARTED.

Acceptance policy: source creation != test pass; record GitHub Actions run, job result, artifact checksum and device model once available.
