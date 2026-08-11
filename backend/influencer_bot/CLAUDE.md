# Instagram Influencer Finder Bot — Development Guide

## Project Overview
Ye bot kisi bhi Instagram profile ke **followings** me jaakar, har following ki **bio** me keywords dhoondta hai. Agar koi bhi keyword match ho jaye to us profile ko CSV file me save karta hai. Har run pe naya numbered CSV banta hai (1.csv, 2.csv, 3.csv...).

---

## How It Works (Simple Flow)
```
Target Profile (@nike) → Following List Scrape → Har Following ki Bio Check → Keyword Match → Save to CSV
```

## Quick Start
```bash
# Single keyword
python collector_runner.py --target "nike" --keyword "fitness"

# Multiple keywords (up to 7) — koi bhi ek match ho jaye to save
python collector_runner.py --target "nike" --keyword "fitness" "gym" "workout"

# Zyada followings harvest karo
python collector_runner.py --target "nike" --keyword "food" "blogger" --max-following 500

# Bina keyword ke — sab profiles save honge
python collector_runner.py --target "nike" --max-following 100
```

## Output
- Har run pe naya file: `output/1.csv`, `output/2.csv`, `output/3.csv`...
- CSV columns: `username, profile_url, niche, score, date_collected`
- Bio CSV me NAHI hoti (time save hota hai)

---

## Architecture — File Map

| File | Role |
|---|---|
| `collector_runner.py` | CLI entry point — arguments parse karke engine chalata hai |
| `discovery_engine/engine.py` | Core brain — browser control, following scrape, profile check |
| `discovery_engine/relevance.py` | Multi-keyword matching logic (case-insensitive, variants) |
| `storage.py` | Numbered CSV file writer |
| `config.py` | Settings (timeouts, paths, CSV columns) |
| `instagram_session.json` | Saved login cookies (Playwright format) |

### Unused Files (safe to delete)
| File | Why Unused |
|---|---|
| `collector.py` | Purana collector — engine apni methods use karta hai |
| `utils.py` | generate_search_queries, normalize_url etc. — engine ko zaroorat nahi |
| `production_runtime.py` | StructuredLogger, BrowserManager etc. — engine apna logger use karta hai |
| `collection_schema.py` | Purani storage schema — naye storage me zaroorat nahi |
| `discovery_engine/queues.py` | BFS queue — ab sirf followings check hote hain, expansion nahi |
| `templates/`, `static/` | GUI dashboard — backend server file hi nahi hai |

---

## Development Phases

### Phase 1: Core Bot (DONE)
- [x] Browser launch with saved cookies
- [x] Target profile ke Following dialog open karna (3 fallback strategies)
- [x] Following dialog scroll karke usernames harvest karna
- [x] Har following ki profile visit karke bio extract karna
- [x] Bio me keywords match karna (case-insensitive, variants support)
- [x] Multi-keyword support (max 7 keywords, ANY match = save)
- [x] Keywords optional — bina keyword sab profiles save
- [x] Matched profiles ko numbered CSV me save karna (1.csv, 2.csv...)
- [x] Console pe progress dikhana (1/50, 2/50...)
- [x] CLI arguments (--target, --keyword, --max-following)

### Phase 2: Reliability & Performance (TODO)
- [ ] Retry logic — agar page load fail ho to 2-3 baar try kare
- [ ] Rate limiting — intelligent pause agar Instagram slow response de
- [ ] Session refresh — agar cookies expire ho jayein to warn kare
- [ ] Error recovery — agar beech me crash ho to resume kar sake
- [ ] Proxy support — IP block se bachne ke liye
- [ ] CAPTCHA detection — agar CAPTCHA aaye to user ko notify kare

### Phase 3: Data Enrichment (TODO)
- [ ] Followers count extract karna (page HTML se)
- [ ] Following count extract karna
- [ ] Full name extract karna
- [ ] Verified badge detect karna
- [ ] Public/Private status check
- [ ] Posts count
- [ ] Profile picture URL

### Phase 4: Google Sheets Integration (TODO)
- [ ] `credentials.json` se Google Sheets API connect karna
- [ ] CSV data ko specified Google Sheet me push karna
- [ ] CLI argument: `--sheet "Sheet_Name"` ya `--sheet-id "1abc..."`
- [ ] Duplicate check — already existing username sheet me dubara na daale

### Phase 5: Advanced Search (TODO)
- [ ] Followers range filter (`--min-followers 1000 --max-followers 50000`)
- [ ] Niche auto-detection from bio
- [ ] Search in followers list (not just following)
- [ ] Multiple targets (`--target "nike,adidas,puma"`)

### Phase 6: GUI Dashboard (TODO)
- [ ] Flask/FastAPI backend server
- [ ] Web UI: target input, keywords fields
- [ ] Live progress bar
- [ ] Results table with export button
- [ ] Google Sheets sync button

---

## Matching Logic Explained

### How Keywords Work
- Max 7 keywords de sakte ho (sab optional hain)
- Agar koi BHI keyword bio me mil jaye → profile SAVE
- Case-insensitive — "FITNESS", "Fitness", "fitness" sab same

### Keyword Variants
Keyword `"food blogger"` se ye variants bante hain:
- `food blogger` (exact)
- `foodblogger` (joined)
- `food-blogger` (hyphenated)
- `food_blogger` (underscore)
- `food` (first word)
- `blogger` (second word)

### No Keywords = Save All
Agar `--keyword` na do, to target ke SAB followings (jinka bio non-empty hai) save honge.

---

## Following Dialog — 3 Fallback Strategies

Instagram ka DOM frequently change hota hai. Bot 3 strategies try karta hai:

1. **Direct URL** — `instagram.com/{target}/following/` pe navigate karta hai
2. **CSS Selectors** — Profile page pe jaake Following link dhundhta hai multiple selectors se
3. **JavaScript Click** — DOM traverse karke Following link find + click karta hai

Agar teeno fail hon → cookies expired ya profile private hai.

---

## Config Reference

| Setting | File | Default | Description |
|---|---|---|---|
| `HEADLESS` | config.py | `False` | `True`=browser hidden, `False`=visible |
| `TIMEOUT` | config.py | `30` sec | Page load timeout |
| `BROWSER_DELAY` | config.py | `2` sec | Delay between actions |
| `OUTPUT_DIR` | config.py | `output/` | CSV files ka folder |
| `INSTAGRAM_SESSION_FILE` | config.py | `instagram_session.json` | Login cookies |
| `CSV_COLUMNS` | config.py | See below | CSV file ke columns |

CSV Columns: `username, profile_url, niche, score, date_collected`

---

## Troubleshooting

### "Following list nahi mili"
- Target username check karo — spelling sahi ho
- `instagram_session.json` fresh ho — expired cookies se Instagram redirect karta hai
- Kuch profiles ke following private hote hain — tab kaam nahi karega

### "Bio extract failed"
- Instagram ne rate limit kia hoga — `BROWSER_DELAY` barhaao (3-4 seconds)
- Profile private hai — private profiles ki bio nahi milti

### "No matching profiles found"
- Keyword spelling check karo
- Bio me exact text hona chahiye — `"fitness"` tabhi milega jab bio me `fitness` word ho
- Try broader keywords: `"food"` instead of `"food blogger"`

### Cookies Refresh Kaise Karein
1. Playwright browser me manually Instagram login karo
2. Login ke baad `instagram_session.json` update karo
3. Ya manually browser se cookies export karo Playwright format me

---

## Dependencies
```
playwright
```

Install:
```bash
pip install playwright
playwright install chromium
```
