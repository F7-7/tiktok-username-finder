# TikTok Username Finder

A static web app that generates TikTok username ideas and gives you a fast manual workflow for checking them on TikTok.
It is not affiliated with TikTok.

Live: https://f7-7.github.io/tiktok-username-finder/

## Why availability is never checked automatically

TikTok has no public API that reports whether a username is free. The ways people work around that are all unreliable or against TikTok's terms:

- **Loading `tiktok.com/@name` from a server.** TikTok blocks most datacenter traffic with CAPTCHAs and rate limits. Also, "Couldn't find this account" shows for banned, deleted and reserved names too, so a missing profile does not prove a name is free.
- **Calling the private signup or edit-username endpoints.** These need a logged-in session (cookies or tokens) and request signing, and using them this way breaks TikTok's terms.

So the app does not guess. Every name starts as **Unverified**, and only you can move it to **Confirmed available**, after TikTok itself accepts the name in *Edit profile → Username*.
The app sends no requests to TikTok. It never asks for a password, cookies or tokens, and it has no backend and no secrets.

| Status | Meaning | Who sets it |
|---|---|---|
| Unverified | Not checked yet | default |
| Taken | A profile exists at `tiktok.com/@name` | you, after opening it |
| No profile found | TikTok says "Couldn't find this account". Possibly free, possibly banned or reserved | you |
| Confirmed available | TikTok accepted it in *Edit profile → Username* | you |
| Couldn't tell | Error page, CAPTCHA, or anything unclear | you |

The **Confirmed available** tab shows only confirmed names, kept apart from unverified suggestions.

## Optional local helper (`tools/check.py`)

For people who don't want to open every profile by hand. Python 3 standard library only, runs on **your own computer**, not on the site.

```bash
# 1. In the app: Export TXT (the current view). 2. Then:
python3 tools/check.py tiktok-usernames.txt -o results.json
# 3. In the app: Import results -> results.json
```

- It requests public profile pages slowly (12 s or more between requests, 40 names per run by default), with a plain identifying User-Agent. No login, no cookies, no CAPTCHA handling.
- It stops after two blocked or unrecognised responses and does not retry. If TikTok blocks it, use the manual checking mode.
- It can only produce **Taken**, **No profile found** or **Couldn't tell**. It never produces Available, and the app refuses an `available` status from an imported file. "No profile found" is not proof a name is free: confirm in *Edit profile → Username*.
- **Risk:** automated requests to TikTok may go against its terms. Use it at your own risk and in small batches.
- Not verified against live TikTok. The page format it reads (`webapp.user-detail`, `statusCode` 0 / 10202) is an assumption based on how TikTok pages currently look, and `tools/test_check.py` tests it only against fake pages. If TikTok changes the format, results become Couldn't tell rather than wrong.

## Tests

- **Generator.** Keywords (a phrase like `fahad awad` also gives first.last combos), initials, preferred words, 5 styles (minimal, aesthetic, professional, gaming, rare-looking), length 3–5, 6–8, 9–12 or any, and toggles for `_`, `.` and numbers. You can exclude characters or words and generate 20–500 names per batch.
- **Smart variations.** Vowel-drop forms (`coffee` → `cffee`), one subtle respelling per variant (`ph`↔`f`, `c`→`k`, `s`→`z`, …), truncations, initials and combos. Digits appear only if you allow them, and then only as a single leet swap. Exact duplicates and separator-only duplicates (`a.b` vs `a_b`) are removed. Picks rotate across patterns so no single template floods the batch.
- **Rules check.** Every name is 2–24 characters, uses only `a–z 0–9 _ .`, does not start or end with `.`, has no `..`, and is not numbers-only.
- **Checking mode.** Steps through the current view one name at a time. *Open* loads the profile in one reused tab. Keyboard: `T` taken, `N` no profile, `A` available, `U` couldn't tell, `S`/→ skip, `←` back, `C` copy, `F` favorite, `O` open.
- **Dashboard.** Status tabs with counts, a progress bar, filters for length, characters, style and status, sorting, copy, favorites, and export of the current view as TXT or CSV. The search box also adds a username you already have in mind.
- **Storage.** Results, statuses, favorites and form settings are kept in this browser's `localStorage`. Export to move them elsewhere.

## Run locally

No build step and no dependencies. ES modules need an HTTP server (not `file://`):

```bash
# from this folder
python3 -m http.server 8765
# open http://localhost:8765/
```

On GitHub Pages it is served as-is from this folder. On Replit or any static host, serve the folder and open `index.html`. No environment variables or secrets are needed, because there is no backend.

## Tests

```bash

node --test tests/*.test.mjs          # generator: validity, ranges, dedup, toggles, exclusions, 500/batch
# browser flows (needs Playwright + Chromium and the server above running):
node tests/e2e.mjs http://localhost:8765/
python3 tools/test_check.py           # helper: classification, never 'available', stops on blocks
```

The browser test runs at 1280px and 375px. It covers generate, copy, favorite, open profile, checking mode with keyboard marks, the confirmed-only tab, status changes, filters, adding a custom name (with validation), TXT/CSV export, persistence across reload, append without duplicates, the non-Latin keyword warning, no horizontal overflow, no console errors, and **no background requests to TikTok**.

## Files

| File | Role |
|---|---|
| `generator.js` | Pure generation, scoring, dedup and TikTok rule validation (no DOM) |
| `app.js` | UI state, filters, checking mode, export and storage |
| `index.html`, `style.css` | Markup and styles |
| `tools/check.py` | Optional slow local profile-page lookup (see above) |
| `tests/` | Node unit tests and the Playwright flow test |
