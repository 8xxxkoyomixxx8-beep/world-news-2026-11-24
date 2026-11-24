#!/usr/bin/env python3
"""Render entry.png: a 1024x1024 editorial newspaper front page
summing up the world news of Tuesday 24 November 2026.

Uses PIL only. Layout is measured before drawing and the whole page
is scaled down in small steps until every block fits inside the
canvas with margins, so no text is clipped.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
MARGIN = 48
CONTENT_W = W - 2 * MARGIN
TOP = 30
BOTTOM_LIMIT = H - 30

PAPER = (250, 247, 238)
INK = (22, 20, 18)
MUTED = (90, 84, 76)
ACCENT = (140, 30, 24)
RULE = (22, 20, 18)

SERIF_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_ITALIC = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def font(path, size):
    return ImageFont.truetype(path, max(10, int(size)))


def wrap(draw, text, fnt, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if draw.textlength(trial, font=fnt) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def build_layout(draw, scale):
    """Return (ops, total_height). Ops are drawn top to bottom."""
    ops = []

    def add_block(text, fnt, line_h, align="left", color=INK, width=CONTENT_W, gap_after=0):
        lines = wrap(draw, text, fnt, width)
        ops.append(("text", lines, fnt, line_h, align, color, width))
        if gap_after:
            ops.append(("gap", gap_after))
        return len(lines) * line_h + gap_after

    def add_gap(h):
        ops.append(("gap", h))
        return h

    def add_rule(thickness=2, gap_after=0):
        ops.append(("rule", thickness))
        if gap_after:
            ops.append(("gap", gap_after))
        return thickness + gap_after

    total = 0
    s = scale

    # --- Masthead -------------------------------------------------
    total += add_rule(3, gap_after=int(10 * s))
    total += add_block("THE DAILY FRONT PAGE", font(SERIF_BOLD, 57 * s),
                       int(66 * s), align="center")
    total += add_block("Tuesday 24 November 2026", font(SANS_BOLD, 25 * s),
                       int(32 * s), align="center", color=ACCENT)
    total += add_gap(int(6 * s))
    total += add_rule(1, gap_after=2)
    total += add_rule(3, gap_after=int(14 * s))

    # --- Lead story -----------------------------------------------
    total += add_block("LEAD STORY", font(SANS_BOLD, 17 * s), int(22 * s),
                       color=ACCENT, gap_after=int(4 * s))
    total += add_block(
        "TANKERS HIT MINES IN HORMUZ AS IRAN REFUSES TALKS",
        font(SERIF_BOLD, 50 * s), int(58 * s), gap_after=int(8 * s))
    total += add_block(
        "Iran says oil tankers that defied its transit rules struck mines "
        "and caught fire in the Strait of Hormuz, and Tehran says it will "
        "not negotiate until its seven conditions are met.",
        font(SERIF_ITALIC, 21 * s), int(28 * s), gap_after=int(12 * s))
    total += add_rule(1, gap_after=int(12 * s))

    # --- Two column stories ---------------------------------------
    col_gap = 28
    col_w = (CONTENT_W - col_gap) // 2
    col_font_h = font(SERIF_BOLD, 28 * s)
    col_font_b = font(SANS, 18 * s)
    col_line_h = int(34 * s)
    col_body_line_h = int(24 * s)
    label_h = int(20 * s)

    left_lines = wrap(draw, "RUSSIAN STRIKE ON ZAPORIZHZHIA FLATS KILLS 2, WOUNDS 40",
                      col_font_h, col_w)
    left_body = wrap(draw, "An overnight attack on an apartment building; "
                           "four children were among the wounded.",
                     col_font_b, col_w)
    right_lines = wrap(draw, "ISRAELI STRIKE KILLS HAMAS SECURITY CHIEF IN GAZA",
                       col_font_h, col_w)
    right_body = wrap(draw, "Naeem Abu Nahel, director of Hamas' internal security "
                            "apparatus, was killed with six others, including "
                            "two police officers.",
                      col_font_b, col_w)
    left_h = label_h + 4 + len(left_lines) * col_line_h + 6 + len(left_body) * col_body_line_h
    right_h = label_h + 4 + len(right_lines) * col_line_h + 6 + len(right_body) * col_body_line_h
    col_h = max(left_h, right_h)
    ops.append(("columns", {
        "left_label": "UKRAINE", "right_label": "GAZA",
        "left_lines": left_lines, "left_body": left_body,
        "right_lines": right_lines, "right_body": right_body,
        "head_font": col_font_h, "body_font": col_font_b,
        "head_line_h": col_line_h, "body_line_h": col_body_line_h,
        "label_h": label_h, "col_w": col_w, "col_gap": col_gap,
        "height": col_h,
    }))
    total += col_h
    total += add_gap(int(12 * s))
    total += add_rule(1, gap_after=int(12 * s))

    # --- Row of smaller stories ------------------------------------
    total += add_block("MORE HEADLINES", font(SANS_BOLD, 17 * s), int(22 * s),
                       color=ACCENT, gap_after=int(6 * s))
    small_font = font(SERIF_BOLD, 22 * s)
    small_line_h = int(28 * s)
    small_stories = [
        "COP31 CLIMATE TALKS COLLAPSE WITHOUT FOSSIL-FUEL DEAL",
        "SANOFI AGREES $41BN TAKEOVER OF US DRUGMAKER INSMED",
        "14 COUNTRIES BACK ICJ ROHINGYA RULING \u2014 MALAYSIA TO RETURN 6,500 REFUGEES",
        "MEDICARE CUTS PRICES ON 13 COSTLY DRUGS BY 45%",
        "MAGNITUDE 5.6 EARTHQUAKE STRIKES NEPAL NEAR CHINA BORDER",
    ]
    for story in small_stories:
        lines = wrap(draw, story, small_font, CONTENT_W - 26)
        ops.append(("bullet", lines, small_font, small_line_h))
        total += len(lines) * small_line_h + int(5 * s)
    total += add_gap(int(8 * s))
    total += add_rule(1, gap_after=int(12 * s))

    # --- Bottom ticker ---------------------------------------------
    total += add_block("THE WIRE \u2014 LATEST", font(SANS_BOLD, 17 * s),
                       int(22 * s), color=ACCENT, gap_after=int(6 * s))
    ticker = (
        "GERMANY FIRST TO GAIN ACCESS TO UKRAINE'S DELTA BATTLEFIELD SYSTEM "
        "+++ NATO DEPLOYS AWACS TO WATCH POLAND'S EAST "
        "+++ SOUTH KOREA OFFERS $375,000 REWARDS TO CATCH AI EXAM CHEATS "
        "+++ CHINA OPENS TIANGONG STATION TO FIRST FOREIGN ASTRONAUT, "
        "PAKISTAN'S ZEESHAN ALI "
        "+++ PENNSYLVANIA MEASLES DEATHS REACH NINE, CASES HIT 1,638 "
        "+++ RAS AL KHAIMAH BUS CRASH KILLS AT LEAST 11 "
        "+++ HASINA VOWS 16 DECEMBER RETURN TO BANGLADESH DESPITE DEATH SENTENCE "
        "+++ US BLACKLISTS SINGAPORE CLOUD FIRM MEGASPEED"
    )
    ticker_font = font(SANS_BOLD, 16 * s)
    ticker_line_h = int(21 * s)
    pad = 14
    ticker_lines = wrap(draw, ticker, ticker_font, CONTENT_W - 2 * pad)
    ticker_h = len(ticker_lines) * ticker_line_h + 2 * pad
    ops.append(("ticker", ticker_lines, ticker_font, ticker_line_h, pad, ticker_h))
    total += ticker_h

    # --- Footer ------------------------------------------------------
    total += add_gap(int(10 * s))
    total += add_rule(1, gap_after=int(9 * s))
    total += add_block(
        "Front page rendered from the day's verified headlines "
        "\u00b7 Tuesday 24 November 2026",
        font(SANS, 14 * s), int(19 * s), align="center", color=MUTED)

    return ops, total


def draw_ops(img, ops):
    draw = ImageDraw.Draw(img)
    y = TOP
    for op in ops:
        kind = op[0]
        if kind == "gap":
            y += op[1]
        elif kind == "rule":
            draw.rectangle([MARGIN, y, W - MARGIN, y + op[1] - 1], fill=RULE)
            y += op[1]
        elif kind == "text":
            _, lines, fnt, line_h, align, color, width = op
            for line in lines:
                if align == "center":
                    tw = draw.textlength(line, font=fnt)
                    x = MARGIN + (CONTENT_W - tw) / 2
                else:
                    x = MARGIN
                draw.text((x, y), line, font=fnt, fill=color)
                y += line_h
        elif kind == "bullet":
            _, lines, fnt, line_h = op
            for i, line in enumerate(lines):
                if i == 0:
                    draw.text((MARGIN, y), "\u25aa", font=fnt, fill=ACCENT)
                draw.text((MARGIN + 26, y), line, font=fnt, fill=INK)
                y += line_h
            y += 5
        elif kind == "columns":
            d = op[1]
            x_left = MARGIN
            x_right = MARGIN + d["col_w"] + d["col_gap"]
            label_font = font(SANS_BOLD, 15)
            for x, label, head_lines, body_lines in (
                (x_left, d["left_label"], d["left_lines"], d["left_body"]),
                (x_right, d["right_label"], d["right_lines"], d["right_body"]),
            ):
                cy = y
                draw.text((x, cy), label, font=label_font, fill=ACCENT)
                cy += d["label_h"] + 4
                for line in head_lines:
                    draw.text((x, cy), line, font=d["head_font"], fill=INK)
                    cy += d["head_line_h"]
                cy += 6
                for line in body_lines:
                    draw.text((x, cy), line, font=d["body_font"], fill=MUTED)
                    cy += d["body_line_h"]
            mid_x = MARGIN + d["col_w"] + d["col_gap"] // 2
            draw.line([mid_x, y, mid_x, y + d["height"]], fill=MUTED, width=1)
            y += d["height"]
        elif kind == "ticker":
            _, lines, fnt, line_h, pad, height = op
            draw.rectangle([MARGIN, y, W - MARGIN, y + height - 1],
                           outline=INK, width=2)
            ty = y + pad
            for line in lines:
                draw.text((MARGIN + pad, ty), line, font=fnt, fill=INK)
                ty += line_h
            y += height
    return y


def main():
    img = Image.new("RGB", (W, H), PAPER)
    probe = ImageDraw.Draw(img)

    scale = 1.0
    while scale > 0.5:
        ops, total = build_layout(probe, scale)
        if TOP + total <= BOTTOM_LIMIT:
            break
        scale -= 0.02
    else:
        raise SystemExit("layout does not fit even at minimum scale")

    end_y = draw_ops(img, ops)
    if end_y > BOTTOM_LIMIT:
        raise SystemExit(f"layout overflow: ends at y={end_y}, limit {BOTTOM_LIMIT}")

    out = Path(__file__).resolve().parent / "entry.png"
    img.save(out, format="PNG", optimize=True)
    print(f"wrote {out} at scale {scale:.2f}, content ends at y={end_y}")


if __name__ == "__main__":
    main()
