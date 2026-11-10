#!/usr/bin/env python3
"""README visuals for dsh-emergency-plan, derived from the shipped pipeline.

Nothing here is a generic checker template; every number below was read off this
repository:

  `src/index.ts`        `emergency_plan` reads `file` or inline `material` and the
                        rule pack (`rulesFile`, else `config.rulesFile`), then
                        calls `parseMaterial` -> `runCheck` -> `buildView`.
  `src/parse.ts`        material is JSON, YAML or pasted text; the normalized
                        shape is `{ name, planType, sections[] }`, and each
                        section may carry `title / page / line / body`.
  `src/check.ts`        nine checks EP-001..EP-009. EP-001/002/003 walk the
                        element list of a plan type; EP-004..EP-009 are the
                        cross-cutting pass. Headings are matched in three
                        widening steps (normalized equality, containment, edit
                        distance <= 2). A locator falls back page -> line ->
                        heading, and is `{}` when none of the three exists.
  `src/view.ts`         every rule lands on exactly one side: an `issues[]`
                        entry (with `found / expected / basis / fix`) or a
                        `skipped[]` entry that states why it did not fire -
                        including "ran, no difference found".
  `src/shared/ruleset.ts`  `MAX_SEVERITY_BY_KIND`: direct <= error,
                        derived-from-principle <= warn,
                        institutional-configuration <= info.
  `rules/emergency-plan.yaml`  nine rules, version 2026.1; 5 warn + 4 info,
                        no error at all.

Two figures:

  hero 1440x576 (Pillow: zh/en x light/dark, four WebP files)
      Left column: kicker / wordmark / two value lines / two-line subtitle /
      one meta line / footer. Right side, top: the EP-001 element list 7.1-7.4
      laid against the headings it was found at, with page chips - 7.3 matched a
      heading with no body, 7.4 matched nothing. Right side, bottom: the
      evidence-kind ceiling of the rule pack, with the rules each kind covers.

  flow 1100x660 (hand-written SVG, light/dark - one pair serves five READMEs)
      Grammar: a CHECK BENCH - one element-list column, one three-step match
      gutter, one material column, one disposition column - not a row of nodes.
      Below the bench: the three-step legend, then a cross-cutting rail with the
      eight remaining rules and their state in the same pass. The bench forks
      into the two report exits (`issues[]`, `skipped[]`), because a rule can
      only ever land on one of them.

Text is measured before it is drawn; a label that would overflow aborts the run
instead of shipping clipped text. Labels in the SVG are English plus command
tokens (`sections[]`, `EP-001`, `issues[]`), so the same pair is honest in every
README language.

The older single-theme `dsh-emergency-plan-flow.svg`, `-flow-light/dark.svg`,
`-hero.png`, `-demo.*` and `quickstart.*` stay untouched in `docs/assets/`: the
READMEs no longer reference them, but external links keep working.

Run once:  python scripts/gen-readme-assets.py
Requires:  Pillow (bundled with the DSH primary runtime); Windows fonts
           msyh.ttc / msyhbd.ttc / consola.ttf.
"""
from __future__ import annotations

import os
from html import escape

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")
NAME = "dsh-emergency-plan"

FONT_FILES = {
    "cjk": r"C:\Windows\Fonts\msyh.ttc",
    "cjk_bold": r"C:\Windows\Fonts\msyhbd.ttc",
    "mono": r"C:\Windows\Fonts\consola.ttf",
    "mono_bold": r"C:\Windows\Fonts\consolab.ttf",
}
for _kind, _path in FONT_FILES.items():
    if not os.path.exists(_path):
        raise SystemExit(f"FATAL: font missing: {_path}")
os.makedirs(OUT, exist_ok=True)

SKIN = {
    "light": dict(
        bg_from="#f9f6fd", bg_to="#e4eaf8",
        card="#ffffff", band="#f8f5fc", edge="#e6e0f0",
        text="#141419", sub="#4d5261", faint="#8b90a2",
        accent="#4B67B4", accent_soft="#ece7f9",
        grid="#e9e4f2",
        amber="#b45309", amber_bg="#fdf4e8", amber_soft="#f0dcc4",
        ok="#15803d", ok_bg="#eaf6ee",
        skip="#7d8290", skip_bg="#eeeaf3",
        shadow=(43, 32, 74), shadow_alpha=16, glow=30,
        flood="#3b2f5c", flood_alpha=0.12,
    ),
    "dark": dict(
        bg_from="#131a2a", bg_to="#0c1016",
        card="#1b2231", band="#202839", edge="#2e374b",
        text="#f0f3f9", sub="#a8b1c4", faint="#7b8396",
        accent="#8496f5", accent_soft="#242d42",
        grid="#263045",
        amber="#d9a441", amber_bg="#2a2216", amber_soft="#3d3220",
        ok="#3fb950", ok_bg="#16281c",
        skip="#7b8396", skip_bg="#222a3a",
        shadow=(0, 0, 0), shadow_alpha=95, glow=46,
        flood="#000000", flood_alpha=0.45,
    ),
}


# --------------------------------------------------------------------------- #
# small drawing kit
# --------------------------------------------------------------------------- #


def font(size: int, kind: str = "cjk") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_FILES[kind], int(round(size)))


def hx(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def gradient(w: int, h: int, top: str, bottom: str) -> Image.Image:
    base = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(base)
    a, b = hx(top), hx(bottom)
    for y in range(h):
        t = 0.10 * (y / h) + 0.90 * (y / h) ** 1.25
        draw.line([(0, y), (w, y)],
                  fill=tuple(int(p + (q - p) * t) for p, q in zip(a, b)))
    return base


def glow(img: Image.Image, cx: int, cy: int, r: int, color: str,
         alpha: int) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rgb = hx(color)
    for i in range(10, 0, -1):
        rr = r * i / 10
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                  fill=rgb + (int(alpha * (1 - i / 11)),))
    return Image.alpha_composite(img.convert("RGBA"),
                                 layer.filter(ImageFilter.GaussianBlur(30))
                                 ).convert("RGB")


def shadows(img: Image.Image, boxes: list[tuple[tuple[int, int, int, int], int]],
            s: dict) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for (x0, y0, x1, y1), radius in boxes:
        for i in range(12, 0, -2):
            alpha = int(s["shadow_alpha"] * (1 - i / 13) ** 1.5)
            if alpha <= 0:
                continue
            ld.rounded_rectangle(
                [x0 - i * 0.35, y0 + i * 0.5, x1 + i * 0.35, y1 + i * 0.9],
                radius=radius + i * 0.4,
                fill=s["shadow"] + (alpha,))
    return Image.alpha_composite(
        img.convert("RGBA"), layer.filter(ImageFilter.GaussianBlur(16))
    ).convert("RGB")


_MEASURE = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def measure(text: str, size: float, kind: str) -> float:
    return _MEASURE.textlength(text, font=font(size, kind))


def require_w(text: str, size: float, kind: str, max_w: float,
              what: str) -> None:
    got = measure(text, size, kind)
    if got > max_w + 0.5:
        raise SystemExit(f"FATAL: {what} overflows: {text!r} needs "
                         f"{got:.1f}px > {max_w:.0f}px")


def fit(text: str, kind: str, max_w: float, start: int, minimum: int) -> int:
    size = start
    while size >= minimum:
        if measure(text, size, kind) <= max_w:
            return size
        size -= 1
    raise SystemExit(f"FATAL: text does not fit {max_w}px at >= {minimum}px: "
                     f"{text!r}")


def fit_lines(lines: list[str], kind: str, max_w: float, start: int,
              minimum: int) -> int:
    return min(fit(t, kind, max_w, start, minimum) for t in lines)


def pill(img: Image.Image, xy: tuple[int, int], text: str, s: dict,
         size: int = 16, fg: str | None = None, bg: str | None = None,
         kind: str = "cjk_bold", pad: int = 16) -> int:
    d = ImageDraw.Draw(img)
    f = font(size, kind)
    w = d.textlength(text, font=f)
    x, y = xy
    h = size + 19
    d.rounded_rectangle([x, y, x + w + pad * 2, y + h], radius=h / 2,
                        fill=hx(bg or s["accent_soft"]))
    d.text((x + pad, y + h / 2), text, font=f, fill=hx(fg or s["accent"]),
           anchor="lm")
    return int(x + w + pad * 2)


def dashed_rrect(d: ImageDraw.ImageDraw, box: tuple[float, float, float, float],
                 color: str, radius: int = 12, width: int = 2,
                 dash: int = 8, gap: int = 6) -> None:
    x0, y0, x1, y1 = box
    xa, xb = x0 + radius, x1 - radius
    for x in range(int(xa), int(xb), dash + gap):
        x_end = min(x + dash, xb)
        d.line([(x, y0), (x_end, y0)], fill=hx(color), width=width)
        d.line([(x, y1), (x_end, y1)], fill=hx(color), width=width)
    ya, yb = y0 + radius, y1 - radius
    for y in range(int(ya), int(yb), dash + gap):
        y_end = min(y + dash, yb)
        d.line([(x0, y), (x0, y_end)], fill=hx(color), width=width)
        d.line([(x1, y), (x1, y_end)], fill=hx(color), width=width)
    d.arc([x0, y0, x0 + 2 * radius, y0 + 2 * radius], 180, 270,
          fill=hx(color), width=width)
    d.arc([x1 - 2 * radius, y0, x1, y0 + 2 * radius], 270, 360,
          fill=hx(color), width=width)
    d.arc([x0, y1 - 2 * radius, x0 + 2 * radius, y1], 90, 180,
          fill=hx(color), width=width)
    d.arc([x1 - 2 * radius, y1 - 2 * radius, x1, y1], 0, 90,
          fill=hx(color), width=width)


# --------------------------------------------------------------------------- #
# hero content
# --------------------------------------------------------------------------- #
# The rows are one real material: a special plan (planType: special) whose third
# heading carries no body and whose fourth required element never appears. The
# finished report for exactly this material is 2 warn + 8 skipped, and the two
# issues are the last two rows of the EP-001 list.

HERO = {
    "zh": dict(
        kicker="DEEPSEEK HARNESS 插件 · 应急预案要素核对 · 只读",
        value=["逐条核对要素齐备性", "每条差异定位到页或行"],
        sub=["读章节树、标题、页码与正文，按声明类型套用 9 条规则；",
             "报出缺失、只有标题没有正文的章节，以及它们的位置。"],
        meta="emergency_plan · EP-001…EP-009 · issues[] + skipped[]",
        foot="Apache-2.0 · 纯本地只读 · 不联网 · 不调用模型 · 只列差异",
        a_head="专项应急预案 · 要素清单 7.1~7.4",
        a_tag="EP-001",
        a_rows=[
            ("7.1", "适用范围", "一、适用范围", "p.1", "ok", "有正文"),
            ("7.2", "应急组织机构及职责", "二、组织机构与职责", "p.2", "ok",
             "有正文"),
            ("7.3", "响应启动", "三、响应启动", "p.3", "warn",
             "只标题、无正文"),
            ("7.4", "处置措施", "材料中没有该章节", "—", "miss", "未找到"),
        ],
        a_loc="定位：page → line → 标题；三者都没有时留空",
        b_head="9 条规则 · 依据类型封顶级别",
        b_tag="2026.1",
        b_rows=[
            ("直接规定", "≤ error", "EP-001 002 003 004 009"),
            ("原则性推论", "≤ warn", "EP-005 006 007"),
            ("本机构配置", "≤ info", "EP-008"),
        ],
        b_foot="本包 warn 5 · info 4 · error 0 · 依据 GB/T 29639-2020",
    ),
    "en": dict(
        kicker="DEEPSEEK HARNESS PLUGIN · EMERGENCY PLAN · READ-ONLY",
        value=["Which elements are missing,", "and where each one sits"],
        sub=["Reads headings, pages and body, then applies nine rules for",
             "the declared plan type — gaps, empty headings, locations."],
        meta="emergency_plan · EP-001…EP-009 · issues[] + skipped[]",
        foot="Apache-2.0 · local and read-only · no network · no model call",
        a_head="Special plan · elements 7.1–7.4",
        a_tag="EP-001",
        a_rows=[
            ("7.1", "适用范围", "一、适用范围", "p.1", "ok", "body present"),
            ("7.2", "应急组织机构及职责", "二、组织机构与职责", "p.2", "ok",
             "body present"),
            ("7.3", "响应启动", "三、响应启动", "p.3", "warn", "heading only"),
            ("7.4", "处置措施", "no such section", "—", "miss", "not found"),
        ],
        a_loc="locator · page → line → heading; empty when none of the three",
        b_head="9 rules · evidence kind caps severity",
        b_tag="2026.1",
        b_rows=[
            ("direct", "≤ error", "EP-001 002 003 004 009"),
            ("derived-from-principle", "≤ warn", "EP-005 006 007"),
            ("institutional-configuration", "≤ info", "EP-008"),
        ],
        b_foot="this pack: warn 5 · info 4 · error 0 · GB/T 29639-2020",
    ),
}

HERO_W, HERO_H = 1440, 576
LEFT_X, LEFT_W = 60, 620
CARD_A = (700, 52, 1384, 372)
CARD_B = (700, 388, 1384, 540)
A_PAD = 24
ROW_TOP, ROW_H, ROW_GAP = 112, 46, 9


def hero(lang: str, skin: str) -> Image.Image:
    s = SKIN[skin]
    h = HERO[lang]
    img = gradient(HERO_W, HERO_H, s["bg_from"], s["bg_to"])
    img = glow(img, 1170, 70, 430, s["accent"], s["glow"])
    img = glow(img, 150, 572, 340, s["accent"], max(8, s["glow"] // 3))
    img = shadows(img, [(CARD_A, 20), (CARD_B, 18)], s)
    d = ImageDraw.Draw(img)

    # ---- left column -------------------------------------------------------
    right = pill(img, (LEFT_X, 50), h["kicker"], s, size=16)
    if right > LEFT_X + LEFT_W:
        raise SystemExit(f"FATAL: kicker overflows ({right - LEFT_X}px)")
    d = ImageDraw.Draw(img)

    title_size = fit(NAME, "mono_bold", LEFT_W, 56, 48)
    require_w(NAME, title_size, "mono_bold", LEFT_W, "hero title")
    d.text((LEFT_X - 2, 152), NAME, font=font(title_size, "mono_bold"),
           fill=hx(s["text"]), anchor="ls")

    value_size = fit_lines(h["value"], "cjk_bold", LEFT_W, 48, 40)
    for i, line in enumerate(h["value"]):
        require_w(line, value_size, "cjk_bold", LEFT_W, "hero value line")
        d.text((LEFT_X, 232 + i * 58), line,
               font=font(value_size, "cjk_bold"), fill=hx(s["text"]),
               anchor="ls")

    sub_size = fit_lines(h["sub"], "cjk", LEFT_W, 22, 18)
    for i, line in enumerate(h["sub"]):
        require_w(line, sub_size, "cjk", LEFT_W, "hero subtitle")
        d.text((LEFT_X, 344 + i * 30), line, font=font(sub_size, "cjk"),
               fill=hx(s["sub"]), anchor="ls")

    require_w(h["meta"], 19, "mono", LEFT_W, "hero meta")
    d.text((LEFT_X - 1, 428), h["meta"], font=font(19, "mono"),
           fill=hx(s["faint"]), anchor="ls")

    d.line([LEFT_X, 470, LEFT_X + LEFT_W - 14, 470], fill=hx(s["grid"]),
           width=2)
    require_w(h["foot"], 16, "cjk", LEFT_W, "hero footer")
    d.text((LEFT_X, 496), h["foot"], font=font(16, "cjk"), fill=hx(s["faint"]),
           anchor="ls")

    # ---- card A: EP-001 element list 7.1-7.4 vs the headings --------------
    ax0, ay0, ax1, ay1 = CARD_A
    d.rounded_rectangle(CARD_A, radius=20, fill=hx(s["card"]),
                        outline=hx(s["edge"]), width=2)
    inner_l, inner_r = ax0 + A_PAD, ax1 - A_PAD
    d.text((inner_l, ay0 + 32), h["a_head"], font=font(15, "cjk_bold"),
           fill=hx(s["text"]), anchor="ls")
    require_w(h["a_head"], 15, "cjk_bold", inner_r - inner_l - 90,
              "hero card A head")
    tag = h["a_tag"]
    tag_w = measure(tag, 10.5, "mono_bold") + 20
    d.rounded_rectangle([inner_r - tag_w, ay0 + 17, inner_r, ay0 + 41],
                        radius=12, fill=hx(s["accent_soft"]))
    d.text((inner_r - tag_w / 2, ay0 + 30), tag, font=font(10.5, "mono_bold"),
           fill=hx(s["accent"]), anchor="mm")
    d.line([inner_l, ay0 + 50, inner_r, ay0 + 50], fill=hx(s["grid"]), width=2)

    for i, (code, element, where, page, state, label) in enumerate(h["a_rows"]):
        top = ROW_TOP + i * (ROW_H + ROW_GAP)
        box = (inner_l, top, inner_r, top + ROW_H)
        if state == "miss":
            dashed_rrect(d, box, s["faint"], radius=12, width=2)
        else:
            fill = s["amber_bg"] if state == "warn" else s["band"]
            edge = s["amber_soft"] if state == "warn" else s["grid"]
            d.rounded_rectangle(box, radius=12, fill=hx(fill),
                                outline=hx(edge), width=2)
        # element number chip
        chip_x0 = inner_l + 16
        d.rounded_rectangle([chip_x0, top + 13, chip_x0 + 34, top + 33],
                            radius=7, fill=hx(s["accent_soft"]))
        d.text((chip_x0 + 17, top + 23), code, font=font(10.5, "mono_bold"),
               fill=hx(s["accent"]), anchor="mm")
        # element name
        name_size = 13.5
        require_w(element, name_size, "cjk_bold", 140, f"{code} hero element")
        d.text((inner_l + 62, top + 29), element,
               font=font(name_size, "cjk_bold"),
               fill=hx(s["text"] if state != "miss" else s["sub"]),
               anchor="ls")
        # matched heading
        where_size = 12.5
        require_w(where, where_size, "cjk", 145, f"{code} hero heading")
        d.text((inner_l + 210, top + 29), where, font=font(where_size, "cjk"),
               fill=hx(s["faint"]), anchor="ls")
        # state marker + label
        cx, cy = inner_l + 362, top + ROW_H / 2
        if state == "ok":
            d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=hx(s["ok"]))
        elif state == "warn":
            d.ellipse([cx - 5.5, cy - 5.5, cx + 5.5, cy + 5.5],
                      outline=hx(s["amber"]), width=2)
        else:
            d.ellipse([cx - 5.5, cy - 5.5, cx + 5.5, cy + 5.5],
                      outline=hx(s["faint"]), width=2)
        state_color = {"ok": s["ok"], "warn": s["amber"],
                       "miss": s["faint"]}[state]
        require_w(label, 12, "cjk", 160, f"{code} hero state")
        d.text((inner_l + 378, top + 29), label, font=font(12, "cjk"),
               fill=hx(state_color), anchor="ls")
        # page / locator on the right edge
        d.text((inner_r - 10, top + 29), page, font=font(12, "mono"),
               fill=hx(s["sub"] if state != "miss" else s["faint"]),
               anchor="rs")

    require_w(h["a_loc"], 11.5, "cjk", inner_r - inner_l, "hero card A locator")
    d.text((inner_l, ay0 + 296), h["a_loc"], font=font(11.5, "cjk"),
           fill=hx(s["faint"]), anchor="ls")

    # ---- card B: the evidence-kind ceiling of the rule pack ---------------
    bx0, by0, bx1, by1 = CARD_B
    d.rounded_rectangle(CARD_B, radius=18, fill=hx(s["card"]),
                        outline=hx(s["edge"]), width=2)
    d.text((inner_l, by0 + 28), h["b_head"], font=font(13.5, "cjk_bold"),
           fill=hx(s["text"]), anchor="ls")
    btag = h["b_tag"]
    btag_w = measure(btag, 10, "mono") + 18
    d.rounded_rectangle([inner_r - btag_w, by0 + 13, inner_r, by0 + 35],
                        radius=11, fill=hx(s["band"]),
                        outline=hx(s["grid"]), width=1)
    d.text((inner_r - btag_w / 2, by0 + 24), btag, font=font(10, "mono"),
           fill=hx(s["faint"]), anchor="mm")
    d.line([inner_l, by0 + 44, inner_r, by0 + 44], fill=hx(s["grid"]), width=2)

    label_kind = "cjk" if lang == "zh" else "mono"
    label_size = 13 if lang == "zh" else 11.5
    ids_x = 940
    cap_w = int(max(measure(cap, 11, "cjk_bold")
                    for _, cap, _ in h["b_rows"])) + 26
    cap_x = inner_r - 10 - cap_w
    for i, (label, cap, ids) in enumerate(h["b_rows"]):
        by = by0 + 62 + i * 22
        require_w(label, label_size, label_kind, ids_x - inner_l - 24,
                  "hero card B label")
        d.text((inner_l, by), label, font=font(label_size, label_kind),
               fill=hx(s["text"]), anchor="ls")
        require_w(ids, 10.5, "mono", cap_x - ids_x - 20, "hero card B ids")
        d.text((ids_x, by), ids, font=font(10.5, "mono"), fill=hx(s["faint"]),
               anchor="ls")
        # dotted leader from the rule ids to the ceiling chip
        lx = ids_x + measure(ids, 10.5, "mono") + 14
        while lx < cap_x - 10:
            d.line([(lx, by - 4), (lx + 3, by - 4)], fill=hx(s["grid"]),
                   width=2)
            lx += 8
        d.rounded_rectangle([cap_x, by - 15, cap_x + cap_w, by + 5],
                            radius=10,
                            fill=hx(s["accent_soft"] if i == 0 else s["band"]))
        d.text((cap_x + cap_w / 2, by - 5), cap, font=font(11, "cjk_bold"),
               fill=hx(s["accent"]), anchor="mm")

    require_w(h["b_foot"], 11, "cjk", inner_r - inner_l, "hero card B foot")
    d.text((inner_l, by0 + 132), h["b_foot"], font=font(11, "cjk"),
           fill=hx(s["faint"]), anchor="ls")

    return img


# --------------------------------------------------------------------------- #
# flow SVG: the check bench
# --------------------------------------------------------------------------- #

FONT_SANS = ("'Microsoft YaHei','Segoe UI',ui-sans-serif,system-ui,"
             "sans-serif")
FONT_MONO = "ui-monospace,Consolas,'Courier New',monospace"
FLOW_W, FLOW_H = 1100, 660

# one element-list column: code, element, match step, heading, page, state,
# state text, disposition tag
FLOW_ROWS = [
    ("7.1", "适用范围", "1", "一、适用范围", "p.1", "ok",
     "✓ body present", "no entry"),
    ("7.2", "应急组织机构及职责", "3", "二、组织机构与职责", "p.2", "ok",
     "✓ body present", "no entry"),
    ("7.3", "响应启动", "1", "三、响应启动", "p.3", "warn",
     "⚠ heading only", "issues[] · p.3"),
    ("7.4", "处置措施", "—", "— no heading", "—", "miss",
     "✕ not found", "issues[] · {}"),
]

# the other eight rules, and what they did in the same pass
FLOW_CROSS = [
    ("EP-002", "n/a"), ("EP-003", "n/a"), ("EP-004", "clean"),
    ("EP-005", "clean"), ("EP-006", "3/3 pages"), ("EP-007", "clean"),
    ("EP-008", "off"), ("EP-009", "off"),
]
CROSS_COLOR = {"n/a": "skip", "clean": "ok", "3/3 pages": "ok", "off": "skip"}

FLOW_ISSUES = [
    ("EP-001 · warn · p.3", "found: 「响应启动」heading, no body beneath"),
    ("EP-001 · warn · {}", "found: 「处置措施」not in the material"),
]
FLOW_SKIPPED = [
    "EP-002 / EP-003 · not applicable (planType: special)",
    "EP-004 / EP-005 / EP-007 · ran, no difference found",
    "EP-006 · 3 / 3 sections carry pages (minPageRatio 0.5)",
    "EP-008 · versionPatterns empty → not executed",
    "EP-009 · requireAttachments=false → off by default",
]


class Svg:
    """Tiny string builder for one hand-written SVG document."""

    def __init__(self) -> None:
        self.parts: list[str] = []

    def add(self, chunk: str) -> None:
        self.parts.append(chunk)

    def rect(self, x: float, y: float, w: float, h: float, fill: str,
             r: float = 0, stroke: str | None = None, sw: float = 1,
             extra: str = "") -> None:
        self.add(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
                 f'rx="{r:g}" fill="{fill}"'
                 + (f' stroke="{stroke}" stroke-width="{sw:g}"' if stroke else "")
                 + extra + "/>")

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str,
             sw: float = 1, dash: str | None = None) -> None:
        self.add(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" '
                 f'stroke="{stroke}" stroke-width="{sw:g}"'
                 + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")

    def circle(self, cx: float, cy: float, r: float, fill: str | None = None,
               stroke: str | None = None, sw: float = 1) -> None:
        self.add(f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" '
                 f'fill="{fill or "none"}"'
                 + (f' stroke="{stroke}" stroke-width="{sw:g}"' if stroke else "")
                 + "/>")

    def path(self, d: str, stroke: str, sw: float = 1,
             dash: str | None = None) -> None:
        self.add(f'<path d="{d}" fill="none" stroke="{stroke}" '
                 f'stroke-width="{sw:g}" stroke-linecap="round" '
                 f'stroke-linejoin="round"'
                 + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")

    def text(self, x: float, y: float, s: str, size: float, fill: str,
             family: str = "sans", weight: str = "400",
             anchor: str = "start", spacing: float | None = None) -> None:
        extra = f' letter-spacing="{spacing:g}"' if spacing is not None else ""
        face = FONT_MONO if family == "mono" else FONT_SANS
        self.add(f'<text x="{x:g}" y="{y:g}" fill="{fill}" '
                 f'font-family="{face}" font-size="{size:g}" '
                 f'font-weight="{weight}" text-anchor="{anchor}"{extra}>'
                 f'{escape(s)}</text>')

    def guard(self, s: str, size: float, family: str, max_w: float,
              what: str) -> None:
        kind = "mono" if family == "mono" else "cjk"
        got = measure(s, size, kind) * 1.06  # browser slack
        if got > max_w + 0.5:
            raise SystemExit(f"FATAL: svg {what} overflows: {s!r} needs "
                             f"{got:.1f}px > {max_w:.0f}px")


def arrow(svg: Svg, x1: float, y1: float, x2: float, y2: float, color: str,
          sw: float = 1.6) -> None:
    """Straight arrow; only horizontal and vertical ones are used here."""
    svg.line(x1, y1, x2, y2, color, sw)
    if y1 == y2:
        sign = 1 if x2 > x1 else -1
        svg.path(f"M{x2 - 6 * sign:g} {y2 - 4.5:g}L{x2:g} {y2:g}"
                 f"L{x2 - 6 * sign:g} {y2 + 4.5:g}", color, sw)
    else:
        sign = 1 if y2 > y1 else -1
        svg.path(f"M{x2 - 4.5:g} {y2 - 6 * sign:g}L{x2:g} {y2:g}"
                 f"L{x2 + 4.5:g} {y2 - 6 * sign:g}", color, sw)


def flow_svg(skin: str) -> str:
    s = SKIN[skin]
    svg = Svg()
    svg.add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{FLOW_W}" '
            f'height="{FLOW_H}" viewBox="0 0 {FLOW_W} {FLOW_H}" role="img" '
            f'aria-labelledby="t d">')
    svg.add('<title id="t">dsh-emergency-plan — check bench</title>')
    svg.add(
        '<desc id="d">One element list (EP-001, 7.1-7.4) laid against the '
        'material headings in three widening match steps; each row ends in a '
        'disposition. The bench forks into the two report exits: issues[] and '
        'skipped[]. A cross-cutting rail carries EP-002 to EP-009 and their '
        'state in the same pass.</desc>')
    svg.add("<defs>")
    svg.add(f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{s["bg_from"]}"/>'
            f'<stop offset="1" stop-color="{s["bg_to"]}"/></linearGradient>')
    svg.add(f'<filter id="soft" x="-8%" y="-14%" width="116%" height="132%">'
            f'<feDropShadow dx="0" dy="5" stdDeviation="11" '
            f'flood-color="{s["flood"]}" '
            f'flood-opacity="{s["flood_alpha"]}"/></filter>')
    svg.add("</defs>")
    svg.add(f'<rect width="{FLOW_W}" height="{FLOW_H}" rx="22" fill="url(#bg)"/>')
    svg.add(f'<rect x="0.5" y="0.5" width="{FLOW_W - 1}" height="{FLOW_H - 1}" '
            f'rx="22" fill="none" stroke="{s["edge"]}"/>')

    # ---- title -------------------------------------------------------------
    svg.text(40, 52, "STRUCTURE · CHECK BENCH", 11, s["accent"],
             family="mono", weight="700", spacing=1.6)
    title = "One element list, one section tree, two exits"
    svg.text(40, 88, title, 21, s["text"], weight="700")
    svg.guard(title, 21, "sans", 700, "title")
    sub = ("material → sections[] + planType → EP-001 elements 7.1–7.4 → "
           "three-step heading match → issues[] / skipped[]")
    svg.text(40, 112, sub, 11.5, s["sub"], family="mono")
    svg.guard(sub, 11.5, "mono", 1020, "subtitle")

    pack = "rules/emergency-plan.yaml · 9 rules · 2026.1"
    pw = measure(pack, 10.5, "mono") * 1.06
    svg.rect(1060 - pw - 24, 38, pw + 24, 24, s["card"], 12, s["edge"], 1,
             ' filter="url(#soft)"')
    svg.text(1060 - 12, 54, pack, 10.5, s["faint"], family="mono",
             anchor="end")
    svg.line(40, 124, 1060, 124, s["grid"], 1)

    # ---- worksheet card ----------------------------------------------------
    svg.rect(40, 136, 1020, 334, s["card"], 18, s["edge"], 1.2,
             ' filter="url(#soft)"')
    # header band: rounded top, square bottom
    svg.add(f'<path d="M40 154a18 18 0 0 1 18 -18h984a18 18 0 0 1 18 18'
            f'v22h-1020z" fill="{s["band"]}"/>')
    heads = [
        (64, "ELEMENT LIST · EP-001 7.1–7.4", "sans"),
        (330, "MATCH", "mono"),
        (432, "MATERIAL · sections[] · planType: special", "mono"),
        (760, "DISPOSITION", "sans"),
    ]
    for x, label, family in heads:
        svg.text(x, 162, label, 11, s["accent"], family=family, weight="700")
        svg.guard(label, 11, family, 300, f"column head {label}")

    # ---- the four rows of the bench ---------------------------------------
    for i, (code, element, step, heading, page, state, state_text,
            tag) in enumerate(FLOW_ROWS):
        top = 176 + i * 49
        mid = top + 20
        base = top + 27
        if i % 2 == 1:
            svg.rect(56, top, 1008, 41, s["band"], 10)
        svg.line(64, top + 41, 1036, top + 41, s["grid"], 1)
        # element code chip
        svg.rect(64, top + 11, 35, 19, s["accent_soft"], 6)
        svg.text(81.5, mid + 3.5, code, 10.5, s["accent"], family="mono",
                 weight="700", anchor="middle")
        # element name
        svg.text(110, base, element, 14, s["text"], weight="700")
        svg.guard(element, 14, "sans", 140, f"{code} element")
        # match step badge
        if state == "miss":
            svg.circle(350, mid, 11, "none", s["faint"], 1.4)
            svg.text(350, mid + 4, step, 11, s["faint"], family="mono",
                     anchor="middle")
        else:
            svg.circle(350, mid, 11, s["accent_soft"])
            svg.text(350, mid + 4, step, 12, s["accent"], family="mono",
                     weight="700", anchor="middle")
        # heading + page chip
        if state == "miss":
            svg.text(432, base, heading, 12.5, s["faint"])
        else:
            svg.text(432, base, heading, 13.5, s["sub"])
        svg.guard(heading, 13.5, "sans", 230, f"{code} heading")
        if page != "—":
            svg.rect(682, top + 10, 44, 19, s["band"], 6, s["grid"], 1)
            svg.text(704, mid + 3.5, page, 10.5, s["faint"], family="mono",
                     anchor="middle")
        # disposition
        color = {"ok": "ok", "warn": "amber", "miss": "amber"}[state]
        svg.text(760, base, state_text, 12.5, s["amber"] if state != "ok"
                 else s["ok"])
        svg.guard(state_text, 12.5, "sans", 112, f"{code} state")
        svg.text(884, base, "→", 11, s["faint"], family="mono")
        tag_color = s["faint"] if tag == "no entry" else s[color]
        svg.text(900, base, tag, 11, tag_color, family="mono")
        svg.guard(tag, 11, "mono", 130, f"{code} disposition tag")

    # ---- three-step legend -------------------------------------------------
    steps = [(64, 206, "1 · normalized equality"),
             (290, 206, "2 · containment"),
             (516, 206, "3 · edit distance ≤ 2")]
    for i, (x, w, label) in enumerate(steps):
        svg.rect(x, 376, w, 24, s["band"], 8, s["grid"], 1)
        svg.text(x + 12, 392, label, 11, s["sub"], family="mono")
        svg.guard(label, 11, "mono", w - 20, f"step {i}")
        if i < len(steps) - 1:
            arrow(svg, x + w + 6, 388, x + w + 18, 388, s["faint"], 1.2)
    note = "一、 / 1.1 / **…** stripped before comparing"
    svg.text(742, 392, note, 10.5, s["faint"], family="mono")
    svg.guard(note, 10.5, "mono", 300, "match note")

    # ---- cross-cutting rail ------------------------------------------------
    svg.text(64, 428, "CROSS-CUTTING", 11, s["accent"], family="mono",
             weight="700", spacing=1.2)
    svg.text(64, 446, "same pass, same material", 10.5, s["faint"],
             family="mono")
    svg.guard("same pass, same material", 10.5, "mono", 190, "cross label")

    x = 252
    for rid, state in FLOW_CROSS:
        state_color = s[CROSS_COLOR[state]]
        w = measure(rid, 11, "mono") * 1.06 + measure(state, 11, "mono") * 1.06 + 20
        svg.rect(x, 412, w, 22, s["card"], 11, s["grid"], 1)
        svg.text(x + 9, 427, rid, 11, s["text"], family="mono", weight="700")
        svg.text(x + w - 9, 427, state, 11, state_color, family="mono",
                 anchor="end")
        x += w + 6
    if x > 1040:
        raise SystemExit(f"FATAL: cross rail overflows to {x:.0f}px")
    legend = ("n/a not applicable · clean ran, no difference · "
              "off not configured")
    svg.text(252, 446, legend, 10.5, s["faint"], family="mono")
    svg.guard(legend, 10.5, "mono", 760, "cross legend")

    # ---- fork into the two exits ------------------------------------------
    svg.path("M550 470V486", s["faint"], 1.4)
    svg.path("M550 486H235", s["amber"], 1.6)
    svg.path("M550 486H755", s["faint"], 1.6)
    arrow(svg, 235, 486, 235, 498, s["amber"], 1.6)
    arrow(svg, 755, 486, 755, 498, s["faint"], 1.6)

    # ---- issues[] ----------------------------------------------------------
    svg.rect(40, 498, 390, 114, s["card"], 16, s["edge"], 1.2,
             ' filter="url(#soft)"')
    svg.text(56, 520, "issues[]", 13.5, s["text"], family="mono",
             weight="700")
    iw = measure("issues[]", 13.5, "mono") * 1.06
    svg.text(56 + iw + 6, 520, "2", 13.5, s["accent"], family="mono",
             weight="700")
    svg.rect(348, 508, 66, 22, s["amber_bg"], 11)
    svg.text(381, 523, "warn", 11, s["amber"], family="mono", anchor="middle")
    for i, (head, body) in enumerate(FLOW_ISSUES):
        y = 544 + i * 34
        svg.text(56, y, head, 11.5, s["amber"], family="mono")
        svg.guard(head, 11, "mono", 358, f"issue {i} head")
        svg.text(56, y + 16, body, 12.5, s["sub"])
        svg.guard(body, 12.5, "sans", 358, f"issue {i} body")

    # ---- skipped[] ---------------------------------------------------------
    svg.rect(446, 498, 614, 114, s["card"], 16, s["edge"], 1.2,
             ' filter="url(#soft)"')
    svg.text(462, 520, "skipped[]", 13.5, s["text"], family="mono",
             weight="700")
    sw_ = measure("skipped[]", 13.5, "mono") * 1.06
    svg.text(462 + sw_ + 6, 520, "8", 13.5, s["accent"], family="mono",
             weight="700")
    svg.text(1044, 523, "every entry states its reason", 10.5, s["faint"],
             family="mono", anchor="end")
    for i, line in enumerate(FLOW_SKIPPED):
        svg.text(462, 542 + i * 15.5, line, 12, s["sub"], family="mono")
        svg.guard(line, 12, "mono", 582, f"skipped {i}")

    # ---- footer ------------------------------------------------------------
    foot = ("a rule lands on exactly one side · the report lists differences, "
            "never a verdict · GB/T 29639-2020")
    svg.text(40, 638, foot, 11, s["faint"], family="mono")
    svg.guard(foot, 11, "mono", 1020, "footer")

    svg.add("</svg>")
    return "\n".join(svg.parts) + "\n"


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #


def main() -> None:
    written: list[str] = []
    for lang in ("zh", "en"):
        for skin in ("light", "dark"):
            img = hero(lang, skin)
            name = f"{NAME}-hero-{lang}-{skin}.webp"
            img.save(os.path.join(OUT, name), "WEBP", quality=92, method=6)
            written.append(name)
    for skin in ("light", "dark"):
        name = f"{NAME}-flow-v5-{skin}.svg"
        with open(os.path.join(OUT, name), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(flow_svg(skin))
        written.append(name)
    for name in written:
        size = os.path.getsize(os.path.join(OUT, name))
        print(f"wrote docs/assets/{name} ({size / 1024:.1f} kB)")


if __name__ == "__main__":
    main()
