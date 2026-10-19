#!/usr/bin/env python3
"""Slow, local helper: looks up public TikTok profile pages for usernames in a text file.

Run it on your own computer, at your own risk: automated requests may go against TikTok's terms.
It NEVER reports "available". The most it can say is "notfound" (TikTok shows no profile), which is not proof
the name is free: banned, deleted and reserved names look the same. Confirm in Edit profile -> Username.

It does not log in, send cookies, solve CAPTCHAs or retry blocked requests. On a block it stops.

  python3 tools/check.py names.txt              # names.txt = the app's "Export TXT"
  python3 tools/check.py names.txt -o out.json  # then use "Import results" in the app
"""
import argparse, json, random, re, sys, time, urllib.error, urllib.request

UA = 'username-finder-local/1.0 (personal use; slow; +https://github.com/F7-7/tiktok-username-finder)'
DATA = re.compile(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', re.S)
VALID = re.compile(r'^(?!\.)(?!.*\.\.)[a-z0-9._]{2,24}(?<!\.)$')


def classify(html):
    """taken | notfound | unknown, from the profile page's embedded state."""
    m = DATA.search(html)
    if not m:
        return 'unknown', 'no profile data in page (CAPTCHA, block or layout change)'
    try:
        detail = json.loads(m.group(1))['__DEFAULT_SCOPE__']['webapp.user-detail']
    except (ValueError, KeyError, TypeError):
        return 'unknown', 'unexpected page structure'
    code = detail.get('statusCode')
    if code == 0 and detail.get('userInfo', {}).get('user', {}).get('uniqueId'):
        return 'taken', 'profile exists'
    if code == 10202:
        return 'notfound', "TikTok: couldn't find this account (NOT proof it is free)"
    return 'unknown', f'status code {code}'


def fetch(base, name):
    req = urllib.request.Request(f'{base}/@{name}', headers={'User-Agent': UA, 'Accept': 'text/html'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode('utf-8', 'replace')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('names', help='text file, one username per line')
    ap.add_argument('-o', '--out', default='results.json')
    ap.add_argument('--limit', type=int, default=40, help='max names per run (default 40)')
    ap.add_argument('--delay', type=float, default=12, help='minimum seconds between requests (default 12, minimum 8)')
    ap.add_argument('--base', default='https://www.tiktok.com', help=argparse.SUPPRESS)
    a = ap.parse_args()
    delay = max(8.0, a.delay)

    names = []
    for line in open(a.names, encoding='utf-8'):
        n = line.strip().lower().lstrip('@')
        if n and n not in names:
            names.append(n) if VALID.match(n) else print(f'skip (invalid): {n}', file=sys.stderr)
    names = names[:a.limit]
    try:
        results = json.load(open(a.out))
    except (OSError, ValueError):
        results = {}
    todo = [n for n in names if results.get(n, {}).get('status') not in ('taken', 'notfound')]
    print(f'{len(todo)} to check, about {int(len(todo) * (delay + 3) / 60) + 1} min. Ctrl+C is safe; progress is saved.')

    bad = 0
    for i, n in enumerate(todo):
        try:
            status, note = classify(fetch(a.base, n))
        except urllib.error.HTTPError as e:
            status, note = 'unknown', f'HTTP {e.code}'
            if e.code in (403, 429):
                bad += 2
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            status, note = 'unknown', f'network error: {e}'
        bad = bad + 1 if status == 'unknown' else 0
        results[n] = {'status': status, 'note': note, 'at': time.strftime('%Y-%m-%dT%H:%M:%S')}
        json.dump(results, open(a.out, 'w'), indent=1)
        print(f'[{i + 1}/{len(todo)}] @{n}: {status}  ({note})')
        if bad >= 2:
            print('Stopping: TikTok is blocking or changed its pages. Not retrying. Use the app\'s manual checking mode.')
            break
        if i + 1 < len(todo):
            time.sleep(delay + random.uniform(0, 5))
    print(f'Saved {a.out}. Import it in the app. Only "Confirmed available" via Edit profile counts.')


if __name__ == '__main__':
    main()
