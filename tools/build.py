"""Build a standalone HTML presentation from the Slides deck files.
usage: python3 -I build.py <deck_project_dir> <out_html>"""
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

def shape(m):
    attrs, kind_attrs = m.group(1), m.group(0)
    kind = re.search(r'kind="([^"]+)"', kind_attrs).group(1)
    style = re.search(r'style="([^"]*)"', kind_attrs).group(1)
    build = re.search(r'(data-build-in="[^"]*")', kind_attrs)
    build = " " + build.group(1) if build else ""
    if kind.startswith("arrow"):
        color = re.search(r"background:\s*([^;]+)", style).group(1).strip()
        style = re.sub(r"background:[^;]+;?", "", style)
        pts = "0,15 60,15 60,0 100,25 60,50 60,35 0,35" if kind == "arrow-right" else "100,15 40,15 40,0 0,25 40,50 40,35 100,35"
        return f'<svg{build} style="{style}" viewBox="0 0 100 50" preserveAspectRatio="none"><polygon points="{pts}" fill="{color}"/></svg>'
    if kind == "ellipse":
        style += ";border-radius:50%"
    return f'<div{build} style="{style}"></div>'

slides = []
for sid in deck["order"]:
    h = open(f"{src}/slides/{sid}.html", encoding="utf-8").read()
    h = re.sub(r"<aside>.*?</aside>", "", h, flags=re.S)  # speaker notes stay private
    h = re.sub(r"<x-shape([^>]*)></x-shape>", shape, h)
    for k, v in BLOBS.items():
        h = h.replace(f"/_blob/{k}", v)
    assert "/_blob/" not in h and "<x-" not in h, sid
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
#stage{{position:absolute;left:50%;top:50%;width:1920px;height:1080px;transform-origin:0 0}}
.slide{{position:absolute;inset:0;opacity:0;pointer-events:none;transition:opacity .45s ease}}
.slide.on{{opacity:1;pointer-events:auto}}
.slide>section{{position:relative;width:1920px;height:1080px;overflow:hidden}}
h1{{line-height:1.1}} h2{{line-height:1.15}} h3{{line-height:1.2}} p{{line-height:1.4}}
img,svg{{display:block}}
table{{border-collapse:collapse;width:100%}} th,td{{padding:.35em .6em;text-align:left;border-bottom:1px solid #d3ccbc}}
hr{{border:0}}
[data-build-in]{{transition:opacity .5s ease,transform .5s ease}}
[data-build-in].pending{{opacity:0}}
[data-build-in^="rise"].pending{{transform:translateY(40px)}}
[data-build-in^="left"].pending{{transform:translateX(-60px)}}
[data-build-in^="right"].pending{{transform:translateX(60px)}}
[data-build-in^="pop"].pending{{transform:scale(.85)}}
#count{{position:fixed;right:16px;bottom:12px;color:#8a9bb8;font:14px system-ui;user-select:none}}
</style></head>
<body>
<div id="stage">
{chr(10).join(slides)}
</div>
<div id="count"></div>
<script>
const slides=[...document.querySelectorAll('.slide')];
const stage=document.getElementById('stage'), count=document.getElementById('count');
let i=0, step=0;
const order=el=>parseInt((el.dataset.buildIn.split(' ')[1])||'1',10);
const steps=s=>Math.max(0,...[...s.querySelectorAll('[data-build-in]')].map(order));
function show(n,full){{
  i=Math.max(0,Math.min(slides.length-1,n));
  step=full?steps(slides[i]):0;
  slides.forEach((s,k)=>s.classList.toggle('on',k===i));
  paint(); location.hash=i+1;
}}
function paint(){{
  slides[i].querySelectorAll('[data-build-in]').forEach(el=>el.classList.toggle('pending',order(el)>step));
  count.textContent=(i+1)+' / '+slides.length;
}}
function next(){{ if(step<steps(slides[i])){{step++;paint();}} else if(i<slides.length-1) show(i+1); }}
function prev(){{ if(step>0){{step--;paint();}} else if(i>0) show(i-1,true); }}
function fit(){{ const k=Math.min(innerWidth/1920,innerHeight/1080);
  stage.style.transform=`scale(${{k}}) translate(-50%,-50%)`; stage.style.left=stage.style.top='50%';
  stage.style.transform=`translate(-50%,-50%) scale(${{k}})`; stage.style.transformOrigin='center'; }}
addEventListener('resize',fit); fit();
addEventListener('keydown',e=>{{
  if(['ArrowRight','ArrowDown','PageDown',' ','Enter'].includes(e.key)){{e.preventDefault();next();}}
  else if(['ArrowLeft','ArrowUp','PageUp','Backspace'].includes(e.key)){{e.preventDefault();prev();}}
  else if(e.key==='Home') show(0); else if(e.key==='End') show(slides.length-1,true);
  else if(e.key==='f') document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();
}});
addEventListener('click',e=>{{ e.clientX<innerWidth/3?prev():next(); }});
show((parseInt(location.hash.slice(1),10)||1)-1);
</script>
</body></html>
"""
open(out, "w", encoding="utf-8").write(html)
print(f"wrote {out}: {len(slides)} slides")
