#!/usr/bin/env python3
"""Compose a skillicons-style tech stack strip as one self-hosted SVG.

Fetches each icon's inner artwork, validates it is non-empty, and lays
them out in a grid (14 per line -> 2 rows). Groovy has no artwork on any
skillicons-style service, so its cell is composed from the simple-icons
logo on a matching #242938 rounded tile.
"""
import re, sys, urllib.request

ICONS = ["java", "kotlin", "groovy", "py", "cpp", "ruby", "js", "ts",
         "bash", "html", "css", "react", "reactnative", "nextjs",
         "spring", "nodejs", "aws", "gcp", "dynamodb", "postgres",
         "mysql", "docker", "kubernetes", "linux", "git", "github",
         "gradle", "idea"]
PER_LINE = 14
CELL, STEP = 256, 300  # skillicons geometry: 256px tiles, 44px gaps
SCALE = 2356 / 441.75  # skillicons display scale


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def inner_svg(name, source):
    body = fetch(source)
    m = re.search(r'<g transform="translate\(0, 0\)">\s*(<svg.*?</svg>)\s*</g>',
                  body, re.S)
    if not m:
        sys.exit(f"FATAL: no inner svg for {name}")
    art = m.group(1)
    # strip outer wrapper, keep content; ensure real artwork exists
    content = re.sub(r'^<svg[^>]*>|</svg>$', '', art, flags=re.S).strip()
    if len(content) < 100:
        sys.exit(f"FATAL: empty artwork for {name} ({len(content)} chars)")
    return content


def groovy_cell():
    logo = fetch("https://cdn.simpleicons.org/apachegroovy/FFFFFF")
    m = re.search(r'<path[^>]*d="([^"]+)"', logo)
    if not m:
        sys.exit("FATAL: no groovy path")
    return (f'<rect width="256" height="256" fill="#242938" rx="60"/>'
            f'<g transform="translate(38,38) scale(7.5)">'
            f'<path fill="#4298B8" d="{m.group(1)}"/></g>')


cells = []
for i, name in enumerate(ICONS):
    x, y = (i % PER_LINE) * STEP, (i // PER_LINE) * STEP
    if name == "groovy":
        content = groovy_cell()
    elif name == "reactnative":
        content = inner_svg(name, f"https://go-skill-icons.vercel.app/api/icons?i={name}&theme=dark")
    else:
        content = inner_svg(name, f"https://skillicons.dev/icons?i={name}&theme=dark")
    cells.append(f'<g transform="translate({x}, {y})">'
                 f'<svg width="{CELL}" height="{CELL}" fill="none" viewBox="0 0 256 256">'
                 f'{content}</svg></g>')

cols = min(PER_LINE, len(ICONS))
rows = (len(ICONS) + PER_LINE - 1) // PER_LINE
vw, vh = cols * STEP - (STEP - CELL), rows * STEP - (STEP - CELL)
svg = (f'<svg width="{vw / SCALE:.2f}" height="{vh / SCALE:.2f}" '
       f'viewBox="0 0 {vw} {vh}" fill="none" xmlns="http://www.w3.org/2000/svg">'
       + "".join(cells) + "</svg>")
open("assets/tech-stack.svg", "w").write(svg)
print(f"wrote assets/tech-stack.svg: {len(ICONS)} icons, {rows} rows, "
      f"{vw / SCALE:.0f}x{vh / SCALE:.0f}px display size")
