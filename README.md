# divya-site

Personal portfolio for Divya Kunaparaju — enterprise transformation and cross-functional programme management, with hands-on AI practice.

Built with plain HTML, CSS, and vanilla JavaScript. No frameworks — just open `public/index.html` in a browser to see the homepage as-is. The one exception is the **Articles / Insights** pages, which are generated from Markdown by `scripts/build_articles.py` (see below) — GitHub Actions runs this automatically on every push, so you never need to run it yourself unless you're testing locally.

## Publishing articles with Pages CMS

Articles are written in [Pages CMS](https://pagescms.org), a free browser-based editor connected to this GitHub repository — no code, no VS Code required.

**Signing in**
1. Go to [pagescms.org](https://pagescms.org) and sign in with your GitHub account (the same account that owns this repo).
2. Select the `divya-site` repository. You'll see an **Articles** collection — that's this site's blog.

**Creating an article**
1. Click **Articles → Add entry**.
2. Fill in the fields: Title, URL slug (lowercase, hyphens, no spaces — e.g. `my-first-article`), Short summary, Publication date, and the Article body.
3. A featured image and custom SEO title/description are optional — if you skip them, the site falls back to the Title and Short summary automatically.
4. **"Save as draft" is checked by default.** While it's checked, the article is saved to the repository but never appears on the live site, the Insights list, the sitemap, or the RSS feed — it's completely private.

**Publishing**
1. When you're ready, open the article and uncheck **"Save as draft."**
2. Save/commit the change in Pages CMS.
3. That's it — no other steps. The site rebuilds and redeploys itself automatically.

**Images**
Upload images directly through the image field in the CMS editor — they're stored in `public/media/articles/` in the repository automatically. You don't need to manage files yourself.

**How long it takes to go live**
Saving in Pages CMS commits directly to this repo's `main` branch, which triggers the GitHub Actions deploy workflow. Based on this repo's own recent runs, that workflow typically finishes in under a minute; allow up to 2–3 minutes total for GitHub Pages' CDN to catch up before you see the change live.

**If a publish doesn't show up**
1. Go to the repo on GitHub → the **Actions** tab.
2. Look at the most recent run. If it has a red ✕ next to "Build articles" or "Verify SEO essentials," click it to see why.
3. The most common cause is a required field left blank, or a URL slug with spaces/capital letters/special characters. Fix it in Pages CMS and save again — a new run will kick off automatically.
4. If you're stuck, the error message in that Actions log is exactly what to share with a developer (or paste to Claude) for help.
