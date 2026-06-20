#!/usr/bin/env python3
"""Generate slides.md and slides.html from transcribed slide content.

Run:  source .venv/bin/activate && python3 generate.py
Edit the SLIDES list below to change content, then re-run.
"""
import html

# ---- helpers to build block dicts ----
def code(lang, src, caption=None, highlight=None):
    return {"kind": "code", "lang": lang, "src": src.strip("\n"),
            "caption": caption, "hl": set(highlight or [])}
def note(text, title=None, variant="info"):
    return {"kind": "note", "text": text, "title": title, "variant": variant}
def image(n, caption=None):
    return {"kind": "image", "n": n, "caption": caption}

N = 23  # total slides

SLIDES = [
 {"n":1,"type":"title","title":"Galaxy Tools 2.0","subtitle":"Bring your own!",
  "meta":["Marius van den Beek","PSU / SCI-SCALE","marius@galaxyproject.org"]},

 {"n":2,"type":"content","title":"Why can’t users install tools?",
  "bullets":[(0,"We don’t want to limit what you can do!"),
             (1,"I need “xyz” and it’s not on the server I use, help please?"),
             (0,"You can already run code with RStudio and Jupyter*"),
             (0,"We can isolate storage and compute")]},

 {"n":3,"type":"section","title":"Why can’t users install tools?"},

 {"n":4,"type":"content","title":"Templating with Cheetah","blocks":[
   code("xml", """
<tool id="cat" version="0.1">
    <description>tail-to-head</description>
    <requirements>
        <requirement type="container">busybox</requirement>
    </requirements>
    <command><![CDATA[
cat
#for dataset in datasets:
    '$dataset'
#end for
> '$output1'
    ]]></command>
    <inputs>
        <input name="datasets" format="data" type="data" multiple="true"/>
    </inputs>
    <outputs>
        <output name="output1" format_source="datasets" />
    </outputs>
</tool>
""", caption="Classic Galaxy tool — Cheetah loop over inputs", highlight=[8,9,10]),
 ]},

 {"n":5,"type":"content","title":"Templating with Cheetah 🎃","blocks":[
   note("Cheetah templates are evaluated as <strong>arbitrary Python</strong> while the job command is built — so a tool author can read the database, touch the filesystem, do anything. That’s exactly why users can’t be allowed to install tools.",
        title="The catch", variant="warn"),
   code("xml", """
<command><![CDATA[
    #from pathlib import Path
    #user_id = $__app__.model.session().query($__app__.model.User.id).one()
    #open(f"{Path.home()}/a_file", "w").write("Hello!")
]]></command>
""", caption="Nothing stops a template from running this", highlight=[2,3,4]),
 ]},

 {"n":6,"type":"content","title":"How do we manage 1000s of tools?","blocks":[
   image(6, "galaxyproject/tools-iuc — 337 open / 5,450 closed pull requests. Every tool is hand-curated and reviewed."),
 ]},

 {"n":7,"type":"section","title":"There has to be a better way!"},

 {"n":8,"type":"content","title":"Javascript expressions & JSON inputs","blocks":[
   code("yaml", """
class: GalaxyUserTool
id: cat_user_defined
version: "0.1"
name: Concatenate Files
description: tail-to-head
container: busybox
shell_command: |
  cat $(inputs.datasets.map((input) => input.path).join(' ')) > output.txt
inputs:
  - name: datasets
    multiple: true
    type: data
outputs:
  - name: output1
    type: data
    format_source: datasets
    from_work_dir: output.txt
""", caption="A user-defined tool — values come from a sandboxed JS expression", highlight=[8]),
 ]},

 {"n":9,"type":"content","title":"Javascript expressions & JSON inputs","blocks":[
   code("yaml", """
class: GalaxyUserTool
id: cat_user_defined
version: "0.1"
name: Concatenate Files
description: tail-to-head
container: busybox
shell_command: |
  cat $(inputs.datasets.map((input) => input.path).join(' ')) > output.txt
inputs:
  - name: datasets
    multiple: true
    type: data
outputs:
  - name: output1
    type: data
    format_source: datasets
    from_work_dir: output.txt
""", caption="Tool definition"),
   code("javascript", """
var inputs = {
    "datasets": [
        {
            "class": "File",
            "location": "step_input://1",
            "format": "csv",
            "path": "/Users/mvandenb/src/galaxy/databa…",
            "basename": "markers.csv",
            "nameroot": "markers",
            "nameext": ".csv"
        }
    ],
    "chromInfo": "/tmp/shared/ucsc/chrom/?.len",
    "dbkey": "?",
    "__input_ext": "input"
};
""", caption="The inputs object the expression evaluates against (path truncated)"),
 ]},

 {"n":10,"type":"content","title":"Javascript expressions & JSON inputs","blocks":[
   code("yaml", """
class: GalaxyUserTool
id: cat_user_defined
version: "0.1"
name: Concatenate Files
description: tail-to-head
container: busybox
shell_command: |
  cat $(inputs.datasets.map((input) => input.path).join(' ')) > output.txt
inputs:
  - name: datasets
    multiple: true
    type: data
outputs:
  - name: output1
    type: data
    format_source: datasets
    from_work_dir: output.txt
""", caption="Tool Editor"),
   note("In the editor, Monaco knows the inferred type of <code>input</code> inside the expression and offers autocomplete:", title="Autocomplete"),
   code("typescript", """
(parameter) input: {
    readonly class: "File";
    readonly basename: string;
    readonly location: string;
    readonly path: string;
    readonly listing: readonly string[] | null;
    readonly nameroot: string | null;
    readonly nameext: string | null;
    readonly checksum: string | null;
    readonly size: number;
}
"""),
   image(10, "The live Tool Editor showing the autocomplete popup"),
 ]},

 {"n":11,"type":"content","title":"Javascript expressions & JSON inputs","blocks":[
   note("Same view as the previous slide (presenter build step)."),
   image(11, "Tool Editor with type-aware autocomplete"),
 ]},

 {"n":12,"type":"content","title":"Monaco + YAML schemas","blocks":[
   note("Hovering a property in the YAML surfaces documentation pulled from the schema:", title="Hover docs"),
   code("text", """
(property) path: string
Path
@description — The absolute path to the file on disk.
"""),
   image(12, "Monaco hover tooltip driven by the YAML schema"),
 ]},

 {"n":13,"type":"content","title":"Monaco + Typescript interfaces","blocks":[
   note("Typos in the expression are caught as real TypeScript errors, with suggestions:", title="Type checking", variant="warn"),
   code("text", """
Property 'datsets' does not exist on type '{ readonly datasets: readonly
{ readonly class: "File"; readonly basename: string; readonly location:
string; readonly path: string; readonly listing: readonly string[] |
null; readonly nameroot: string | null; readonly nameext: string | null;
readonly checksum: string | null; readonly size: number; }[]; }'.
Did you mean 'datasets'?
"""),
   image(13, "TypeScript error shown inline in the Tool Editor"),
 ]},

 {"n":14,"type":"content","title":"Behind the scenes",
  "bullets":[(0,"Tool parameters are modeled as Pydantic models"),
             (1,"As a general schema that describes “A Galaxy Tool”"),
             (1,"As a specialized schema for “This Galaxy Tool’s Potential Input Object”"),
             (0,"Pydantic models are transformed to JSON schema"),
             (0,"JSON schema is transformed to a TypeScript interface for runtime inputs"),
             (0,"Monaco Editor renders the tool source"),
             (1,"Knows what to do with the YAML schema for the tool"),
             (1,"Understands the TypeScript interface and compares it to the code in JavaScript fragments")]},

 {"n":15,"type":"section","title":"Behind the scenes"},

 {"n":16,"type":"content","title":"Generated JSON schema — inputs","blocks":[
   code("json", """
"inputs": {
    "additionalProperties": false,
    "properties": {
        "datasets": {
            "items": {
                "$ref": "#/components/schemas/DataInternalJson"
            },
            "title": "Datasets",
            "type": "array"
        }
    },
    "required": [
        "datasets"
    ],
""", caption="Top-level inputs schema (excerpt)"),
 ]},

 {"n":17,"type":"content","title":"Generated JSON schema — inputs","blocks":[
   note("Same schema as the previous slide (presenter build step)."),
   code("json", """
"inputs": {
    "additionalProperties": false,
    "properties": {
        "datasets": {
            "items": {
                "$ref": "#/components/schemas/DataInternalJson"
            },
            "title": "Datasets",
            "type": "array"
        }
    },
    "required": [
        "datasets"
    ],
""", caption="Top-level inputs schema (excerpt)"),
 ]},

 {"n":18,"type":"content","title":"Generated JSON schema — DataInternalJson","blocks":[
   code("json", """
"DataInternalJson": {
    "additionalProperties": false,
    "properties": {
        "class": {
            "const": "File",
            "title": "Class",
            "type": "string"
        },
        "basename": {
            "description": "The base name of the file, that is, the nam…",
            "title": "Basename",
            "type": "string"
        },
        "location": {
            "title": "Location",
            "type": "string"
        },
        "path": {
            "description": "The absolute path to the file on disk.",
            "title": "Path",
            "type": "string"
        },
    }
}
""", caption="The File schema referenced by inputs (excerpt; some descriptions truncated)"),
 ]},

 {"n":19,"type":"content","title":"Enabling User-Defined Tools","blocks":[
   note("To enable this feature:", title=None),
   {"kind":"olist","items":[
     "Set <code>enable_beta_tool_formats: true</code> in your Galaxy configuration.",
     "Create a role of type <code>Custom Tool Execution</code> in the admin user interface.",
     "Assign users or groups to this role.",
   ]},
 ]},

 {"n":20,"type":"content","title":"Sharing User-Defined Tools","blocks":[
   {"kind":"prose","text":"User-defined tools are private to their creators. However, if a tool is embedded in a workflow, any user who imports that workflow will automatically have the tool created in their account."},
   {"kind":"prose","text":"These tools can also be exported to disk and loaded like regular tools, enabling instance-wide availability if needed."},
 ]},

 {"n":21,"type":"content","title":"Sharing User-Defined Tools","blocks":[
   note("Same content as the previous slide (presenter build step)."),
   {"kind":"prose","text":"User-defined tools are private to their creators. However, if a tool is embedded in a workflow, any user who imports that workflow will automatically have the tool created in their account."},
   {"kind":"prose","text":"These tools can also be exported to disk and loaded like regular tools, enabling instance-wide availability if needed."},
 ]},

 {"n":22,"type":"content","title":"Limitations","blocks":[
   {"kind":"prose","text":"The user-defined tool language is still evolving, and additional safety audits are ongoing."},
   {"kind":"prose","text":"Current limitations include:"},
   {"kind":"ulist","items":[
     "<code>configfiles</code> are not supported",
     "Access to reference data is not supported",
     "Access to metadata and metadata files (such as BAM indexes) is not supported",
     "Access to the <code>extra_files</code> directory is not supported",
   ]},
 ]},

 {"n":23,"type":"closing","title":"Coming to a server near you soon!",
  "meta":["With gratitude 💜"],
  "blocks":[
   code("yaml", """
class: GalaxyUserTool
id: thank-you
version: "1.0"
name: Thank You!
description: Bring your own gratitude
container: busybox
shell_command: |
  echo "Thank you John Chilton, Dannon Baker, Michael Crusoe,
  Anton Nekrutenko, and the audience at GCC!" > thanks.txt
outputs:
  - name: output1
    type: data
    from_work_dir: thanks.txt
""", caption="One last user-defined tool"),
 ]},
]

# ----------------------------------------------------------------------
def esc(t):
    return html.escape(t)

def img_path(n):
    return f"images/slide-{n:02d}.png"

# ---------- nested bullets (level,text) -> HTML ----------
def render_bullets(bullets):
    out = []
    depth = 0
    for lvl, txt in bullets:
        while depth < lvl + 1:
            out.append("<ul><li>" if depth == lvl else "<ul><li>")
            depth += 1
            if depth == lvl + 1:
                out.append(esc(txt))
                break
        else:
            pass
    # simpler explicit algorithm:
    out = []
    cur = -1
    for lvl, txt in bullets:
        if lvl > cur:
            for _ in range(lvl - cur):
                out.append("<ul>")
            out.append("<li>" + esc(txt))
            cur = lvl
        elif lvl == cur:
            out.append("</li><li>" + esc(txt))
        else:
            out.append("</li>")
            for _ in range(cur - lvl):
                out.append("</ul></li>")
            out.append("<li>" + esc(txt))
            cur = lvl
    out.append("</li>")
    for _ in range(cur):
        out.append("</ul></li>")
    out.append("</ul>")
    return "".join(out)

# ---------- code -> line-numbered, line-highlightable HTML ----------
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
        return (f'<figure class="shot"><img src="{img_path(b["n"])}" '
                f'alt="Slide {b["n"]} screenshot" loading="lazy">{cap}</figure>')
    if k == "prose":
        return f'<p class="prose">{b["text"]}</p>'
    if k == "olist":
        return "<ol class=\"doc\">" + "".join(f"<li>{it}</li>" for it in b["items"]) + "</ol>"
    if k == "ulist":
        return "<ul class=\"doc\">" + "".join(f"<li>{it}</li>" for it in b["items"]) + "</ul>"
    return ""

# ---------- HTML ----------
def build_html():
    parts = []
    for s in SLIDES:
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
<title>Galaxy Tools 2.0 — Bring your own!</title>
<link rel="stylesheet" href="slides.css">
</head>
<body>
<div class="toolbar">
  <button id="presentBtn" title="Present — press f">&#9974; Present</button>
</div>
<header class="deck-header">
  <h1>Galaxy Tools 2.0 <span>— Bring your own!</span></h1>
  <p>Marius van den Beek · PSU / SCI-SCALE · marius@galaxyproject.org</p>
  <p class="hint">Press <kbd>f</kbd> for fullscreen · <kbd>←</kbd> <kbd>→</kbd> to navigate</p>
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
  function present(on) {{
    if (on) {{
      body.classList.add('present');
      const el = document.documentElement;
      if (el.requestFullscreen) el.requestFullscreen().catch(() => {{}});
      requestAnimationFrame(() => go(nearest()));
    }} else {{
      body.classList.remove('present');
      if (document.fullscreenElement) document.exitFullscreen();
    }}
  }}
  document.getElementById('presentBtn')
    .addEventListener('click', () => present(!isPresent()));
  document.addEventListener('fullscreenchange', () => {{
    if (!document.fullscreenElement) body.classList.remove('present');
  }});
  document.addEventListener('keydown', (e) => {{
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(e.key)) {{ e.preventDefault(); go(nearest() + 1); }}
    else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) {{ e.preventDefault(); go(nearest() - 1); }}
    else if (e.key === 'f' || e.key === 'F') {{ present(!isPresent()); }}
    else if (e.key === 'Home') {{ e.preventDefault(); go(0); }}
    else if (e.key === 'End') {{ e.preventDefault(); go(slides.length - 1); }}
  }});
}})();
</script>
</body>
</html>
"""

# ---------- Markdown ----------
def md_bullets(bullets):
    return "\n".join(("  " * lvl) + f"- {txt}" for lvl, txt in bullets)

def strip_tags(t):
    import re
    return re.sub(r"<[^>]+>", "", t).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

def md_block(b):
    k = b["kind"]
    if k == "code":
        out = [f"```{b['lang']}", b["src"], "```"]
        if b.get("caption"):
            out.append(f"*{b['caption']}*")
        return "\n".join(out)
    if k == "note":
        t = (f"**{strip_tags(b['title'])}:** " if b.get("title") else "")
        return f"> {t}{strip_tags(b['text'])}"
    if k == "image":
        cap = f"\n*{b['caption']}*" if b.get("caption") else ""
        return f"![Slide {b['n']}]({img_path(b['n'])}){cap}"
    if k == "prose":
        return strip_tags(b["text"])
    if k == "olist":
        return "\n".join(f"{i}. {strip_tags(it)}" for i, it in enumerate(b["items"], 1))
    if k == "ulist":
        return "\n".join(f"- {strip_tags(it)}" for it in b["items"])
    return ""

def build_md():
    md = ["# Galaxy Tools 2.0 — Bring your own!\n",
          "*Converted from `User defined tools.pptx` / `User defined tools (1).pdf`. "
          "Code transcribed from the slide screenshots.*\n"]
    for s in SLIDES:
        md.append(f"\n---\n\n## Slide {s['n']}" + (f": {s['title']}" if s.get("title") else ""))
        if s.get("subtitle"):
            md.append(f"\n**{s['subtitle']}**\n")
        if s.get("bullets"):
            md.append("\n" + md_bullets(s["bullets"]))
        for b in s.get("blocks", []):
            md.append("\n" + md_block(b))
        if s.get("meta"):
            md.append("")
            for m in s["meta"]:
                md.append(f"{m}  ")
    return "\n".join(md) + "\n"

if __name__ == "__main__":
    open("slides.html", "w").write(build_html())
    open("slides.md", "w").write(build_md())
    print("wrote slides.html and slides.md")
