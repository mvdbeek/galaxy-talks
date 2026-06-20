#!/usr/bin/env python3
"""Emit a root index.html linking to every slide deck in this repo.

A "deck" is any immediate sub-folder containing a slides.html (e.g. udt/).
Title and byline are read straight from each deck's built slides.html, so
adding a new deck is just: drop a folder with its slides.html, re-run this.

    python3 build_index.py
"""
import html
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))


def find_decks():
    decks = []
    for name in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, name)
        page = os.path.join(d, "slides.html")
        if os.path.isdir(d) and not name.startswith(".") and os.path.isfile(page):
            decks.append((name, page))
    return decks


def deck_meta(page):
    src = open(page, encoding="utf-8").read()
    m = re.search(r"<h1>(.*?)</h1>", src, re.S)
    title = m.group(1).strip() if m else "Slides"
    # byline = first <p> in the deck header (skip the .hint paragraph)
    hdr = re.search(r'<header class="deck-header">(.*?)</header>', src, re.S)
    byline = ""
    if hdr:
        for p in re.findall(r"<p[^>]*>(.*?)</p>", hdr.group(1), re.S):
            if "hint" not in p and p.strip():
                byline = p.strip()
                break
    return title, byline


def build_index(decks):
    cards = []
    for name, page in decks:
        title, byline = deck_meta(page)
        cards.append(
            f'  <a class="card" href="{html.escape(name)}/slides.html">\n'
            f'    <h2>{title}</h2>\n'
            f'    <p class="byline">{byline}</p>\n'
            f'    <span class="open">Open deck &rarr;</span>\n'
            f'  </a>'
        )
    cards_html = "\n".join(cards) or '  <p class="empty">No decks yet.</p>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Slide decks</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&display=swap');
:root {{
  --galaxy-primary:#25537b; --galaxy-dark:#2c3143; --gold:#e8c547;
  --font-sans:'Atkinson Hyperlegible',ui-sans-serif,system-ui,-apple-system,sans-serif;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; min-height:100vh; font-family:var(--font-sans); color:#f8f9fa;
  background:
    linear-gradient(to right, rgba(255,255,255,.03) 1px, transparent 1px) 0 0 / 24px 24px,
    linear-gradient(to bottom, rgba(255,255,255,.03) 1px, transparent 1px) 0 0 / 24px 24px,
    radial-gradient(1100px 560px at 15% -10%, #34507a 0%, transparent 60%),
    var(--galaxy-dark);
}}
.wrap {{ max-width:880px; margin:0 auto; padding:4rem 1.25rem 5rem; }}
header h1 {{ font-size:clamp(2rem,5vw,3.2rem); margin:0 0 .4rem; letter-spacing:-.01em; }}
header p {{ color:#aeb6c2; margin:0 0 2.5rem; }}
.cards {{ display:flex; flex-direction:column; gap:1.1rem; }}
.card {{
  display:block; text-decoration:none; color:inherit;
  background:#ffffff; color:#2c3143; border-radius:14px;
  padding:1.6rem 1.8rem; border:1px solid #e1e4e8;
  box-shadow:0 20px 50px -22px rgba(0,0,0,.55);
  transition:transform .12s, box-shadow .12s;
}}
.card:hover {{ transform:translateY(-2px); box-shadow:0 26px 60px -22px rgba(0,0,0,.6); }}
.card h2 {{ margin:0 0 .35rem; color:var(--galaxy-primary); font-size:clamp(1.3rem,2.6vw,1.9rem); }}
.card h2 span {{ color:#b89a1f; font-weight:400; }}
.card .byline {{ margin:0 0 .9rem; color:#58585a; font-size:.95rem; }}
.card .open {{ color:var(--galaxy-primary); font-weight:700; }}
.empty {{ color:#aeb6c2; }}
:focus-visible {{ outline:2px solid var(--gold); outline-offset:3px; border-radius:4px; }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Slide decks</h1>
  <p>Galaxy talks &amp; presentations</p>
</header>
<main class="cards">
{cards_html}
</main>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    decks = find_decks()
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(build_index(decks))
    print(f"wrote index.html ({len(decks)} deck{'s' if len(decks) != 1 else ''}: "
          f"{', '.join(n for n, _ in decks) or 'none'})")
