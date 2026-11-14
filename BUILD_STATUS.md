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

## Phase 1
- Android CI workflow: `.github/workflows/android-build.yml`.
- First attempt failed SDK installation (not a Kotlin compiler result); workflow fixed in follow-up commit.
- No verified compiled APK yet. Build status remains IN PROGRESS.

### Verified CI on Phase 1 head `691ddd94312e86b187b1680809b23f26fab2577e`
- **SUCCESS** GitHub Actions: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43590922509
- Tasks verified: `:app:assembleDebug`, `:app:testDebugUnitTest`, `:app:lintDebug`.
- Artifact: `NaviTaxi-debug-apk` ID `14111199844`.
- APK: `app-debug.apk`, 16,416,125 bytes; SHA-256 `1b1824ecd27f4a7364ef38f7fbc85f6e8f803743144928f6c083be06947c7171`.
- Android manifest and 4 DEX files inspected in downloaded artifact.
- Device launch/screenshot/install validation: **NOT TESTED**; defer to instrumented/device acceptance.
- Note: successful debug compilation is NOT a signed production `NaviTaxi.apk` release.
