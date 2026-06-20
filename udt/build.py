#!/usr/bin/env python3
"""Build slides.html from slides.md — slides.md is the source of truth.

Run:  source .venv/bin/activate && python3 build.py

Markdown dialect (plain Markdown + a few lightweight conventions):

  # Deck Title — subtitle        the deck H1 (text after " — " is the gold span)
  *description*                   optional, ignored in the header

  ---                             thematic breaks separate slides (cosmetic)

  ## Slide N: Title               a slide. N drives the "n / N" counter and,
                                  for images, the screenshot file.
  ## Slide N: Title {.section}    slide type — {.title} {.section} {.closing};
                                  default (no class) is a content slide.

  **Subtitle**                    a standalone bold line in a {.title} slide
  ::: meta                        a fenced block of meta lines (one per line),
  line 1                          used on the title / closing slides
  :::

  ```yaml {hl=8}                  fenced code. lang from the info string;
  ...                             highlight lines via {hl=8} / {hl=8,9} / {hl=8-10}
  ```
  *caption*                       an italic line right after a fence/image = caption

  > text                          a note (callout). First-line [!WARN] -> warn
  > [!WARN] **Title:** text       variant; leading **Title:** sets the note title.

  ![alt](images/slide-10.png)     a screenshot (slide number read from the path)
  [![alt](images/slide-10.png)](url)   linked screenshot (opens url in a new tab)
  *caption*

  - bullet                        a list that is a slide's only content becomes
    - nested                      the slide body (supports nesting); a list that
                                  sits alongside other blocks becomes a doc list.
  1. step                         ordered lists work the same way.

  plain paragraph                 prose.

Inline `code`, **bold** and *italic* are converted to <code>/<strong>/<em>
in notes, prose, lists and bullets.
"""
import html
import re

# ---------------------------------------------------------------- inline md
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    # single-asterisk italics — runs after bold (no ** left) and is fenced to
    # one text run: content may not contain *, < or > (so it can't span tags
    # or pair with a stray * inside inline code), and can't open on a space.
    t = re.sub(r"\*(?!\s)([^*<>]+?)\*", r"<em>\1</em>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t

def parse_hl(attr):
    """'8' / '8,9,10' / '8-10' -> set of ints."""
    out = set()
    for part in attr.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return out

# ---------------------------------------------------------------- md parser
HEAD_RE = re.compile(r"^## Slide (\d+):\s*(.*?)\s*(?:\{\.(\w+)\})?\s*$")
FENCE_RE = re.compile(r"^```(\S+)?\s*(?:\{([^}]*)\})?\s*$")
IMG_RE = re.compile(r"^!\[[^\]]*\]\((.+?)\)\s*$")
LINKED_IMG_RE = re.compile(r"^\[!\[[^\]]*\]\((.+?)\)\]\((.+?)\)\s*$")  # [![alt](img)](url)
ITALIC_RE = re.compile(r"^\*(.+)\*\s*$")
OL_RE = re.compile(r"^(\s*)\d+\.\s+(.*)$")
UL_RE = re.compile(r"^(\s*)-\s+(.*)$")

def is_caption(line):
    m = ITALIC_RE.match(line)
    return m.group(1) if (m and not line.strip().startswith("**")) else None

def parse_slide(num, title, stype, lines):
    s = {"n": num, "type": stype or "content", "title": title}
    blocks = []
    meta = []
    i, N = 0, len(lines)

    def lookahead_caption(j):
        while j < N and lines[j].strip() == "":
            j += 1
        if j < N:
            cap = is_caption(lines[j])
            if cap is not None:
                return cap, j + 1
        return None, j

    while i < N:
        line = lines[i]
        stripped = line.strip()
        if stripped == "":
            i += 1
            continue

        # meta fence
        if stripped == "::: meta":
            i += 1
            while i < N and lines[i].strip() != ":::":
                if lines[i].strip():
                    meta.append(lines[i].strip())
                i += 1
            i += 1
            continue

        # code fence
        m = FENCE_RE.match(line)
        if m:
            lang = m.group(1) or "text"
            hl = set()
            if m.group(2) and "hl=" in m.group(2):
                hl = parse_hl(m.group(2).split("hl=", 1)[1])
            i += 1
            buf = []
            while i < N and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # closing fence
            cap, i = lookahead_caption(i)
            blocks.append({"kind": "code", "lang": lang, "src": "\n".join(buf),
                           "caption": cap, "hl": hl})
            continue

        # image (optionally wrapped in a link: [![alt](img)](url))
        m = LINKED_IMG_RE.match(line) or IMG_RE.match(line)
        if m:
            href = m.group(2) if m.re is LINKED_IMG_RE else None
            n = int(re.search(r"slide-(\d+)", m.group(1)).group(1))
            i += 1
            cap, i = lookahead_caption(i)
            blocks.append({"kind": "image", "n": n, "caption": cap, "href": href})
            continue

        # note (blockquote)
        if stripped.startswith(">"):
            buf = []
            while i < N and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            text = " ".join(x.strip() for x in buf).strip()
            variant = "info"
            mvar = re.match(r"^\[!(\w+)\]\s*(.*)$", text)
            if mvar:
                variant = "warn" if mvar.group(1).upper().startswith("WARN") else "info"
                text = mvar.group(2)
            ntitle = None
            mt = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", text)
            if mt:
                ntitle, text = mt.group(1), mt.group(2)
            blocks.append({"kind": "note", "text": inline(text),
                           "title": ntitle, "variant": variant})
            continue

        # list (ordered or unordered)
        if OL_RE.match(line) or UL_RE.match(line):
            ordered = bool(OL_RE.match(line))
            items = []
            while i < N:
                mo, mu = OL_RE.match(lines[i]), UL_RE.match(lines[i])
                if not (mo or mu):
                    if lines[i].strip() == "":
                        break
                    break
                indent, txt = (mo or mu).group(1), (mo or mu).group(2)
                lvl = len(indent) // 2
                items.append((lvl, txt))
                i += 1
            blocks.append({"kind": "list", "ordered": ordered, "items": items})
            continue

        # standalone bold line in a title slide -> subtitle
        mb = re.match(r"^\*\*(.+?)\*\*\s*$", stripped)
        if mb and s["type"] in ("title", "closing"):
            s["subtitle"] = mb.group(1)
            i += 1
            continue

        # otherwise: a prose paragraph (collect until blank)
        buf = [stripped]
        i += 1
        while i < N and lines[i].strip() and not lines[i].startswith(("```", ">", "!", "    ")) \
                and not OL_RE.match(lines[i]) and not UL_RE.match(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        blocks.append({"kind": "prose", "text": inline(" ".join(buf))})

    # a lone list with no other blocks becomes the slide body (bullets)
    non_list = [b for b in blocks if b["kind"] != "list"]
    lists = [b for b in blocks if b["kind"] == "list"]
    if len(lists) == 1 and not non_list:
        s["bullets"] = lists[0]["items"]
    else:
        # convert list blocks to doc lists, keeping order
        conv = []
        for b in blocks:
            if b["kind"] == "list":
                conv.append({"kind": "olist" if b["ordered"] else "ulist",
                             "items": [inline(t) for _, t in b["items"]]})
            else:
                conv.append(b)
        blocks = conv
        s["blocks"] = blocks
    if "bullets" not in s:
        s["blocks"] = [b for b in (s.get("blocks") or blocks) if b["kind"] != "list"]
    if meta:
        s["meta"] = meta
    return s

def parse_md(text):
    lines = text.split("\n")
    # preamble: deck H1
    deck_title = "Slides"
    for ln in lines:
        if ln.startswith("# "):
            deck_title = ln[2:].strip()
            break
    # split into slides on "## Slide" headings
    slides = []
    i, N = 0, len(lines)
    while i < N:
        m = HEAD_RE.match(lines[i])
        if not m:
            i += 1
            continue
        num, title, stype = int(m.group(1)), m.group(2), m.group(3)
        j = i + 1
        body = []
        while j < N and not HEAD_RE.match(lines[j]):
            if lines[j].strip() == "---":
                j += 1
                continue
            body.append(lines[j])
            j += 1
        slides.append(parse_slide(num, title, stype, body))
        i = j
    return deck_title, slides

# ---------------------------------------------------------------- renderers
def esc(t):
    return html.escape(t)

def img_path(n):
    return f"images/slide-{n:02d}.png"

def render_bullets(bullets):
    out = []
    cur = -1
    for lvl, txt in bullets:
        if lvl > cur:
            for _ in range(lvl - cur):
                out.append("<ul>")
            out.append("<li>" + inline(txt))
            cur = lvl
        elif lvl == cur:
            out.append("</li><li>" + inline(txt))
        else:
            out.append("</li>")
            for _ in range(cur - lvl):
                out.append("</ul></li>")
            out.append("<li>" + inline(txt))
            cur = lvl
    out.append("</li>")
    for _ in range(cur):
        out.append("</ul></li>")
    out.append("</ul>")
    return "".join(out)

def render_code(block):
    lines = block["src"].split("\n")
    rows = []
    for i, ln in enumerate(lines, 1):
        cls = "line hl" if i in block["hl"] else "line"
        rows.append(f'<span class="{cls}"><span class="ln">{i}</span>'
                    f'<span class="lc">{esc(ln) or "&nbsp;"}</span></span>')
    cap = f'<figcaption>{esc(block["caption"])}</figcaption>' if block.get("caption") else ""
    return (f'<figure class="code"><pre class="language-{block["lang"]}"><code>'
            + "".join(rows) + f'</code></pre>{cap}</figure>')

def render_block(b):
    k = b["kind"]
    if k == "code":
        return render_code(b)
    if k == "note":
        title = f'<span class="note__title">{esc(b["title"])}</span>' if b.get("title") else ""
        return f'<aside class="note note--{b.get("variant","info")}">{title}<span>{b["text"]}</span></aside>'
    if k == "image":
        cap = f'<figcaption>{esc(b["caption"])}</figcaption>' if b.get("caption") else ""
        img = (f'<img src="{img_path(b["n"])}" '
               f'alt="Slide {b["n"]} screenshot" loading="lazy">')
        if b.get("href"):
            img = (f'<a href="{esc(b["href"])}" target="_blank" rel="noopener" '
                   f'title="Open {esc(b["href"])}">{img}</a>')
        return f'<figure class="shot">{img}{cap}</figure>'
    if k == "prose":
        return f'<p class="prose">{b["text"]}</p>'
    if k == "olist":
        return "<ol class=\"doc\">" + "".join(f"<li>{it}</li>" for it in b["items"]) + "</ol>"
    if k == "ulist":
        return "<ul class=\"doc\">" + "".join(f"<li>{it}</li>" for it in b["items"]) + "</ul>"
    return ""

# ---------------------------------------------------------------- html
def build_html(deck_title, slides):
    N = max(s["n"] for s in slides)
    if " — " in deck_title:
        a, b = deck_title.split(" — ", 1)
        h1 = f"{esc(a)} <span>— {esc(b)}</span>"
    else:
        h1 = esc(deck_title)
    byline = ""
    for s in slides:
        if s["n"] == 1 and s.get("meta"):
            byline = " · ".join(esc(m) for m in s["meta"])
            break

    parts = []
    for s in slides:
        n = s["n"]
        parts.append(f'  <section class="slide slide--{s["type"]}" id="slide-{n}" aria-label="Slide {n}">')
        parts.append(f'    <span class="slide__num">{n} / {N}</span>')
        if s.get("title"):
            parts.append(f'    <h2 class="slide__title">{esc(s["title"])}</h2>')
        if s.get("subtitle"):
            parts.append(f'    <p class="slide__subtitle">{esc(s["subtitle"])}</p>')
        if s.get("bullets"):
            parts.append('    <div class="slide__body">' + render_bullets(s["bullets"]) + '</div>')
        if s.get("blocks"):
            parts.append('    <div class="slide__blocks">')
            for b in s["blocks"]:
                parts.append("      " + render_block(b))
            parts.append('    </div>')
        if s.get("meta"):
            parts.append('    <div class="slide__meta">' +
                         "".join(f"<p>{esc(m)}</p>" for m in s["meta"]) + '</div>')
        parts.append('  </section>')
    body = "\n".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>User-Defined Tools — From LLM Code to Validated Workflows</title>
<link rel="stylesheet" href="slides.css">
</head>
<body>
<div class="toolbar">
  <button id="presentBtn" title="Present — press f">&#9974; Present</button>
</div>
<header class="deck-header">
  <h1>{h1}</h1>
  <p>{byline}</p>
  <p class="hint">Press <kbd>f</kbd> for fullscreen · <kbd>←</kbd> <kbd>→</kbd> to navigate · type a <kbd>number</kbd> to jump</p>
</header>
<main class="deck">
{body}
</main>
<script>
(function () {{
  const slides = Array.from(document.querySelectorAll('.slide'));
  const body = document.body;
  const isPresent = () => body.classList.contains('present');
  function nearest() {{
    let best = 0, bd = Infinity;
    slides.forEach((s, idx) => {{
      const d = Math.abs(s.getBoundingClientRect().top);
      if (d < bd) {{ bd = d; best = idx; }}
    }});
    return best;
  }}
  function go(n) {{
    const i = Math.max(0, Math.min(slides.length - 1, n));
    slides[i].scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }}
  function restore(i) {{
    // after the layout reflows out of present mode, bring the slide we were
    // on back into view (instant, no animation)
    requestAnimationFrame(() =>
      slides[i].scrollIntoView({{ block: 'center' }}));
  }}
  function fitSlide(s) {{
    // shrink a slide's content (via --fit) just enough that it stops
    // overflowing — so tall code/bullets fit without scrolling. The content
    // scrolls inside .slide__blocks (max-height:100%), so check that box too.
    const box = s.querySelector('.slide__blocks') || s.querySelector('.slide__body');
    const overflows = () =>
      s.scrollHeight > s.clientHeight + 1 ||
      (box && box.scrollHeight > box.clientHeight + 1);
    s.style.setProperty('--fit', '1');
    let fit = 1, guard = 0;
    while (overflows() && fit > 0.5 && guard++ < 24) {{
      fit -= 0.05;
      s.style.setProperty('--fit', fit.toFixed(2));
    }}
  }}
  function fitAll() {{ if (isPresent()) slides.forEach(fitSlide); }}
  function unfit() {{ slides.forEach((s) => s.style.removeProperty('--fit')); }}
  let presentTarget = 0;
  function present(on) {{
    if (on) {{
      presentTarget = nearest();   // slide visible now, captured before the reflow
      body.classList.add('present');
      const el = document.documentElement;
      if (el.requestFullscreen) el.requestFullscreen().catch(() => {{}});
      requestAnimationFrame(() => {{ fitAll(); go(presentTarget); }});
    }} else {{
      const i = nearest();
      body.classList.remove('present');
      unfit();
      if (document.fullscreenElement) document.exitFullscreen();
      restore(i);
    }}
  }}
  document.getElementById('presentBtn')
    .addEventListener('click', () => present(!isPresent()));
  document.addEventListener('fullscreenchange', () => {{
    if (document.fullscreenElement && isPresent()) {{
      // fullscreen just engaged — re-anchor to the intended slide after the
      // viewport resize (and re-fit for the new size)
      requestAnimationFrame(() => {{ fitAll(); go(presentTarget); }});
    }} else if (!document.fullscreenElement && isPresent()) {{
      // Esc / OS-level fullscreen exit; keep our current slide
      const i = nearest();
      body.classList.remove('present');
      unfit();
      restore(i);
    }}
  }});
  let fitTimer;
  window.addEventListener('resize', () => {{
    clearTimeout(fitTimer);
    fitTimer = setTimeout(fitAll, 150);
  }});
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitAll);

  // type a number (multi-digit) then Enter — or just pause — to jump to a slide
  let gotoBuf = '', gotoTimer;
  const gotoHint = document.createElement('div');
  gotoHint.className = 'goto-hint';
  gotoHint.setAttribute('aria-hidden', 'true');
  document.body.appendChild(gotoHint);
  function gotoCommit() {{
    clearTimeout(gotoTimer);
    if (gotoBuf) {{ const n = parseInt(gotoBuf, 10); if (!isNaN(n)) go(n - 1); }}
    gotoBuf = '';
    gotoHint.classList.remove('show');
  }}
  function gotoCancel() {{
    clearTimeout(gotoTimer);
    gotoBuf = '';
    gotoHint.classList.remove('show');
  }}
  function gotoDigit(d) {{
    gotoBuf += d;
    gotoHint.textContent = '→ ' + gotoBuf + ' / ' + slides.length;
    gotoHint.classList.add('show');
    clearTimeout(gotoTimer);
    gotoTimer = setTimeout(gotoCommit, 900);
  }}

  document.addEventListener('keydown', (e) => {{
    if (e.key >= '0' && e.key <= '9') {{ e.preventDefault(); gotoDigit(e.key); }}
    else if (e.key === 'Enter') {{ e.preventDefault(); gotoCommit(); }}
    else if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(e.key)) {{ e.preventDefault(); gotoCancel(); go(nearest() + 1); }}
    else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) {{ e.preventDefault(); gotoCancel(); go(nearest() - 1); }}
    else if (e.key === 'f' || e.key === 'F') {{ gotoCancel(); present(!isPresent()); }}
    else if (e.key === 'Home') {{ e.preventDefault(); gotoCancel(); go(0); }}
    else if (e.key === 'End') {{ e.preventDefault(); gotoCancel(); go(slides.length - 1); }}
    else if (e.key === 'Escape') {{ gotoCancel(); }}
  }});
}})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    text = open("slides.md").read()
    deck_title, slides = parse_md(text)
    open("slides.html", "w").write(build_html(deck_title, slides))
    print(f"wrote slides.html from slides.md ({len(slides)} slides)")
