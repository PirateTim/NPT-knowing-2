# Spyglass: The Ingestion & Seizure Engine

## Role & Mandate
**Spyglass** is the NPT Fleet's dedicated acquisition agent. Her mandate is the deduplicated, multi-tiered seizure of web, PDF, and academic payloads from the wild into the Google Cloud Storage Cargo Hold (`gs://npt-fleet-cargo-hold/acquisitions/`) and the PostgreSQL metadata catalog (`cargo.content_metadata`).

---

## 1. Multi-Tier Acquisition Architecture

```
[ Target URL / DOI ]
        │
        ▼ (Pre-Flight Check)
[ check_cargo_manifest ] ──► Queries cargo.content_metadata & cargo.failed_metadata
        │                      ├── [ALREADY CAPTURED] ──► Skip acquisition
        │                      └── [KNOWN DEAD-LETTER] ──► Skip dead domain / permanent 404
        ▼ [CLEAR]
[ Tier 1: Fast HTTP Client (download_url) ] ── (requests + trafilatura)
        │
        ├──► Succeeded (Text length > 500 chars) ──► Stream to GCS via upsert_knowledge_artifact
        │
        └──► Failed (HTTP 403, Cloudflare, JS-Wall, or text < 500 chars)
                 │
                 ▼
[ Tier 2: Anti-Detect Engine (Botasaurus) ] ── (Headless Chromium DOM fetch)
        │
        ├──► Succeeded ──► Stream to GCS via upsert_knowledge_artifact & log to cargo.content_metadata
        │
        └──► Failed (Timeout / Dead Host / Hard Paywall) ──► Log to cargo.failed_metadata dead-letter queue
```

---

## 2. Botasaurus Headless vs. Visual Debug Mode

By default, Spyglass runs in **automated batch mode**:
- `headless=True`: No desktop browser window opens.
- `close_on_crash=True`: If a site triggers a timeout or anti-bot challenge, the browser process terminates immediately without pausing for interactive input (`"Press 'Enter' to close"`).
- `block_images=True`: Skips loading heavy image assets to conserve memory and bandwidth.

### How to Turn Visible Browser Debug Mode ON
If you want to manually inspect why a specific domain (e.g. Cloudflare captcha, dynamic JavaScript rendering, paywall interstitial) is failing:

#### Method A: Environment Variables (`.env`)
Add the following to your `.env` file:
```ini
BOTASAURUS_HEADLESS=false
BOTASAURUS_CLOSE_ON_CRASH=false
```

#### Method B: Code Configuration in `acquisition_tools.py`
In `src/react_agent/tools/acquisition_tools.py`, set:
```python
_BOTASAURUS_HEADLESS = False
_BOTASAURUS_CLOSE_ON_CRASH = False
```

When visual debug mode is active:
1. Chromium will open visibly on your desktop when Tier 2 Botasaurus triggers.
2. If a crash or challenge occurs, the window will stay open and display a screenshot in `error_logs/` so you can visually inspect the page layout or solve interactive captchas.

---

## 3. Telemetry & Dead-Letter Ingestion Optimization

- **`cargo.content_metadata`**: Master catalog of successful acquisitions, tracking `source_url`, `gcp_bucket_path`, and `tool_name` (which tier succeeded).
- **`cargo.failed_metadata`**: Dead-letter tracking table recording failed URLs, error messages, and failure timestamps.
- **Pre-Flight Deduplication**: `check_cargo_manifest(url)` checks **both** tables before downloading. If a URL is already captured or logged as a known dead-letter, Spyglass skips it immediately, preventing redundant retry loops and saving execution cycles.
