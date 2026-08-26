#!/usr/bin/env python3
"""Generate the three profile stat cards as self-hosted SVGs.

Replaces github-readme-stats + streak-stats + top-langs external services
(all repeatedly rate-limited/dead) with cards built from:
  - github.com/users/<user>/contributions HTML  (streak + daily counts, no auth)
  - REST API /users, /repos, /repos/*/languages (stars, followers, languages)

Styled to the Cybertron palette used across the profile.
Usage: build_stats_cards.py [output_dir]   (default: assets)
GITHUB_TOKEN env is used when present (recommended in CI).
"""
import json
import os
import re
import sys
import urllib.request
from datetime import date, timedelta

USER = "homeo26"
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets"
BASE, CARD_BG = "#0b0d12", "#11141c"
PURPLE, TEAL, PINK, BLUE = "#7c3aed", "#14b8a6", "#ec4899", "#3b82f6"
LAVENDER, MINT = "#a78bfa", "#2dd4bf"
TEXT, DIM = "#e6e8ef", "#9ca3af"
FONT = "font-family=\"'Segoe UI',Ubuntu,'Helvetica Neue',sans-serif\""
W, H, R = 400, 170, 12


def fetch(url, headers=None):
    h = {"User-Agent": "profile-card-builder"}
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url:
        h["Authorization"] = f"Bearer {tok}"
    if headers:
        h.update(headers)
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
        return r.read().decode()


# ---------------------------------------------------------------- contributions
def contributions(user):
    """{date: count} for the last year from the public contributions page."""
    html = fetch(f"https://github.com/{('users/' + user)}/contributions")
    days = {}
    for m in re.finditer(
            r'id="(contribution-day-component-[\d-]+)"[^>]*data-date="([\d-]+)"|'
            r'data-date="([\d-]+)"[^>]*id="(contribution-day-component-[\d-]+)"', html):
        cid = m.group(1) or m.group(4)
        d = m.group(2) or m.group(3)
        days[cid] = [d, 0]
    for m in re.finditer(r'for="(contribution-day-component-[\d-]+)"[^>]*>([^<]*)</tool-tip>', html):
        cid, label = m.group(1), m.group(2)
        if cid in days:
            n = re.match(r"(\d+)", label.replace(",", ""))
            days[cid][1] = int(n.group(1)) if n else 0
    return {d: c for d, c in days.values()}


def streaks(cal):
    today = date.today()
    total = sum(cal.values())
    # current streak: walk back from today (today itself may still be 0)
    cur, d = 0, today
    if cal.get(d.isoformat(), 0) == 0:
        d -= timedelta(days=1)
    cur_start = cur_end = d
    while cal.get(d.isoformat(), 0) > 0:
        if cur == 0:
            cur_end = d
        cur += 1
        cur_start = d
        d -= timedelta(days=1)
    # longest streak
    best, best_range, run, run_start = 0, ("", ""), 0, None
    for ds in sorted(cal):
        if cal[ds] > 0:
            run = run + 1
            run_start = run_start or ds
            if run > best:
                best, best_range = run, (run_start, ds)
        else:
            run, run_start = 0, None
    return total, cur, (cur_start, cur_end), best, best_range


# ---------------------------------------------------------------- REST stats
def rest_stats(user):
    u = json.loads(fetch(f"https://api.github.com/users/{user}"))
    repos = json.loads(fetch(f"https://api.github.com/users/{user}/repos?per_page=100"))
    stars = sum(r["stargazers_count"] for r in repos)
    langs = {}
    for r in repos:
        if r.get("fork"):
            continue
        for lang, n in json.loads(fetch(r["languages_url"])).items():
            langs[lang] = langs.get(lang, 0) + n
    return {"followers": u["followers"], "repos": u["public_repos"],
            "stars": stars, "langs": langs}


# ---------------------------------------------------------------- SVG helpers
def card(body):
    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'xmlns="http://www.w3.org/2000/svg" {FONT}>'
        f'<rect width="{W}" height="{H}" rx="{R}" fill="{BASE}"/>'
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="{R}" '
        f'fill="{CARD_BG}" stroke="#1e2230" stroke-width="1"/>'
        f'{body}</svg>'
    )


def fmt_date(ds):
    if not ds:
        return "—"
    try:
        d = date.fromisoformat(str(ds))
    except (ValueError, TypeError):
        return "—"
    return d.strftime("%b %-d")


def stats_card(s, total):
    rows = [("Total Contributions (year)", total, TEAL),
            ("Total Stars Earned", s["stars"], LAVENDER),
            ("Public Repositories", s["repos"], PINK),
            ("Followers", s["followers"], BLUE)]
    body = [f'<text x="24" y="34" fill="{LAVENDER}" font-size="17" font-weight="600">'
            f"Homam's GitHub Stats</text>"]
    y = 66
    for label, val, c in rows:
        body.append(f'<circle cx="30" cy="{y - 4}" r="3.5" fill="{c}"/>')
        body.append(f'<text x="44" y="{y}" fill="{TEXT}" font-size="14">{label}</text>')
        body.append(f'<text x="{W - 24}" y="{y}" fill="{TEXT}" font-size="14" '
                    f'font-weight="700" text-anchor="end">{val}</text>')
        y += 28
    return card("".join(body))


def streak_card(total, cur, cur_range, best, best_range):
    cx = W / 2
    body = [
        # left column: total
        f'<text x="{W * 0.18}" y="72" fill="{TEXT}" font-size="26" font-weight="700" '
        f'text-anchor="middle">{total}</text>',
        f'<text x="{W * 0.18}" y="98" fill="{LAVENDER}" font-size="12" text-anchor="middle">Total (year)</text>',
        # center: current streak with ring
        f'<circle cx="{cx}" cy="74" r="36" fill="none" stroke="{PURPLE}" stroke-width="4"/>',
        f'<text x="{cx}" y="82" fill="{TEXT}" font-size="26" font-weight="700" '
        f'text-anchor="middle">{cur}</text>',
        f'<text x="{cx}" y="128" fill="{TEAL}" font-size="13" font-weight="600" '
        f'text-anchor="middle">Current Streak</text>',
        f'<text x="{cx}" y="146" fill="{DIM}" font-size="10" text-anchor="middle">'
        f'{fmt_date(cur_range[0])} - {fmt_date(cur_range[1])}</text>'
        if (cur and cur_range and cur_range[0] and cur_range[1]) else "",
        # right column: longest
        f'<text x="{W * 0.82}" y="72" fill="{TEXT}" font-size="26" font-weight="700" '
        f'text-anchor="middle">{best}</text>',
        f'<text x="{W * 0.82}" y="98" fill="{LAVENDER}" font-size="12" text-anchor="middle">Longest Streak</text>',
        f'<text x="{W * 0.82}" y="114" fill="{DIM}" font-size="10" text-anchor="middle">'
        f'{fmt_date(best_range[0])} - {fmt_date(best_range[1])}</text>'
        if (best and best_range and best_range[0] and best_range[1]) else "",
        f'<text x="{W * 0.18}" y="114" fill="{DIM}" font-size="10" text-anchor="middle">last 365 days</text>',
    ]
    return card("".join(body))


def langs_card(langs):
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    total = sum(v for _, v in top) or 1
    colors = [PURPLE, TEAL, PINK, BLUE, LAVENDER, MINT]
    body = [f'<text x="24" y="34" fill="{LAVENDER}" font-size="17" font-weight="600">'
            f'Most Used Languages</text>']
    # stacked bar
    x, bw = 24.0, W - 48
    body.append(f'<clipPath id="bar"><rect x="24" y="50" width="{bw}" height="10" rx="5"/></clipPath>')
    for i, (lang, v) in enumerate(top):
        w = bw * v / total
        body.append(f'<rect x="{x:.1f}" y="50" width="{w:.1f}" height="10" '
                    f'fill="{colors[i]}" clip-path="url(#bar)"/>')
        x += w
    # legend, two columns
    for i, (lang, v) in enumerate(top):
        cx0 = 24 + (i % 2) * (W / 2 - 24)
        cy0 = 86 + (i // 2) * 26
        pct = 100 * v / total
        body.append(f'<circle cx="{cx0 + 5}" cy="{cy0 - 4}" r="5" fill="{colors[i]}"/>')
        body.append(f'<text x="{cx0 + 18}" y="{cy0}" fill="{TEXT}" font-size="13">'
                    f'{lang} <tspan fill="{DIM}">{pct:.1f}%</tspan></text>')
    return card("".join(body))


os.makedirs(OUT, exist_ok=True)
cal = contributions(USER)
total, cur, cur_range, best, best_range = streaks(cal)
s = rest_stats(USER)
open(f"{OUT}/stats-card.svg", "w").write(stats_card(s, total))
open(f"{OUT}/streak-card.svg", "w").write(streak_card(total, cur, cur_range, best, best_range))
open(f"{OUT}/top-langs-card.svg", "w").write(langs_card(s["langs"]))
print(f"wrote {OUT}/stats-card.svg streak-card.svg top-langs-card.svg | "
      f"total={total} cur={cur} best={best} langs={len(s['langs'])}")
