"""Build a standalone HTML presentation from the Slides deck files.
usage: python3 -I build.py <deck_project_dir> <out_html>

Desktop / landscape: 1920x1080 slides scaled to fit, click or arrow keys to step.
Phone portrait: slides reflow into one scrolling page (all builds shown)."""
import json, re, sys

src, out = sys.argv[1], sys.argv[2]
deck = json.load(open(f"{src}/deck.json", encoding="utf-8"))
BLOBS = {
    "1e0bd88f9f6243e110a7e5c414a28adb": "images/board.jpg",
    "161d9374df297bc4391b92d91f565aba": "images/blank.jpg",
    "936923180ccd3fa05905b46ac5a0c6dd": "images/q1.jpg",
    "7b901dd1401dc130851484aaa3e35317": "images/q2.jpg",
    "7a1fb062ed0820cdc1fb720d1d8ae424": "images/q3.jpg",
    "3bcab2e7b5743169e5b2915db79e50a6": "images/q4.jpg",
}
VOID = {"br", "img", "hr", "input", "meta", "link"}
TAG = re.compile(r"<(/?)([a-zA-Z][\w-]*)\b[^>]*?(/?)>")


def shape(m):
    tag = m.group(0)
    kind = re.search(r'kind="([^"]+)"', tag).group(1)
    style = re.search(r'style="([^"]*)"', tag).group(1)
    build = re.search(r'(data-build-in="[^"]*")', tag)
    build = " " + build.group(1) if build else ""
    if kind.startswith("arrow"):
        color = re.search(r"background:\s*([^;]+)", style).group(1).strip()
        style = re.sub(r"background:[^;]+;?", "", style)
        pts = "0,15 60,15 60,0 100,25 60,50 60,35 0,35" if kind == "arrow-right" else "100,15 40,15 40,0 0,25 40,50 40,35 100,35"
        return f'<svg class="m-arrow"{build} style="{style}" viewBox="0 0 100 50" preserveAspectRatio="none"><polygon points="{pts}" fill="{color}"/></svg>'
    if kind == "ellipse":
        style += ";border-radius:50%"
    return f'<div{build} style="{style}"></div>'


def children(inner):
    """(start, end) spans of the top-level elements in a section's inner HTML."""
    spans, depth, start = [], 0, 0
    for m in TAG.finditer(inner):
        close, tag, selfclose = m.group(1), m.group(2).lower(), m.group(3)
        if tag in VOID or selfclose:
            if depth == 0:
                spans.append((m.start(), m.end()))
        elif not close:
            if depth == 0:
                start = m.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                spans.append((start, m.end()))
    assert depth == 0
    return spans


def num(style, prop):
    m = re.search(rf"(?<![-\w]){prop}:\s*([\d.]+)px", style)
    return float(m.group(1)) if m else None


def add_class(el, cls):
    return re.sub(r"^<([\w-]+)", rf'<\1 class="{cls}"', el, count=1) if 'class="' not in el[:el.find(">")] else el.replace('class="', f'class="{cls} ', 1)


def mobile_marks(sid, h):
    """Tag elements for the phone layout: hide decoration and step trackers, keep the pie chart intact."""
    o = h.index(">", h.index("<section")) + 1
    c = h.rindex("</section>")
    inner = h[o:c]
    els = [inner[a:b] for a, b in children(inner)]
    out, pie = [], []
    for el in els:
        head = el[: el.find(">") + 1]
        style = (re.search(r'style="([^"]*)"', head) or [None, ""])[1]
        absolute = "position:absolute" in style.replace(" ", "")
        text = re.sub(r"<[^>]+>", "", el).strip()
        left, top = num(style, "left"), num(style, "top")
        if absolute and not text and not el.startswith(("<svg", "<img")):
            el = add_class(el, "m-hide")  # decorative rings
        elif absolute and "bottom:64px" in style.replace(" ", "") and el.startswith("<div"):
            el = add_class(el, "m-hide")  # step tracker row
        elif sid == "pattern" and absolute and top is not None and top < 340:
            el = add_class(el, "m-hide")  # loop arrow + its label
        elif sid == "blindspot" and absolute and left is not None and left < 800 and top is not None and top >= 330:
            el = re.sub(r"(?<![-\w])left:\s*([\d.]+)px", lambda m: f"left:{float(m.group(1)) - 160:g}px", el, count=1)
            el = re.sub(r"(?<![-\w])top:\s*([\d.]+)px", lambda m: f"top:{float(m.group(1)) - 330:g}px", el, count=1)
            pie.append(el)
            if len(pie) == 1:
                out.append("\0PIE\0")
            continue
        out.append(el)
    body = "\n".join(out).replace("\0PIE\0", '<div class="pie">' + "\n".join(pie) + "</div>")
    return h[:o] + "\n" + body + "\n" + h[c:]


slides = []
for sid in deck["order"]:
    h = open(f"{src}/slides/{sid}.html", encoding="utf-8").read()
    h = re.sub(r"<aside>.*?</aside>", "", h, flags=re.S)  # speaker notes stay private
    h = re.sub(r"<x-shape([^>]*)></x-shape>", shape, h)
    for k, v in BLOBS.items():
        h = h.replace(f"/_blob/{k}", v)
    assert "/_blob/" not in h and "<x-" not in h, sid
    h = mobile_marks(sid, h)
    slides.append(f'<div class="slide">{h.strip()}</div>')

fonts = "".join(f'<link rel="stylesheet" href="{f["href"]}">' for f in deck["faces"].values())
html = f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{deck["title"]}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{fonts}
<style>
*{{box-sizing:border-box;margin:0}}
html,body{{height:100%;background:#0b1220;overflow:hidden;font-family:'IBM Plex Sans Thai',Tahoma,sans-serif}}
#stage{{position:absolute;left:50%;top:50%;width:1920px;height:1080px;transform-origin:center}}
.slide{{position:absolute;inset:0;opacity:0;pointer-events:none;transform:scale(1.015);transition:opacity .7s cubic-bezier(.4,0,.2,1),transform .9s cubic-bezier(.22,1,.36,1)}}
.slide.on{{opacity:1;pointer-events:auto;transform:none}}
.slide>section{{position:relative;width:1920px;height:1080px;overflow:hidden}}
h1{{line-height:1.1}} h2{{line-height:1.15}} h3{{line-height:1.2}} p{{line-height:1.4}}
img,svg{{display:block}}
table{{border-collapse:collapse;width:100%}} th,td{{padding:.35em .6em;text-align:left;border-bottom:1px solid #d3ccbc}}
hr{{border:0}}
.pie{{position:absolute;left:160px;top:330px;width:600px;height:600px}}
[data-build-in]{{transition:opacity .7s cubic-bezier(.4,0,.2,1),transform .8s cubic-bezier(.22,1,.36,1)}}
[data-build-in]:not(.shown){{opacity:0}}
.reset [data-build-in]{{transition:none!important}}
[data-build-in^="rise"]:not(.shown){{transform:translateY(40px)}}
[data-build-in^="left"]:not(.shown){{transform:translateX(-60px)}}
[data-build-in^="right"]:not(.shown){{transform:translateX(60px)}}
[data-build-in^="pop"]:not(.shown){{transform:scale(.85)}}
#count{{position:fixed;right:16px;bottom:12px;color:#8a9bb8;font:14px system-ui;user-select:none}}

/* phone portrait: one scrolling page, layout reflowed at a 760px virtual width */
html.m,html.m body{{height:auto;overflow:auto}}
.m #stage{{position:static;width:auto;height:auto;transform:none!important}}
.m .slide{{position:relative;opacity:0;pointer-events:auto;width:760px;zoom:var(--z);transform:translateY(32px)}}
.m .slide.seen{{opacity:1;transform:none}}
html.m{{scroll-behavior:smooth}}
.m .slide>section{{width:760px!important;height:auto!important;padding:72px 40px!important;display:flex!important;flex-direction:column!important;gap:28px!important;overflow:visible}}
.m section *:not(.pie *):not([id=people-ring] *){{position:static!important;left:auto!important;top:auto!important;right:auto!important;bottom:auto!important;max-width:100%!important;white-space:normal!important}}
.m section div:has(>img),.m section div:has(>div>table){{flex-wrap:wrap}}
.m section h1{{font-size:120px!important}}
.m section div[style*="width:460px"]{{width:100%!important}}
.m section img{{height:auto!important}}
.m section div:has(>table){{flex-basis:100%!important}}
.m .slide section div.pie,.m .slide section div[id=people-ring]{{position:relative!important;align-self:center;flex:none}}
.m section .m-hide{{display:none!important}}
.m section .m-arrow{{rotate:90deg;align-self:center;margin:8px 0}}
.m section>div[style*="border-radius:50%"],.m section>p[style*="width:340px"],.m section>div[style*="width:392px"]{{align-self:center}}
.m [data-build-in]{{opacity:1!important;transform:none!important}}
.m #count{{display:none}}
@media (prefers-reduced-motion:reduce){{.slide,[data-build-in]{{transition:none!important}}.m .slide{{opacity:1;transform:none}}}}
</style></head>
<body>
<div id="stage">
{chr(10).join(slides)}
</div>
<div id="count"></div>
<script>
const slides=[...document.querySelectorAll('.slide')];
const stage=document.getElementById('stage'), count=document.getElementById('count'), root=document.documentElement;
const phone=matchMedia('(max-width: 900px) and (orientation: portrait)');
let i=0, step=0;
const order=el=>parseInt((el.dataset.buildIn.split(' ')[1])||'1',10);
const steps=s=>Math.max(0,...[...s.querySelectorAll('[data-build-in]')].map(order));
function show(n,full){{
  i=Math.max(0,Math.min(slides.length-1,n));
  step=full?steps(slides[i]):0;
  slides.forEach((s,k)=>s.classList.toggle('on',k===i));
  const s=slides[i]; s.classList.add('reset'); paint(); void s.offsetWidth; s.classList.remove('reset');
  history.replaceState(null,'','#'+(i+1));
}}
function paint(){{
  slides[i].querySelectorAll('[data-build-in]').forEach(el=>el.classList.toggle('shown',order(el)<=step));
  count.textContent=(i+1)+' / '+slides.length;
}}
function next(){{ if(step<steps(slides[i])){{step++;paint();}} else if(i<slides.length-1) show(i+1); }}
function prev(){{ if(step>0){{step--;paint();}} else if(i>0) show(i-1,true); }}
function layout(){{
  root.classList.toggle('m',phone.matches);
  if(phone.matches){{ root.style.setProperty('--z',innerWidth/760); return; }}
  slides.forEach(s=>s.classList.add('seen'));
  const k=Math.min(innerWidth/1920,innerHeight/1080);
  stage.style.transform=`translate(-50%,-50%) scale(${{k}})`;
}}
const io=new IntersectionObserver(es=>es.forEach(e=>{{ if(e.isIntersecting){{ e.target.classList.add('seen'); io.unobserve(e.target); }} }}),{{threshold:0.12}});
slides.forEach(s=>io.observe(s));
addEventListener('resize',layout); layout();
addEventListener('keydown',e=>{{
  if(phone.matches) return;
  if(['ArrowRight','ArrowDown','PageDown',' ','Enter'].includes(e.key)){{e.preventDefault();next();}}
  else if(['ArrowLeft','ArrowUp','PageUp','Backspace'].includes(e.key)){{e.preventDefault();prev();}}
  else if(e.key==='Home') show(0); else if(e.key==='End') show(slides.length-1,true);
  else if(e.key==='f') document.fullscreenElement?document.exitFullscreen():root.requestFullscreen();
}});
addEventListener('click',e=>{{ if(phone.matches) return; e.clientX<innerWidth/3?prev():next(); }});
show((parseInt(location.hash.slice(1),10)||1)-1);
</script>
</body></html>
"""
open(out, "w", encoding="utf-8").write(html)
print(f"wrote {out}: {len(slides)} slides")
