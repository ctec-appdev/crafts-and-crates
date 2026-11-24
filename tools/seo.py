#!/usr/bin/env python3
"""
WordPress-replacement SEO kit for Crafts & Crates ATL (static site).

Run from the repository root:  python3 tools/seo.py

What it does (all idempotent):
  1. Injects canonical + Open Graph + Twitter tags into <head> of every page
     (skip list: 404.html). Existing blocks it previously injected are removed
     and re-emitted, so it never duplicates itself.
  2. Adds structured data: Organization JSON-LD on site pages, Event +
     BreadcrumbList JSON-LD on event pages (dates parsed from .post-date).
  3. Writes sitemap.xml (every canonical page, mtime as lastmod).
  4. Writes robots.txt (points at sitemap.xml).
  5. Writes .htaccess: force https + apex host (canonical form), 301-map every
     legacy WordPress URL -> its static replacement, 404 page, caching headers
     (html/css/js 1h, images/fonts 1y immutable) for LiteSpeed/cPanel.
"""

import html as html_mod
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SITE = "https://craftsandcratesatl.com"  # canonical host = apex https (WP's own canonical form)
OG_IMAGE_DEFAULT = "assets/images/IMG_9508.jpg"

START_MARK = "<!-- seo.py -->"
END_MARK = "<!-- /seo.py -->"

# ---------------------------------------------------------------------------
# 1+2. Head injection
# ---------------------------------------------------------------------------

def esc_attr(text: str) -> str:
    return html_mod.escape(text, quote=True)


def parse_head(html: str) -> dict:
    t = re.search(r"<title>(.*?)</title>", html, re.S)
    d = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html)
    return {
        "title": t.group(1) if t else "",
        "desc": d.group(1) if d else "",
    }


def event_date_iso(html: str):
    m = re.search(
        r'class="post-date">\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})',
        html,
    )
    if not m:
        return None
    return datetime.strptime(f"{m.group(1)} {m.group(2)}, {m.group(3)}", "%B %d, %Y").date().isoformat()


VENUE = {
    "@type": "Place",
    "name": "Halfway Crooks Biergarten",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "640 Reed St. SE",
        "addressLocality": "Atlanta",
        "addressRegion": "GA",
        "postalCode": "30312",
        "addressCountry": "US",
    },
}

ORGANIZER = {"@type": "Organization", "name": "Crafts & Crates ATL", "url": SITE}


def org_ld() -> dict:
    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Crafts & Crates ATL",
        "url": SITE,
        "logo": f"{SITE}/assets/images/cropped-CC_Logo.png",
        "sameAs": ["https://www.instagram.com/craftsandcratesatl/"],
        "description": "Live hip-hop events at Halfway Crooks Biergarten in Atlanta's historic Summerhill neighborhood.",
    }
    return data



def homepage_ld() -> dict:
    local_business = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "Crafts & Crates ATL",
        "url": SITE,
        "description": "Live hip-hop events at Halfway Crooks Biergarten in Atlanta's historic Summerhill neighborhood.",
        "address": VENUE["address"],
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": [day], "opens": opens, "closes": closes}
            for day, opens, closes in (
                ("Monday", "00:00", "00:00"),
                ("Tuesday", "00:00", "00:00"),
                ("Wednesday", "00:00", "00:00"),
                ("Thursday", "00:00", "00:00"),
                ("Friday", "17:00", "02:00"),
                ("Saturday", "12:00", "02:00"),
                ("Sunday", "00:00", "00:00"),
            )
        ],
    }
    return local_business


EVENT_PERFORMERS = {
    # Spreadsheet source of truth: Crafts & Crates EventInfo, one row per event.
    # Keys are event-page filenames so headings and capitalization stay exact.
    "april-24-crafts-and-crates.html": ["DJ Popo", "DJ Dainja", "Peppermint Gatty", "DJ Mafioso"],
    "april-25-crafts-and-crates.html": ["Jeremy Avalon", "Sir Daniel", "Peppermint Gatty", "DJ Mafioso"],
    "april-26-crafts-and-crates.html": ["Mafioso", "Sinista", "Gnosis & Sinceelay"],
    "atl-underground-reunion-10-18.html": ["Kaos", "Illustrate", "4-IZE", "Supastition", "John Robinson", "Headkrack", "Eddie Meeks", "A.O.S.", "Flux", "Ekundayo", "G.R.E.A.T. Scott", "Luey Price", "Galaxy High", "MRK SX"],
    "august-23-crafts-and-crates.html": ["DJ Kerosene", "Peppermint Gatty", "DJ Dainja"],
    "august-24-crafts-and-crates.html": ["Oxygen", "Sir Daniel", "Peppermint Gatty", "DJ Mafioso"],
    "august-25-crafts-and-crates.html": ["DJ Kemit", "Spearhead X", "Break Rabbi", "Jason Greene"],
    "august-26-crafts-and-crates.html": ["J-Rawls", "John Doe", "Dainja", "Mafioso", "Peppermint Gatty"],
    "crafts-and-crates-presents-36-chambers-wu-tang-tribute.html": ["Jason Staten", "DJ Kerosene", "DJ Dainja"],
    "crafts-and-crates-presents-all-hail-the-queens.html": ["Empress Rah", "Eboni Atl", "DJ Ghost", "DJ Aquaria"],
    "crafts-and-crates-presents-diamond-d.html": ["Diamond D", "DJ Mafioso", "DJ Dainja"],
    "crafts-and-crates-presents-dj-premier-vs-pete-rock.html": ["DJ Dainja", "DJ Kerosene"],
    "crafts-and-crates-presents-doomsday.html": ["Morgan Garcia", "DJ Dainja"],
    "crafts-and-crates-presents-fantastic-dilla-tribute.html": ["DJ Jaycee", "DJ Dainja"],
    "crafts-and-crates-presents-shook-ones.html": ["DJ Mafioso", "DJ Dainja"],
    "crafts-and-crates-presents-the-almighty-griselda.html": ["DJ Kerosene", "DJ Dainja"],
    "crafts-and-crates-presents-vibes-and-stuff.html": ["Rasta Root", "DJ Dainja"],
    "december-23-crafts-and-crates.html": ["DJ Ghost", "Eljay", "DJ Jaycee", "DJ Dainja", "Mafioso", "Peppermint Gatty"],
    "december-25-crafts-and-crates.html": ["Nicolay", "Maurice Daniels", "Empress Rah", "Stlndrms", "Mafioso"],
    "february-26-crafts-and-crates.html": ["Jamad", "Johnnie Dynemite", "Mafioso", "Peppermint Gatty"],
    "january-26-crafts-and-crates.html": ["Presyce", "Deliver", "Mafioso", "Peppermint Gatty"],
    "july-23-crafts-and-crates.html": ["DJ Og Bobby Johnson", "Peppermint Gatty", "DJ Mafioso", "DJ Dainja"],
    "july-24-crafts-and-crates.html": ["Cozy Shawn", "DJ Dainja", "Peppermint Gatty", "DJ Mafioso"],
    "june-24-crafts-and-crates.html": ["Skyzoo", "DJ Fudge", "Peppermint Gatty", "DJ Mafioso", "DJ Dainja"],
    "june-25-crafts-and-crates.html": ["Sammy B", "DJ Nervex", "DJ Mafioso", "Peppermint Gatty"],
    "march-24-crafts-and-crates.html": ["Cj Plays", "DJ Deliver", "DJ Shakim", "DJ Dainja", "Peppermint Gatty", "DJ Mafioso"],
    "march-25-crafts-and-crates-jax-tribute.html": ["Rasta Root", "DJ Mafioso", "DJ Dainja", "Oxygen"],
    "march-26-crafts-and-crates.html": ["DJ Ghost", "DJ Doc Bintu", "DJ Rasyrious", "Sugar Deluxe"],
    "may-24-crafts-and-crates.html": ["Wally Sparks", "Mettaspin", "DJ Rasyrious", "Peppermint Gatty"],
    "may-26-crafts-and-crates.html": ["Skyzoo", "Michael Mayhem", "Tabone", "Mafioso"],
    "november-23-crafts-and-crates.html": ["Johnny Dynamite", "DJ Larmarrous", "Oxygen", "DJ Dainja", "Peppermint Gatty", "DJ Mafioso"],
    "november-24-crafts-and-crates.html": ["J-Live", "Cj Plays", "Sean Falyon", "DJ Mafioso"],
    "november-25-crafts-and-crates.html": ["Rock Most", "Mighty Paul", "Mafioso", "Peppermint Gatty"],
    "november-26-crafts-and-crates.html": ["Sol Messiah", "John Robinson", "Invizible Handz", "Agent M", "Mafiso", "Peppermint Gatty"],
    "october-23-crafts-and-crates-reunion-edition.html": ["DJ Sky", "DJ Dainja", "Peppermint Gatty", "DJ Mafioso"],
    "october-24-crafts-and-crates-reunion-edition.html": ["DJ Dainja", "DJ Mafioso", "DJ Sky"],
    "october-26-atl-underground-reunion-4.html": ["Mikeflo", "Melaphyre", "Broady Champs", "Ishues", "Clan Destined", "Lunden Bernard", "Mafioso", "Peppermint Gatty"],
    "september-23-crafts-and-crates.html": ["Jason Staten", "Sir Daniel", "DJ Synthesis", "DJ Dainja", "Peppermint Gatty", "DJ Mafioso"],
    "september-24-crafts-and-crates.html": ["DJ Smiles", "Rasta Root", "Peppermint Gatty", "DJ Mafioso", "DJ Dainja"],
    "september-25-crafts-and-crates.html": ["Rob Wonder", "DJ Sek", "DJ Mafioso", "Peppermint Gatty"],
    "september-26-crafts-and-crates.html": ["Nicolay", "Karl Injex", "Nabani", "Mafisos", "Peppermint Gatty"],
}


def event_performers(html: str, filename: str) -> list[dict]:
    """Read featured performer headings from an event page, when present."""
    if filename in EVENT_PERFORMERS:
        return [{"@type": "Person", "name": name} for name in EVENT_PERFORMERS[filename]]
    section = re.search(
        r"<h2[^>]*>\s*Featured DJ(?:’|'|&rsquo;)s\s*</h2>(.*?)(?=<h2\b|$)",
        html,
        re.S | re.I,
    )
    names = re.findall(r"<h5[^>]*>(.*?)</h5>", section.group(1), re.S | re.I) if section else []
    performers = []
    for raw_name in names:
        name = html_mod.unescape(re.sub(r"<[^>]+>", "", raw_name)).strip()
        if name:
            name = name.title().replace("Dj ", "DJ ").replace("Cj ", "CJ ")
            performers.append({"@type": "Person", "name": name})
    return performers or [{"@type": "Organization", "name": "Crafts & Crates ATL"}]


def event_ld(title: str, desc: str, start: str, image_url: str, url: str, html: str, filename: str) -> dict:
    data = {
        "@type": "Event",
        "name": title,
        "description": desc,
        "startDate": start,
        "endDate": start,
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "eventStatus": "https://schema.org/EventScheduled",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
            "url": url,
        },
        "performer": event_performers(html, filename),
        "location": VENUE,
        "image": [image_url],
        "url": url,
        "organizer": ORGANIZER,
    }
    return data


def breadcrumb_ld(title: str, is_event: bool, filename: str) -> dict:
    items = [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
    ]
    if is_event:
        items.append({"@type": "ListItem", "position": 2, "name": "Events", "item": f"{SITE}/events.html"})
        items.append({"@type": "ListItem", "position": 3, "name": title})
    elif filename not in ("index.html",):
        items.append({"@type": "ListItem", "position": 2, "name": title})
    return {"@type": "BreadcrumbList", "itemListElement": items}


def page_h1(html: str) -> str:
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I)
    if not m:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip()


def enhance_page(path: Path, first_img_basenames: dict={}):
    html = path.read_text(encoding="utf-8")
    if "</head>" not in html:
        return False
    head_txt = html.split("</head>")[0]
    head = parse_head(head_txt)
    rel_path = str(path.relative_to(REPO)).replace("\\", "/")
    if rel_path == "404.html":
        return False

    is_event = rel_path.startswith("events/") and rel_path != "events.html"
    canonical = f"{SITE}/" if rel_path == "index.html" else f"{SITE}/{rel_path}"
    title = html_mod.unescape(head["title"]) or "Crafts & Crates ATL"
    desc = html_mod.unescape(head["desc"]) or "Live hip-hop events in Atlanta's Summerhill."

    # per-page og:image: skip the site header (logo) block, take the first real
    # content image after it; fall back to the default hero photo
    body_from_main = html.split("</header>", 1)[-1]
    m = re.search(r'<img[^>]+src="(?:\.\./)?assets/images/([^"]+)"', body_from_main)
    og_img = m.group(1) if m else OG_IMAGE_DEFAULT.split("/")[-1]
    og_img_url = f"{SITE}/assets/images/{og_img}"

    # Event/Breadcrumb name: the visible H1 (not the title tag, which carries a suffix)
    h1 = page_h1(html) or title

    lines = [
        START_MARK,
        f'  <link rel="canonical" href="{canonical}">',
        '  <meta property="og:site_name" content="Crafts &amp; Crates ATL">',
        f'  <meta property="og:type" content="{"article" if is_event else "website"}">',
        f'  <meta property="og:title" content="{esc_attr(title)}">',
        f'  <meta property="og:description" content="{esc_attr(desc)}">',
        f'  <meta property="og:url" content="{canonical}">',
        f'  <meta property="og:image" content="{og_img_url}">',
        f'  <meta property="og:image:alt" content="{esc_attr(title)}">',
        '  <meta name="twitter:card" content="summary_large_image">',
    ]

    graph = []
    if is_event:
        date_iso = event_date_iso(html)
        if date_iso:
            graph.append(event_ld(h1, desc, date_iso, og_img_url, canonical, html, path.name))
        graph.append(breadcrumb_ld(h1, True, rel_path))
    elif rel_path == "index.html":
        graph.append(org_ld())
        graph.append(homepage_ld())
    else:
        graph.append(breadcrumb_ld(h1, False, rel_path))

    if graph:
        lines.append('  <script type="application/ld+json">')
        lines.append("  " + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False))
        lines.append("  </script>")
    lines.append(END_MARK)
    block = "\n".join(lines) + "\n"

    # strip any previously injected block (idempotency)
    pattern = re.compile(re.escape(START_MARK) + r"[\s\S]*?" + re.escape(END_MARK) + "\n?")
    html = pattern.sub("", html)

    html = html.replace("</head>", block + "</head>", 1)
    path.write_text(html, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# 3+4. sitemap.xml / robots.txt
# ---------------------------------------------------------------------------

def write_sitemap():
    pages = []
    for p in sorted(REPO.rglob("*.html")):
        rel = p.relative_to(REPO).as_posix()
        if rel == "404.html":
            continue
        loc = f"{SITE}/" if rel == "index.html" else f"{SITE}/{rel}"
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        pages.append((loc, mtime))
    body = "\n".join(
        f"  <url><loc>{loc}</loc><lastmod>{mt.strftime('%Y-%m-%dT%H:%M:%SZ')}</lastmod></url>"
        for loc, mt in pages
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n"
    )
    (REPO / "sitemap.xml").write_text(xml, encoding="utf-8")
    return len(pages)


def write_robots():
    robots = f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"
    (REPO / "robots.txt").write_text(robots, encoding="utf-8")


# ---------------------------------------------------------------------------
# 5. .htaccess with WP -> static 301 map
# ---------------------------------------------------------------------------

PAGE_MAP = {
    "blog": "events.html",
    "event-info": "gallery.html",
    "about-crafts-and-crates-hip-hop-event": "about.html",
    "contact": "about.html",
    "faq": "about.html",
    "august-26-crafts-and-crates": "events/august-26-crafts-crates.html",  # slug drift on WP side
}


def build_redirect_map() -> list[tuple[str, str]]:
    rules = []
    for slug, target in PAGE_MAP.items():
        rules.append((slug, target))
    static_slugs = sorted(
        p.stem for p in (REPO / "events").glob("*.html")
        if p.stem not in ("august-26-crafts-crates",)
    )
    for slug in static_slugs:  # all remaining WP slugs match 1:1
        rules.append((slug, f"events/{slug}.html"))
    return rules


def write_htaccess():
    rules = build_redirect_map()
    lines = [
        "# crafts-and-cratesatl.com — static site (WordPress replacement)",
        "Options -Indexes",
        "",
        "<IfModule mod_rewrite.c>",
        "RewriteEngine On",
        "",
        "# Canonical host: force https + apex (matches WP-era canonical form)",
        "RewriteCond %{HTTPS} off [OR]",
        "RewriteCond %{HTTP_HOST} ^www\\. [NC]",
        f"RewriteRule ^ {SITE}%{{REQUEST_URI}} [R=301,L]",
        "",
        "# 301: legacy WordPress URLs -> static structure",
    ]
    for slug, target in rules:
        lines.append(f"RewriteRule ^{re.escape(slug)}/?$ /{target} [R=301,L]")
    lines += [
        "",
        "# Pretty URL niceties (strip .html when the extension was omitted)",
        "RewriteCond %{REQUEST_FILENAME} !-d",
        "RewriteCond %{REQUEST_FILENAME}.html -f",
        "RewriteCond %{THE_REQUEST} \\s/[^? ]*\\.html",
        "RewriteCond %{REQUEST_URI} (.+)\\.html$",
        "RewriteRule ^ %1 [R=301,L]",
        "",
        "RewriteCond %{REQUEST_FILENAME} !-d",
        "RewriteCond %{REQUEST_FILENAME} !-f",
        "RewriteCond %{REQUEST_FILENAME}.html -f",
        "RewriteRule ^([^?]*)$ $1.html [L]",
        "</IfModule>",
        "",
        "ErrorDocument 404 /404.html",
        "",
        "<IfModule mod_expires.c>",
        "ExpiresActive On",
        'ExpiresByType text/html "access plus 1 hour"',
        'ExpiresByType text/css "access plus 1 hour"',
        'ExpiresByType application/javascript "access plus 1 hour"',
        "ExpiresByType image/jpeg \"access plus 1 year\"",
        'ExpiresByType image/png "access plus 1 year"',
        'ExpiresByType image/gif "access plus 1 year"',
        'ExpiresByType image/webp "access plus 1 year"',
        'ExpiresByType image/svg+xml "access plus 1 year"',
        'ExpiresByType font/woff2 "access plus 1 year"',
        'ExpiresByType font/woff "access plus 1 year"',
        "</IfModule>",
        "",
        "<IfModule mod_headers.c>",
        '<FilesMatch "\\.(jpe?g|png|gif|webp|svg|woff2?|ttf)$">',
        'Header set Cache-Control "public, max-age=31536000, immutable"',
        "</FilesMatch>",
        '<FilesMatch "\\.(html|css|js)$">',
        'Header set Cache-Control "public, max-age=3600"',
        "</FilesMatch>",
        "</IfModule>",
        "",
    ]
    (REPO / ".htaccess").write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------

def main():
    touched = 0
    for p in sorted(list(REPO.glob("*.html")) + list((REPO / "events").glob("*.html"))):
        if enhance_page(p, {}):
            touched += 1
    sitemap_n = write_sitemap()
    write_robots()
    write_htaccess()
    print(f"SEO tags injected into {touched} pages")
    print(f"sitemap.xml: {sitemap_n} URLs")
    print("robots.txt written")
    print(f".htaccess written with {len(build_redirect_map())} WP->static 301 rules")


if __name__ == "__main__":
    main()
