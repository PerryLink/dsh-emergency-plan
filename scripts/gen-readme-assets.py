#!/usr/bin/env python3
"""Generate README image assets for dsh-emergency-plan (docs/assets/).

Outputs (idempotent overwrite):
  dsh-emergency-plan-flow-light.svg / dsh-emergency-plan-flow-dark.svg
      Hero pipeline diagram. Two hand-written SVG files (vector - never
      rasterized to webp). Every label inside is a command/surface token
      (plan.json, emergency_plan, rules/emergency-plan.yaml, EP-001..EP-009,
      issues[], skipped[], config keys), so all five README languages share
      the same pair.

The older single-theme dsh-emergency-plan-flow.svg, dsh-emergency-plan-hero.png,
dsh-emergency-plan-demo.* and quickstart.* stay untouched in docs/assets/: the
README no longer references them, but external links keep working.

Run once:  python scripts/gen-readme-assets.py
Requires:  Pillow (bundled with the DSH primary runtime)
"""
from __future__ import annotations

import os
import sys

from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")

# --- palette: PerryLink family (accent) + GitHub page backgrounds ----------
FAMILY = "#4B67B4"   # family accent (badges use labelColor #2B3245)
GREEN = {"light": "#16a34a", "dark": "#3fb950"}
SKIN = {
    "light": dict(bg="#ffffff", box="#f6f8fa", border="#d0d7de",
                  text="#1f2328", sub="#57606a"),
    "dark": dict(bg="#0d1117", box="#161b22", border="#30363d",
                 text="#f0f6fc", sub="#8b949e"),
}

# --- CJK font probe: kept from the family template. SVG labels are ASCII
# tokens today, but the checklist requires the probe so a future Chinese
# label can never render as tofu boxes. --------------------------------
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",      # Microsoft YaHei
    r"C:\Windows\Fonts\simhei.ttf",    # SimHei
    r"C:\Windows\Fonts\Deng.ttf",      # DengXian
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
if FONT_PATH is None:
    sys.exit("FATAL: no CJK font found (looked for msyh.ttc, simhei.ttf, "
             "Deng.ttf, Noto Sans CJK, PingFang). Refusing to risk tofu "
             "boxes; install one of the probed fonts and re-run.")


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


# ---------------------------------------------------------------------------
# Hero pipeline SVG (light + dark)
# ---------------------------------------------------------------------------
# Three pipeline stages plus the rule pack that the tool applies. Every label
# is a command-surface token, never a natural-language sentence.
STAGES = [
    ("plan.json / plan.yaml", "sections[] · page · body"),
    ("emergency_plan", "tool · JSON | YAML"),
    ("issues[] + skipped[]", "found · expected · fix"),
]
PACK = ("rules/emergency-plan.yaml",
        "EP-001 … EP-009 · direct · principle · local")
CONFIG = ("config: rulesFile · disabledRules · onlyRules · "
          "skipNotes · timeoutMs")
FOOTER = "GB/T 29639-2020 · rules/evidence/ · Apache-2.0"


def flow_svg(skin: str) -> str:
    s = SKIN[skin]
    w, h = 1200, 480
    nw, nh, gap = 300, 120, 60
    y0 = 150
    xs = [70, 450, 830]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="dsh-emergency-plan pipeline">',
        '<title>dsh-emergency-plan pipeline</title>',
        f'<rect width="{w}" height="{h}" rx="18" fill="{s["bg"]}"/>',
        f'<text x="60" y="62" fill="{s["text"]}" '
        f'font-family="ui-sans-serif,system-ui,sans-serif" font-size="30" '
        f'font-weight="700">dsh-emergency-plan</text>',
        f'<text x="60" y="94" fill="{s["sub"]}" '
        f'font-family="ui-monospace,monospace" font-size="16">'
        f'plan.json / plan.yaml → emergency_plan → issues[] + skipped[]'
        f'</text>',
        f'<line x1="60" y1="118" x2="1140" y2="118" stroke="{s["border"]}"/>',
    ]
    for i, (label, sub) in enumerate(STAGES):
        x = xs[i]
        accent = FAMILY if i == 1 else (
            GREEN[skin] if i == len(STAGES) - 1 else s["border"])
        parts.append(
            f'<rect x="{x}" y="{y0}" width="{nw}" height="{nh}" rx="14" '
            f'fill="{s["box"]}" stroke="{accent}" stroke-width="2"/>')
        parts.append(
            f'<text x="{x + nw // 2}" y="{y0 + 52}" fill="{s["text"]}" '
            f'text-anchor="middle" font-family="ui-monospace,monospace" '
            f'font-size="18" font-weight="700">{label}</text>')
        parts.append(
            f'<text x="{x + nw // 2}" y="{y0 + 82}" fill="{s["sub"]}" '
            f'text-anchor="middle" font-family="ui-monospace,monospace" '
            f'font-size="13">{sub}</text>')
        if i < len(STAGES) - 1:
            ax = x + nw + 8
            ay = y0 + nh // 2
            parts.append(
                f'<path d="M{ax} {ay}h{gap - 20}" stroke="{s["sub"]}" '
                f'stroke-width="3"/>')
            parts.append(
                f'<path d="M{ax + gap - 26} {ay - 7}l10 7-10 7" fill="none" '
                f'stroke="{s["sub"]}" stroke-width="3" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
    # rule pack under the tool, connected by a dashed line
    pack_x, pack_w, pack_y, pack_h = 330, 540, 300, 70
    tool_cx = xs[1] + nw // 2
    parts.append(
        f'<path d="M{tool_cx} {y0 + nh}v{pack_y - y0 - nh}" '
        f'stroke="{FAMILY}" stroke-width="2" stroke-dasharray="5 5"/>')
    parts.append(
        f'<rect x="{pack_x}" y="{pack_y}" width="{pack_w}" '
        f'height="{pack_h}" rx="12" fill="{s["box"]}" stroke="{FAMILY}" '
        f'stroke-width="2"/>')
    parts.append(
        f'<text x="{pack_x + pack_w // 2}" y="{pack_y + 30}" '
        f'fill="{s["text"]}" text-anchor="middle" '
        f'font-family="ui-monospace,monospace" font-size="15" '
        f'font-weight="700">{PACK[0]}</text>')
    parts.append(
        f'<text x="{pack_x + pack_w // 2}" y="{pack_y + 52}" '
        f'fill="{s["sub"]}" text-anchor="middle" '
        f'font-family="ui-monospace,monospace" font-size="13">{PACK[1]}</text>')
    # config bar
    parts.append(
        f'<rect x="70" y="394" width="1060" height="44" rx="10" '
        f'fill="{s["box"]}" stroke="{s["border"]}"/>')
    parts.append(
        f'<text x="600" y="422" fill="{s["text"]}" text-anchor="middle" '
        f'font-family="ui-monospace,monospace" font-size="14">{CONFIG}</text>')
    # footer
    parts.append(
        f'<text x="60" y="466" fill="{s["sub"]}" '
        f'font-family="ui-monospace,monospace" font-size="13">{FOOTER}</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for skin in ("light", "dark"):
        path = os.path.join(OUT, f"dsh-emergency-plan-flow-{skin}.svg")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(flow_svg(skin))
    print("wrote 2 SVG assets to docs/assets/ "
          "(dsh-emergency-plan-flow-{light,dark}.svg)")


if __name__ == "__main__":
    main()
