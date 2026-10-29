#!/usr/bin/env python3
"""
DonorChase website builder.

Turns the page files in src/pages/ into a complete static site in _site/,
ready for GitHub Pages (or any static host). No dependencies beyond Python 3.

    python3 build.py                  # build into _site/
    python3 build.py --serve          # build, then preview at http://localhost:8000
    python3 build.py --fetch-images   # download any missing images from the live site

Each page file starts with a small header comment:

    <!--
    title: Page title | DonorChase
    description: Meta description for search engines.
    nav: pricing
    -->

followed by the HTML that goes inside <main>. Write links as root paths
("/contact-us", "/images/<file>"); the builder converts them to relative
links so the site works on a custom domain AND on username.github.io/repo/.
"""

import argparse
import datetime
import html
import http.server
import os
import re
import shutil
import socketserver
import sys
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Settings - edit these
# ---------------------------------------------------------------------------

# The public address of the site (used for canonical links, sitemap and the 404 page).
SITE_URL = "https://donorchase.com"

# Formspree form ID for the contact form (the part after formspree.io/f/).
# Create a free form at https://formspree.io and paste the ID here.
FORMSPREE_ID = "YOUR_FORM_ID"

# Where the app login lives.
LOGIN_URL = "https://app.donorchase.com/login"

# If an image is missing from src/static/images, the page links to the copy on
# this site instead, so nothing looks broken while you move the images across.
# Set to "" once all images are committed.
IMAGE_FALLBACK_URL = "https://donorchase.com"

# DonorBoost, our Gift Aid claims software (linked from the menu, footer and several pages).
# In page files, write {{DONORBOOST_URL}} and it is replaced with this address.
DONORBOOST_URL = "https://donorboost.co.uk/"

CONTACT_EMAIL = "info@donorchase.com"
CONTACT_PHONE_DISPLAY = "0 7570 013936"
CONTACT_PHONE_LINK = "07570013936"

# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
SRC_PAGES = ROOT / "src" / "pages"
SRC_STATIC = ROOT / "src" / "static"
OUT = ROOT / "_site"

NAV = [
    ("home", "Home", "/"),
    ("who", "Who it's for", None),  # dropdown, see SEGMENTS
    ("pricing", "Pricing", "/non-profit-accounting-software"),
    ("about", "About us", "/donation-tracking-software"),
    ("giftaid", "Gift Aid", None),  # dropdown, see GIFT_AID_MENU
    ("help", "Help", "/help-articles"),
    ("blog", "Blog", "/blog-and-news"),
    ("contact", "Contact Us", "/contact-us"),
]

SEGMENTS = [
    ("schools", "Schools", "/schools", "Voluntary contributions and school fees"),
    ("membership", "Membership charities", "/membership-charities", "Subscriptions, dues and renewals"),
    ("events", "Fundraising events", "/event-pledges", "Pledges from dinners and appeals"),
]

GIFT_AID_MENU = [
    ("giftaid", "Gift Aid reviews", "/gift-aid-review", "We check past years for Gift Aid you've missed"),
    ("donorboost", "DonorBoost \u2197", DONORBOOST_URL, "Our Gift Aid claims software: upload, reconcile, claim"),
]

DROPDOWNS = {"who": SEGMENTS, "giftaid": GIFT_AID_MENU}


def ext(href):
    """rel attribute for links that leave the site."""
    return ' rel="noopener"' if href.startswith("http") else ""


def header_html(active):
    items = []
    for key, label, href in NAV:
        if key in DROPDOWNS:
            menu = DROPDOWNS[key]
            seg_active = active in [s[0] for s in menu]
            act = ' class="active"'
            links = "\n".join(
                f'<a href="{h}"{act if active == k else ""}{ext(h)}><strong>{l}</strong><span>{d}</span></a>'
                for k, l, h, d in menu
            )
            items.append(f"""<div class="nav-dropdown{' active' if seg_active else ''}">
<button class="nav-dropdown-toggle" type="button" aria-expanded="false">{label} <span class="caret" aria-hidden="true"></span></button>
<div class="nav-dropdown-menu">
{links}
</div>
</div>""")
        else:
            cls = ' class="active"' if key == active else ""
            items.append(f'<a href="{href}"{cls}>{label}</a>')
    items.append(f'<a class="btn btn-login" href="{LOGIN_URL}">Log in</a>')
    nav = "\n".join(items)
    return f"""<header class="site-header">
<div class="container header-inner">
<a class="logo" href="/">
<img src="/images/DonorChase-Logo-WEB.jpg" alt="DonorChase charity bookkeeping software" width="236" height="56" />
</a>
<button class="nav-toggle" type="button" aria-label="Menu" aria-expanded="false">
<span></span><span></span><span></span>
</button>
<nav class="site-nav">
{nav}
</nav>
</div>
</header>"""


def footer_html():
    year = datetime.date.today().year
    nav_links = "\n".join(
        f'<li><a href="{h}">{l}</a></li>'
        for l, h in [
            ("Home", "/"),
            ("Pricing", "/non-profit-accounting-software"),
            ("About Us", "/donation-tracking-software"),
            ("Gift Aid", "/gift-aid-review"),
            ("Integrations", "/software/integrations"),
            ("Help Articles", "/help-articles"),
            ("Blog and News", "/blog-and-news"),
            ("Contact Us", "/contact-us"),
        ]
    )
    seg_links = "\n".join(f'<li><a href="{h}">{l}</a></li>' for _, l, h, _ in SEGMENTS)
    return f"""<section class="footer-cta">
<div class="container">
<img class="footer-logo" src="/images/DonorChase-Logo.png" alt="DonorChase" />
<h2>Contact Us</h2>
<p>For more information, please contact us via email at <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>, or use the contact form.</p>
<a class="btn btn-primary" href="/contact-us">Get in Touch</a>
</div>
</section>

<footer class="site-footer">
<div class="container footer-inner">
<div class="footer-col">
<h3>Navigation</h3>
<ul>
{nav_links}
</ul>
</div>
<div class="footer-col">
<h3>Who it's for</h3>
<ul>
{seg_links}
</ul>
</div>
<div class="footer-col">
<h3>Our products</h3>
<ul>
<li><a href="/">DonorChase</a> &ndash; donor and pledge tracking</li>
<li><a href="{DONORBOOST_URL}" rel="noopener">DonorBoost</a> &ndash; Gift Aid claims</li>
<li><a href="/blog-and-news/bankline-convertor">Xero to Bankline Convertor</a></li>
</ul>
</div>
<div class="footer-col">
<h3>Get in touch</h3>
<ul>
<li><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></li>
<li><a href="tel:{CONTACT_PHONE_LINK}">{CONTACT_PHONE_DISPLAY}</a></li>
</ul>
</div>
<div class="footer-col">
<h3>Legal</h3>
<ul>
<li><a href="/privacy-policy">Privacy Policy</a></li>
<li><a href="/terms-and-conditions">Terms and Conditions</a></li>
</ul>
</div>
</div>
<div class="container copyright">
<p>&copy; {year} DonorChase. All rights reserved.</p>
<p>DonorChase is a trading name of Chasm (Grants) Limited, registered in England and Wales, company number 14190757. Registered office: 13 Elmcroft Avenue, London NW11 0RS.</p>
</div>
</footer>"""


def page_shell(meta, body, url_path):
    title = html.escape(meta.get("title", "DonorChase"), quote=False)
    desc = html.escape(meta.get("description", ""), quote=True)
    canonical = SITE_URL.rstrip("/") + url_path
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<meta name="description" content="{desc}" />
<link rel="canonical" href="{canonical}" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{desc}" />
<meta property="og:url" content="{canonical}" />
<meta property="og:type" content="website" />
<link rel="icon" type="image/png" href="/favicon.png" />
<link rel="stylesheet" href="/css/site.css" />
</head>
<body>
{header_html(meta.get("nav", ""))}

<main>
{body}
</main>

{footer_html()}

<script src="/js/site.js"></script>
</body>
</html>
"""


def parse_page(text):
    m = re.match(r"\s*<!--(.*?)-->\s*", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        text = text[m.end():]
    return meta, text


def url_for(src_file):
    rel = src_file.relative_to(SRC_PAGES).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "index":
        parts = parts[:-1]
    return "/" + "".join(p + "/" for p in parts)


def make_relative(doc, url_path, missing_images, absolute=False):
    """Rewrite root paths (/x) in href/src/action/url() to relative or absolute links."""
    depth = url_path.strip("/").count("/") + 1 if url_path.strip("/") else 0
    prefix = "../" * depth if depth else "./"

    def fix(path):
        if not path.startswith("/") or path.startswith("//"):
            return path
        # split off query/hash
        m = re.match(r"([^?#]*)(.*)", path)
        p, rest = m.group(1), m.group(2)
        last = p.rstrip("/").split("/")[-1]
        is_file = "." in last
        if is_file and (p.startswith("/images/") or p == "/favicon.png") and not (SRC_STATIC / p.lstrip("/")).exists():
            missing_images.add(p)
            if IMAGE_FALLBACK_URL:
                return IMAGE_FALLBACK_URL.rstrip("/") + p + rest
        if not is_file and p != "/" and not p.endswith("/"):
            p += "/"
        if absolute:
            return SITE_URL.rstrip("/") + p + rest
        rel = p.lstrip("/")
        return (prefix + rel if rel else prefix) + rest

    doc = re.sub(r'((?:href|src|action)=")([^"]*)(")', lambda m: m.group(1) + fix(m.group(2)) + m.group(3), doc)
    doc = re.sub(r"(url\(')([^']*)('\))", lambda m: m.group(1) + fix(m.group(2)) + m.group(3), doc)
    return doc


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC_STATIC, OUT, ignore=shutil.ignore_patterns("README*"))
    missing = set()
    urls = []
    for src in sorted(SRC_PAGES.rglob("*.html")):
        meta, body = parse_page(src.read_text(encoding="utf-8"))
        body = body.replace("{{FORMSPREE_ID}}", FORMSPREE_ID).replace("{{DONORBOOST_URL}}", DONORBOOST_URL)
        url_path = url_for(src)
        doc = page_shell(meta, body, url_path)
        doc = make_relative(doc, url_path, missing)
        dest = OUT / url_path.lstrip("/") / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(doc, encoding="utf-8")
        if meta.get("sitemap", "yes") != "no":
            urls.append(url_path)

    # 404 page: GitHub Pages serves it at any depth, so it uses absolute links.
    nf_meta = {"title": "Page not found | DonorChase", "description": "Page not found.", "nav": ""}
    nf_body = """<section class="page-hero"><div class="container"><h1>Page not found</h1>
<p>Sorry, we couldn't find that page.</p></div></section>
<section class="block"><div class="container center">
<p>It may have moved when we updated the website.</p>
<p class="section-cta"><a class="btn btn-primary" href="/">Go to the homepage</a></p>
</div></section>"""
    (OUT / "404.html").write_text(make_relative(page_shell(nf_meta, nf_body, "/404"), "/", missing, absolute=True), encoding="utf-8")

    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"<url><loc>{SITE_URL.rstrip('/')}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls]
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL.rstrip('/')}/sitemap.xml\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Built {len(urls)} pages into {OUT.relative_to(ROOT)}/")
    if FORMSPREE_ID == "YOUR_FORM_ID":
        print("NOTE: contact form not connected yet - set FORMSPREE_ID in build.py")
    if missing:
        print(f"NOTE: {len(missing)} image(s) not in src/static/images yet"
              + (f" - linking to {IMAGE_FALLBACK_URL} for now." if IMAGE_FALLBACK_URL else "."))
        print("      Run: python3 build.py --fetch-images")
    return missing


def all_image_refs():
    refs = set()
    for f in list(SRC_PAGES.rglob("*.html")) + [ROOT / "build.py", SRC_STATIC / "css" / "site.css"]:
        refs |= set(re.findall(r"(/images/[\w\-./]+\.(?:png|jpe?g|gif|svg|webp))", f.read_text(encoding="utf-8")))
    refs.add("/favicon.png")
    return sorted(refs)


def fetch_images():
    base = IMAGE_FALLBACK_URL or SITE_URL
    got = 0
    for ref in all_image_refs():
        dest = SRC_STATIC / ref.lstrip("/")
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(base.rstrip("/") + ref, timeout=30) as r:
                dest.write_bytes(r.read())
            got += 1
            print("  downloaded", ref)
        except Exception as e:  # noqa: BLE001
            print("  could not download", ref, "-", e)
    print(f"Downloaded {got} file(s) into src/static/. Commit them to the repository.")


def serve():
    os.chdir(OUT)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", 8000), handler) as httpd:
        print("Preview at http://localhost:8000  (Ctrl+C to stop)")
        httpd.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--fetch-images", action="store_true")
    a = ap.parse_args()
    if a.fetch_images:
        fetch_images()
    build()
    if a.serve:
        serve()
    sys.exit(0)
