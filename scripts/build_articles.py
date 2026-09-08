#!/usr/bin/env python3
"""Render Pages-CMS-authored Markdown articles into static HTML.

Reads content/articles/*.md (YAML frontmatter + Markdown body, written by
Pages CMS), and generates:
  - public/articles/<slug>/index.html   for every non-draft article
  - public/articles/index.html          the Insights listing page
  - public/sitemap.xml                  homepage + listing + published articles
  - public/rss.xml                      RSS 2.0 feed of published articles

Draft articles (draft: true) are parsed (so they can be reported) but never
written to public/ — they never become part of the deployed site.

Stdlib only, by design: this site has no build step and no package manager,
and the Markdown this needs to handle is exactly what Pages CMS's rich-text
editor produces (headings, bold/italic, links, images, lists, blockquotes,
inline/fenced code, paragraphs). No table support.
"""
import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content" / "articles"
PUBLIC_DIR = ROOT / "public"
ARTICLES_OUT = PUBLIC_DIR / "articles"
DOMAIN = "https://divyakunaparaju.github.io"
BASE_URL = f"{DOMAIN}/divya-site"
SITE_NAME = "Divya Kunaparaju"
AUTHOR_NAME = "Divya Kunaparaju"


# ─── Frontmatter parsing ──────────────────────────────────────────────────
def _coerce(value):
    v = value.strip()
    if v.startswith('"') and v.endswith('"') and len(v) >= 2:
        v = v[1:-1].replace('\\n', '\n').replace('\\"', '"')
    elif v.startswith("'") and v.endswith("'") and len(v) >= 2:
        v = v[1:-1]
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    return v


def parse_frontmatter(text):
    """Flat key: value frontmatter only — matches what this CMS schema writes.
    Returns (fields_dict, body_markdown)."""
    if not text.startswith("---"):
        raise ValueError("missing --- frontmatter delimiter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("malformed frontmatter block")
    _, fm_block, body = parts
    fields = {}
    for line in fm_block.splitlines():
        line = line.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = _coerce(value)
    return fields, body.strip("\n")


# ─── Markdown → HTML (small, dependency-free subset) ──────────────────────
def _esc(s):
    return html.escape(s, quote=True)


def _inline(text):
    text = _esc(text)
    # images ![alt](src)
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
        lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}" loading="lazy" />',
        text,
    )
    # links [text](href)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
        lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener noreferrer">{m.group(1)}</a>',
        text,
    )
    # bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    # italic (after bold, so **x** isn't half-eaten by *x*)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"<em>\1</em>", text)
    # inline code
    text = re.sub(r"`([^`]+?)`", r"<code>\1</code>", text)
    return text


def render_markdown(md):
    lines = md.replace("\r\n", "\n").split("\n")
    html_parts = []
    i = 0
    list_stack = None  # ('ul' | 'ol', [items])

    def flush_list():
        nonlocal list_stack
        if list_stack:
            tag, items = list_stack
            html_parts.append(f"<{tag}>")
            for item in items:
                html_parts.append(f"<li>{_inline(item)}</li>")
            html_parts.append(f"</{tag}>")
            list_stack = None

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            flush_list()
            i += 1
            continue

        # fenced code block
        fence = re.match(r"^```(\w*)", line)
        if fence:
            flush_list()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            code = _esc("\n".join(code_lines))
            html_parts.append(f"<pre><code>{code}</code></pre>")
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            flush_list()
            level = len(heading.group(1))
            html_parts.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        if line.lstrip().startswith(">"):
            flush_list()
            quote_lines = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quote_lines.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            html_parts.append(f"<blockquote><p>{_inline(' '.join(quote_lines))}</p></blockquote>")
            continue

        unordered = re.match(r"^\s*[-*]\s+(.*)$", line)
        ordered = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if unordered or ordered:
            tag = "ul" if unordered else "ol"
            item_text = (unordered or ordered).group(1)
            if list_stack and list_stack[0] != tag:
                flush_list()
            if not list_stack:
                list_stack = (tag, [])
            list_stack[1].append(item_text)
            i += 1
            continue

        flush_list()
        # paragraph: collect contiguous non-blank, non-block-start lines
        para_lines = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#{1,6})\s|^\s*[-*]\s|^\s*\d+\.\s|^\s*>|^```", lines[i]
        ):
            para_lines.append(lines[i])
            i += 1
        html_parts.append(f"<p>{_inline(' '.join(para_lines))}</p>")

    flush_list()
    return "\n".join(html_parts)


# ─── Article loading ───────────────────────────────────────────────────────
class Article:
    def __init__(self, path, fields, body_md):
        self.path = path
        self.title = fields.get("title", "").strip()
        self.slug = fields.get("slug", "").strip()
        self.summary = fields.get("summary", "").strip()
        self.date = fields.get("date", "").strip()
        self.image = (fields.get("image") or "").strip()
        self.draft = bool(fields.get("draft", True))
        self.seo_title = (fields.get("seoTitle") or "").strip() or self.title
        self.seo_description = (fields.get("seoDescription") or "").strip() or self.summary
        self.body_html = render_markdown(body_md)

    @property
    def url(self):
        return f"{BASE_URL}/articles/{self.slug}/"


def load_articles():
    articles, errors = [], []
    if not CONTENT_DIR.exists():
        return articles, errors
    for path in sorted(CONTENT_DIR.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
            fields, body_md = parse_frontmatter(text)
            article = Article(path, fields, body_md)
            if not article.slug:
                raise ValueError("missing required field: slug")
            if not article.title:
                raise ValueError("missing required field: title")
            articles.append(article)
        except Exception as exc:
            errors.append((path, str(exc)))
    return articles, errors


# ─── HTML templates ────────────────────────────────────────────────────────
NAV = """  <nav class="nav" id="nav" aria-label="Site navigation">
    <div class="nav-inner">
      <a href="/divya-site/" class="nav-logo" aria-label="Divya Kunaparaju — home">DK</a>
      <ul class="nav-links" id="nav-links" role="list">
        <li><a href="/divya-site/#about">About</a></li>
        <li><a href="/divya-site/#expertise">Expertise</a></li>
        <li><a href="/divya-site/#projects">Projects</a></li>
        <li><a href="/divya-site/articles/">Insights</a></li>
        <li><a href="/divya-site/#contact" class="nav-cta">Contact</a></li>
      </ul>
      <button class="nav-toggle" aria-label="Toggle navigation" aria-expanded="false" aria-controls="nav-links">
        <span></span><span></span><span></span>
      </button>
    </div>
  </nav>"""

FOOTER = """  <footer class="footer">
    <div class="footer-inner">
      <p>© 2026 Divya Kunaparaju &middot; Singapore</p>
    </div>
  </footer>"""

HEAD_ASSETS = """  <link rel="canonical" href="{canonical}" />
  <link rel="icon" href="/divya-site/favicon.svg" type="image/svg+xml" />
  <link rel="alternate" type="application/rss+xml" title="Divya Kunaparaju — Insights" href="{base_url}/rss.xml" />

  <meta property="og:type" content="{og_type}" />
  <meta property="og:site_name" content="{site_name}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:locale" content="en_SG" />
{og_image}
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{description}" />
{twitter_image}
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link
    rel="preload"
    as="style"
    href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@300;400;500;600&display=swap"
    onload="this.onload=null;this.rel='stylesheet'"
  />
  <noscript>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@300;400;500;600&display=swap" />
  </noscript>
  <link rel="stylesheet" href="/divya-site/style.css" />"""


def page_shell(title, description, canonical, body_html, og_type="website", image_url=None, extra_head=""):
    if image_url:
        og_image = (
            f'  <meta property="og:image" content="{image_url}" />\n'
            f'  <meta property="og:image:alt" content="{_esc(title)}" />'
        )
        twitter_image = f'  <meta name="twitter:image" content="{image_url}" />'
    else:
        og_image = ""
        twitter_image = ""

    head_assets = HEAD_ASSETS.format(
        canonical=canonical,
        base_url=BASE_URL,
        og_type=og_type,
        site_name=SITE_NAME,
        title=_esc(title),
        description=_esc(description),
        og_image=og_image,
        twitter_image=twitter_image,
    )

    return f"""<!DOCTYPE html>
<html lang="en-SG">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{_esc(title)}</title>
  <meta name="description" content="{_esc(description)}" />
  <meta name="robots" content="index, follow" />
  <meta name="author" content="{AUTHOR_NAME}" />
  <meta name="theme-color" content="#0D1B2A" />
{head_assets}
{extra_head}
</head>
<body>
  <a href="#main" class="skip-link">Skip to main content</a>

{NAV}

  <main id="main">
{body_html}
  </main>

{FOOTER}

  <script src="/divya-site/main.js"></script>
</body>
</html>
"""


def article_page(article):
    # Pages CMS writes the image field as an already-site-rooted path
    # (e.g. "/divya-site/media/articles/photo.jpg", per .pages.yml's media
    # `output` config) — so we prefix the bare domain, not BASE_URL, or
    # we'd double up the "/divya-site" segment.
    if article.image:
        image_url = f"{DOMAIN}{article.image}" if article.image.startswith("/") else f"{BASE_URL}/{article.image}"
    else:
        image_url = None
    figure = (
        f'          <img class="article-hero-image" src="{image_url}" alt="{_esc(article.title)}" loading="eager" />\n'
        if image_url
        else ""
    )
    json_ld_image = f',\n    "image": "{image_url}"' if image_url else ""

    json_ld = f"""  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{_esc(article.title)}",
    "description": "{_esc(article.seo_description)}",
    "author": {{"@type": "Person", "name": "{AUTHOR_NAME}"}},
    "datePublished": "{article.date}",
    "dateModified": "{article.date}",
    "mainEntityOfPage": "{article.url}"{json_ld_image}
  }}
  </script>"""

    body = f"""    <section class="section reveal">
      <div class="section-inner section-inner--article">
        <article class="article">
          <p class="article-back"><a href="/divya-site/articles/">&larr; Back to Insights</a></p>
{figure}          <h1 class="article-title">{_esc(article.title)}</h1>
          <p class="article-byline">{AUTHOR_NAME} &middot; {article.date}</p>
          <div class="article-body">
{article.body_html}
          </div>
          <p class="article-back article-back--bottom"><a href="/divya-site/articles/">&larr; Back to Insights</a></p>
        </article>
      </div>
    </section>"""

    return page_shell(
        title=f"{article.seo_title} | {SITE_NAME}",
        description=article.seo_description,
        canonical=article.url,
        body_html=body,
        og_type="article",
        image_url=image_url,
        extra_head=json_ld,
    )


def listing_page(published):
    if published:
        cards = []
        for a in published:
            cards.append(f"""          <article class="article-card">
            <p class="article-card-date">{a.date}</p>
            <h2 class="article-card-title"><a href="/divya-site/articles/{a.slug}/">{_esc(a.title)}</a></h2>
            <p class="article-card-summary">{_esc(a.summary)}</p>
            <a href="/divya-site/articles/{a.slug}/" class="article-card-link">Read <span aria-hidden="true">&rarr;</span></a>
          </article>""")
        list_html = '        <div class="articles-list">\n' + "\n".join(cards) + "\n        </div>"
    else:
        list_html = '        <p class="articles-empty">No articles published yet — check back soon.</p>'

    body = f"""    <section class="section reveal">
      <div class="section-inner">
        <h1 class="section-eyebrow">Insights</h1>
        <p class="section-sub">Writing on enterprise transformation, cross-functional programme delivery, and practical AI adoption.</p>
{list_html}
      </div>
    </section>"""

    return page_shell(
        title=f"Insights | {SITE_NAME}",
        description="Writing by Divya Kunaparaju on enterprise transformation, cross-functional programme management, and hands-on AI adoption.",
        canonical=f"{BASE_URL}/articles/",
        body_html=body,
    )


def build_sitemap(published):
    urls = [(f"{BASE_URL}/", "monthly", "1.0", None), (f"{BASE_URL}/articles/", "weekly", "0.8", None)]
    for a in published:
        urls.append((a.url, "monthly", "0.6", a.date))
    entries = []
    for loc, changefreq, priority, lastmod in urls:
        lastmod_tag = f"\n    <lastmod>{lastmod}</lastmod>" if lastmod else ""
        entries.append(
            f"  <url>\n    <loc>{loc}</loc>{lastmod_tag}\n    <changefreq>{changefreq}</changefreq>\n    <priority>{priority}</priority>\n  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


def build_rss(published):
    items = []
    for a in published:
        items.append(f"""    <item>
      <title>{_esc(a.title)}</title>
      <link>{a.url}</link>
      <guid>{a.url}</guid>
      <pubDate>{a.date}</pubDate>
      <description>{_esc(a.summary)}</description>
    </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{SITE_NAME} — Insights</title>
    <link>{BASE_URL}/articles/</link>
    <description>Writing by {AUTHOR_NAME} on enterprise transformation, cross-functional programme management, and hands-on AI adoption.</description>
{chr(10).join(items)}
  </channel>
</rss>
"""


def main():
    articles, errors = load_articles()
    published = [a for a in articles if not a.draft]
    drafts = [a for a in articles if a.draft]
    published.sort(key=lambda a: a.date, reverse=True)

    if ARTICLES_OUT.exists():
        shutil.rmtree(ARTICLES_OUT)
    ARTICLES_OUT.mkdir(parents=True, exist_ok=True)

    for article in published:
        out_dir = ARTICLES_OUT / article.slug
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(article_page(article), encoding="utf-8")

    (ARTICLES_OUT / "index.html").write_text(listing_page(published), encoding="utf-8")
    (PUBLIC_DIR / "sitemap.xml").write_text(build_sitemap(published), encoding="utf-8")
    (PUBLIC_DIR / "rss.xml").write_text(build_rss(published), encoding="utf-8")

    print(f"Articles: {len(published)} published, {len(drafts)} draft (excluded from public/).")
    for a in drafts:
        print(f"  draft (skipped): {a.slug}  <- {a.path.relative_to(ROOT)}")
    for path, err in errors:
        print(f"  ERROR parsing {path.relative_to(ROOT)}: {err}")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
