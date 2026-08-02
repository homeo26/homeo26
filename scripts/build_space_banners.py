#!/usr/bin/env python3
"""Generate the animated dark-space banner + footer SVGs.

Recreates the Cybertron Console 'aurora silk' WebGL aesthetic
(BackgroundCanvas.tsx) as pure SMIL-animated SVG that GitHub READMEs
can render: dark #0b0d12 space base, blurred purple/teal/pink aurora
ribbons drifting slowly, a twinkling starfield, and a soft vignette.
"""
import random

BASE = "#0b0d12"
PURPLE, TEAL, PINK = "#7c3aed", "#14b8a6", "#ec4899"
TEXT, DIM = "#e6e8ef", "#9ca3af"
random.seed(26)


def stars(w, h, n):
    out = []
    for _ in range(n):
        x, y = round(random.uniform(0, w), 1), round(random.uniform(0, h), 1)
        r = round(random.uniform(0.4, 1.4), 2)
        base_o = round(random.uniform(0.25, 0.9), 2)
        dur = round(random.uniform(2.5, 7.0), 1)
        begin = round(random.uniform(0, 5), 1)
        out.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="#e6e8ef" opacity="{base_o}">'
            f'<animate attributeName="opacity" values="{base_o};{max(0.05, base_o - 0.5)};{base_o}" '
            f'dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></circle>'
        )
    return "".join(out)


def aurora(w, h):
    """Three blurred radial blobs drifting horizontally, like the fBm ribbons."""
    blobs = [
        (PURPLE, 0.30 * w, 0.55 * h, 0.38 * w, 0.9 * h, 0.55, 26, 0.10 * w),
        (TEAL,   0.62 * w, 0.35 * h, 0.34 * w, 0.8 * h, 0.45, 32, -0.12 * w),
        (PINK,   0.85 * w, 0.70 * h, 0.30 * w, 0.7 * h, 0.40, 22, 0.08 * w),
    ]
    parts = []
    for i, (c, cx, cy, rx, ry, op, dur, drift) in enumerate(blobs):
        parts.append(
            f'<g filter="url(#blur)">'
            f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" fill="{c}" opacity="{op}">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0; {drift:.0f} {(-1) ** i * 8}; 0 0" dur="{dur}s" repeatCount="indefinite"/>'
            f'</ellipse></g>'
        )
    return "".join(parts)


def svg(w, h, body):
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="\'JetBrains Mono\',\'Fira Code\',monospace">'
        f'<defs>'
        f'<filter id="blur" x="-60%" y="-60%" width="220%" height="220%">'
        f'<feGaussianBlur stdDeviation="55"/></filter>'
        f'<radialGradient id="vig" cx="50%" cy="50%" r="75%">'
        f'<stop offset="60%" stop-color="{BASE}" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="#000" stop-opacity="0.45"/></radialGradient>'
        f'</defs>'
        f'<rect width="{w}" height="{h}" fill="{BASE}"/>'
        f'{aurora(w, h)}'
        f'{stars(w, h, max(30, w * h // 4200))}'
        f'<rect width="{w}" height="{h}" fill="url(#vig)"/>'
        f'{body}'
        f'</svg>'
    )


BANNER_W, BANNER_H = 1200, 220
banner_text = (
    f'<text x="{BANNER_W / 2}" y="104" text-anchor="middle" fill="{TEXT}" '
    f'font-size="46" font-weight="700" opacity="1">Homam Manasra'
    f'<animate attributeName="opacity" values="0;1" dur="1.6s" fill="freeze" restart="never"/></text>'
    f'<text x="{BANNER_W / 2}" y="148" text-anchor="middle" fill="{DIM}" '
    f'font-size="19" opacity="1">SDE @ Amazon &#183; Competitive Programmer'
    f'<animate attributeName="opacity" values="0;1" dur="2.4s" fill="freeze" restart="never"/></text>'
)
open("assets/space-banner.svg", "w").write(svg(BANNER_W, BANNER_H, banner_text))
open("assets/space-footer.svg", "w").write(svg(1200, 120, ""))
print("wrote assets/space-banner.svg and assets/space-footer.svg")
