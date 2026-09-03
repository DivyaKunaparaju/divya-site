#!/usr/bin/env python3
"""Fail-fast checks for the technical SEO surface of the site.

No third-party dependencies — stdlib only, runnable in CI with a bare
`python3 scripts/verify-seo.py` from the repo root.
"""
import re
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
CANONICAL = "https://divyakunaparaju.github.io/divya-site/"
NAME = "Divya Kunaparaju"

failures = []
warnings = []


def fail(msg):
    failures.append(msg)


def warn(msg):
    warnings.append(msg)


def read(path):
    if not path.exists():
        fail(f"missing file: {path.relative_to(ROOT)}")
        return None
    return path.read_text(encoding="utf-8")


html = read(PUBLIC / "index.html")

if html is not None:
    title_match = re.search(r"<title>(.*?)</title>", html, re.S)
    if not title_match:
        fail("no <title> tag found")
    else:
        title = re.sub(r"&amp;", "&", title_match.group(1)).strip()
        if NAME not in title:
            fail(f"<title> does not contain '{NAME}': {title!r}")
        if not (10 <= len(title) <= 70):
            warn(f"<title> length {len(title)} outside the ~10-70 char sweet spot: {title!r}")

    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html)
    if not desc_match:
        fail("no meta description found")
    else:
        desc = desc_match.group(1)
        if not (120 <= len(desc) <= 170):
            warn(f"meta description length {len(desc)} outside ~120-170 chars: {desc!r}")
        if "Singapore" not in desc:
            warn("meta description does not mention 'Singapore'")

    canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]*)"', html)
    if not canonical_match:
        fail("no canonical <link> found")
    elif canonical_match.group(1) != CANONICAL:
        fail(f"canonical URL is {canonical_match.group(1)!r}, expected {CANONICAL!r}")

    robots_match = re.search(r'<meta\s+name="robots"\s+content="([^"]*)"', html)
    if robots_match and "noindex" in robots_match.group(1).lower():
        fail("robots meta tag contains 'noindex'")

    for prop in ["og:title", "og:description", "og:url", "og:site_name", "og:type"]:
        if not re.search(rf'<meta\s+property="{re.escape(prop)}"', html):
            fail(f"missing Open Graph tag: {prop}")

    for name in ["twitter:card", "twitter:title", "twitter:description"]:
        if not re.search(rf'<meta\s+name="{re.escape(name)}"', html):
            fail(f"missing Twitter Card tag: {name}")

    og_image_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]*)"', html)
    if not og_image_match:
        warn("no og:image set (fine if no social-preview image exists yet)")
    else:
        og_image_url = og_image_match.group(1)
        if not og_image_url.startswith(CANONICAL):
            fail(f"og:image is not an absolute URL under the canonical base: {og_image_url!r}")
        else:
            image_path = PUBLIC / og_image_url[len(CANONICAL):]
            if not image_path.exists():
                fail(f"og:image referenced but missing on disk: {image_path.relative_to(ROOT)}")
        if not re.search(r'<meta\s+name="twitter:image"', html):
            fail("og:image is set but twitter:image is missing")

    h1_matches = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    if len(h1_matches) != 1:
        fail(f"expected exactly one <h1>, found {len(h1_matches)}")
    else:
        h1_text = re.sub(r"<[^>]+>", " ", h1_matches[0])
        h1_text = re.sub(r"\s+", " ", h1_text).strip()
        if "Divya" not in h1_text or "Kunaparaju" not in h1_text:
            fail(f"<h1> does not contain the full name: {h1_text!r}")

    ldjson_match = re.search(
        r'<script\s+type="application/ld\+json">(.*?)</script>', html, re.S
    )
    if not ldjson_match:
        fail("no JSON-LD <script type=\"application/ld+json\"> block found")
    else:
        try:
            data = json.loads(ldjson_match.group(1))
        except json.JSONDecodeError as exc:
            fail(f"JSON-LD is not valid JSON: {exc}")
            data = None
        if data is not None:
            if data.get("@type") != "Person":
                fail(f"JSON-LD @type is {data.get('@type')!r}, expected 'Person'")
            if data.get("name") != NAME:
                fail(f"JSON-LD name is {data.get('name')!r}, expected {NAME!r}")
            same_as = data.get("sameAs", [])
            if not any("linkedin.com/in/divya-kunaparaju" in s for s in same_as):
                fail("JSON-LD sameAs does not include the LinkedIn profile URL")

    favicon_match = re.search(r'<link\s+rel="icon"\s+href="([^"]*)"', html)
    if favicon_match:
        favicon_path = PUBLIC / favicon_match.group(1)
        if not favicon_path.exists():
            fail(f"favicon referenced but missing on disk: {favicon_match.group(1)}")

robots_txt = read(PUBLIC / "robots.txt")
if robots_txt is not None:
    if re.search(r"^\s*Disallow:\s*/\s*$", robots_txt, re.M):
        fail("robots.txt has a blanket 'Disallow: /'")
    if "Sitemap:" not in robots_txt:
        warn("robots.txt does not reference a Sitemap")

sitemap_xml = read(PUBLIC / "sitemap.xml")
if sitemap_xml is not None:
    try:
        tree = ET.fromstring(sitemap_xml)
    except ET.ParseError as exc:
        fail(f"sitemap.xml is not valid XML: {exc}")
        tree = None
    if tree is not None:
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [el.text.strip() for el in tree.findall(".//sm:loc", ns) if el.text]
        if not locs:
            fail("sitemap.xml contains no <loc> entries")
        if CANONICAL not in locs:
            fail(f"sitemap.xml does not include the canonical homepage URL {CANONICAL!r}")
        for loc in locs:
            if not loc.startswith("https://divyakunaparaju.github.io/divya-site/"):
                fail(f"sitemap.xml URL outside the expected base path: {loc!r}")
            if "#" in loc:
                fail(f"sitemap.xml contains a fragment-only URL: {loc!r}")

print(f"Checked {PUBLIC}")
for w in warnings:
    print(f"WARN: {w}")
if failures:
    for f in failures:
        print(f"FAIL: {f}")
    print(f"\n{len(failures)} check(s) failed.")
    sys.exit(1)

print(f"All SEO checks passed ({len(warnings)} warning(s)).")
