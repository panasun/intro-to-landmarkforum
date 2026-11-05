# Intro to Landmark Forum

Presentation deck, live at https://landmark-forum-intro.pages.dev

- `deck/` — slide sources (one `<section>` per file, order in `deck/deck.json`)
- `site/` — the published site; `site/index.html` is generated, images live in `site/images/`
- `tools/build.py` — builds `site/index.html` from `deck/`

```bash
python3 tools/build.py deck site/index.html
```

Every push to `main` rebuilds and deploys to Cloudflare Pages (`.github/workflows/deploy.yml`).
It needs the repo secret `CLOUDFLARE_API_TOKEN` (a token with **Cloudflare Pages: Edit**).

Controls: → / Space / click = next, ← = back, `f` = fullscreen. Each click reveals the next step on slides with builds.
