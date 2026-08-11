# Implementation Roadmap: Instagram Influencer Finder Bot

This document outlines the detailed development phases, checklists, deliverables, and architecture requirements for building the production-quality Instagram Influencer Finder Bot.

---

## Architecture Design Principles

* **Configuration-Driven**: All timeouts, paths, thresholds, and CSS selectors are defined centrally in `config/settings.py` or `.env`.
* **State Preservation**: Run details are stored in SQLite and incremental matches are dumped immediately to CSV. The crawl state will persist, allowing resumes from intermediate states.
* **Loose Coupling**: Distinct modules handle browser automation, bio matching, data storage, and external API sync.
* **Resiliency**: Built-in exponential backoff, rate limit delay models, and intercepting CAPTCHA fallbacks to protect the account from bans.

---

## Phase 1: Project Setup

Establish a clean structure, configure virtual environment environments, and prepare the logging/config scaffolding.

### TODO Checklist
- [x] Configure standard virtual environment `venv` and confirm platform dependencies.
- [ ] Establish folders:
  - `src/` (root source code wrapper)
  - `config/` (settings and local environment configs)
  - `core/` (scrapers and traversers)
  - `instagram/` (auth and browser management)
  - `matcher/` (keywords and locations parser)
  - `storage/` (CSV and SQLite modules)
  - `google_sheets/` (Sheets client sync)
  - `utils/` (shared formatters and parsers)
  - `logs/` (directory for runtime files)
  - `tests/` (unit and integration tests)
- [ ] Initialize `config/settings.py` with path constants, delay boundaries, and database paths.
- [ ] Create a `.env.template` specifying required credential locations (e.g. sheets credentials, session states).

### Deliverables
* Standardized, production-ready directory structure.
* Working `config/settings.py` template.
* Setup scripts (`setup.py`, `setup.sh`) verifying dependency configurations.

---

## Phase 2: Instagram Authentication

Provide a reliable method to run authenticated Playwright instances using imported cookies.

### TODO Checklist
- [ ] Implement cookie extraction and validation logic in `instagram/auth.py`.
- [ ] Inject cookies from `instagram_session.json` directly into Playwright's `BrowserContext`.
- [ ] Design a heartbeat check (e.g. loading a light account settings page or the main dashboard) to verify authentication status before traversing.
- [ ] Setup a fallback trigger to pause execution and notify the dashboard/console if session verification fails (e.g., CAPTCHA or expired cookie).

### Deliverables
* `instagram/auth.py` and `instagram/client.py`.
* Heartbeat session verification module.
* Local session validation test suites.

---

## Phase 3: Following Traversal Engine

Build the core algorithm to safely retrieve and scroll the following list of a target profile.

### TODO Checklist
- [ ] Direct browser to the target profile (`https://www.instagram.com/{target_username}/`).
- [ ] Inject CSS selectors to click the "following" link and wait for the dialog overlay.
- [ ] Write a dialog scrolling loop that handles virtualized nodes (extracting links while scrolling and cleaning up off-screen elements).
- [ ] Build network interceptors using Playwright `on("response")` to capture JSON responses from Instagram's `graphql/query` endpoints related to following (`edge_follow`).
- [ ] Yield followed profile URLs/usernames incrementally as generators to keep memory overhead at a minimum.

### Deliverables
* `core/traversal.py`.
* Network capturing logic for internal Instagram GraphQL APIs.
* Traversal flow testing utilities.

---

## Phase 4: Bio & Profile Extraction

Visit scraped followed accounts, determine details, and handle page structure variation.

### TODO Checklist
- [ ] Navigate to each crawled followed profile.
- [ ] Scrape the following profile elements:
  * Full Name (profile header element)
  * Biography (text contents with links and line breaks)
  * Post count, followers count, and following count
  * Verified status (existence of checkmark badge)
  * Account privacy (private vs. public indicators)
  * Business category description (if present)
- [ ] **Bio Capture on Match**: When a profile matches both keyword and location, the full biography text must be captured and saved as part of the result record. The bio is a mandatory output field for every matched profile.
- [ ] Detect block/rate-limit indicators (e.g. redirected to login page or custom page-not-found layouts).

### Deliverables
* `core/extraction.py`.
* Selection maps covering dynamic profile structures.
* Parser tests using mocked profile HTML templates.

---

## Phase 5: Keyword Matching Engine

Implement normalizing classifiers to check bio texts against single/multiple targets.

### TODO Checklist
- [ ] Build a text normalizer in `utils/helpers.py` to remove non-alphanumeric punctuation and squash duplicate whitespace.
- [ ] Implement case-insensitive comparison in `matcher/keyword.py`.
- [ ] Extend keyword check to handle list targets:
  * `OR` queries: true if any keywords are found.
  * `AND` queries: true only if all keywords match.
  * Phrase boundaries: match word groupings exactly.

### Deliverables
* `matcher/keyword.py`.
* Standard keyword list definitions in `config/settings.py`.
* Extensive keyword matching unit tests covering capitalization and spacing patterns.

---

## Phase 6: Location Matching Engine

Locate geographical indicators inside user bios and profiles.

### TODO Checklist
- [ ] Design location parsers in `matcher/location.py`.
- [ ] Match location markers against:
  * Profile Bio text
  * Target location tags (if profile provides them)
  * External linked URLs or business address mentions
- [ ] Support list-based location queries (e.g. matching multiple cities or local neighborhoods).

### Deliverables
* `matcher/location.py`.
* Unit tests containing various bio formats with mock locations.

---

## Phase 7: CSV & SQLite Storage

Store crawled profiles immediately and avoid crawl redundancy.

### TODO Checklist
- [ ] Write `storage/csv_writer.py` to append matched profiles incrementally:
  * Columns: `Username`, `Full Name`, `Profile URL`, `Bio`, `Location`, `Followers Count`, `Following Count`, `Posts Count`, `Verified`, `Public/Private`, `Keyword Matched`, `Location Matched`, `Date Collected`.
  * The `Bio` column is **mandatory** for every matched row — it must never be empty when a keyword+location match is confirmed.
- [ ] Establish `storage/sqlite_db.py` to track visited history (`visited_cache`) and profile results.
- [ ] Build resume logic: query SQLite database before loading a followed profile page to check if the target profile has already been parsed.

### Deliverables
* Database schemas (`profiles.db` containing `visited` and `matches`).
* Incremental CSV generator output.
* Verification tests ensuring duplicate records are ignored.

---

## Phase 8: Google Sheets Integration

Synchronize verified records directly to remote sheets.

### TODO Checklist
- [ ] Authenticate with Google API using service account credentials (`credentials.json`).
- [ ] Develop `google_sheets/sync.py` to batch-append new database records.
- [ ] Save sync metadata locally (e.g., date of last sync, last synced SQLite row IDs) to bypass duplicate uploads.
- [ ] Include automatic retries with backoff on Google Sheets API timeouts or quota limits.

### Deliverables
* `google_sheets/sync.py`.
* Sheet setup scripts assigning permissions.
* Batch uploading unit test suite.

---

## Phase 9: Logging and Error Handling

Log bot activities, retry transient failures, and save details on error.

### TODO Checklist
- [ ] Setup log rotating file handlers inside `logs/`.
- [ ] Create a JSONL structured logger for analytical logs (e.g., matching rates, scraping times).
- [ ] Implement exponential backoff retry wrappers for network request tasks.
- [ ] Add specific actions for known errors:
  * Rate-limited: Pause scraping, sleep 10-15 minutes, notify administrator.
  * Private account: Skip extraction, note in logs.
  * Session expired: Terminate execution or prompt cookie refresh.

### Deliverables
* Modular error handler (`utils/errors.py`).
* Rotated log outputs in the `logs/` directory.

---

## Phase 10: Performance Optimization

Achieve stability and resource efficiency while running headful or headless.

### TODO Checklist
- [ ] Disable assets (images, fonts, stylesheets) in Playwright browser configuration to reduce network load.
- [ ] Implement variable delays (`random.uniform(min, max)`) between visits.
- [ ] Optimize memory footprint: reuse browser page context objects instead of opening new tabs.

### Deliverables
* Asset blocking controls.
* Performance tuning parameters in settings.

---

## Phase 11: Testing

Verify correctness across components using mock inputs.

### TODO Checklist
- [ ] Write unit tests for cleaning functions, matchers, and DB engines in `tests/`.
- [ ] Create integration tests that mock Playwright network requests to isolate logic.
- [ ] Validate CSV/SQLite schemas against target constraints.

### Deliverables
* Verified `pytest` config showing complete code coverage.
* HTML extraction test files.

---

## Phase 12: Production-Ready Checklist

Ensure operational security and maintenance strategies.

### Deployment Checklist
- [ ] Verify `instagram_session.json` cookies are active.
- [ ] Install Playwright system dependencies (`playwright install-deps`).
- [ ] Ensure `credentials.json` is protected and has spreadsheet edit permissions.
- [ ] Schedule regular log rotations to prevent disk space issues.

### Future Improvements
- [ ] Implement proxy rotation management to bypass Instagram IP rate-limits.
- [ ] Add multi-account rotation support to split following crawl tasks.
- [ ] Create a web dashboard showing analytics and matching status maps in real-time.
- [ ] Support OCR extraction for bio information embedded in profile images.
