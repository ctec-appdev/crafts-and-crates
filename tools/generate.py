#!/usr/bin/env python3
"""
Generate events.html, gallery.html, and events/<slug>.html for Crafts & Crates ATL.
Run from the repository root:  python3 tools/generate.py
"""

import json
import os
import re
import sys
from datetime import datetime
from html import escape
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parent.parent
SCRATCHPAD = Path("/private/tmp/claude-501/-Users-ctec-Documents-Github-crafts-and-crates/508a7e3f-50c8-4d92-9fe9-7ba68a3b070f/scratchpad")
CONTENT_DIR = SCRATCHPAD / "content"
EVENTS_JSON = SCRATCHPAD / "events.json"
IMAGES_DIR = REPO / "assets" / "images"
OUTPUT_EVENTS_DIR = REPO / "events"

OUTPUT_EVENTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Image URL → local filename
# ---------------------------------------------------------------------------

def url_to_local(url: str) -> str:
    """Strip URL to basename, then strip -WxH and -scaled suffixes."""
    basename = url.split("?")[0].split("/")[-1]
    # Strip -NxN size suffix  e.g. -1024x768
    basename = re.sub(r"-\d+x\d+(\.[a-zA-Z]+)$", r"\1", basename)
    # Strip -scaled suffix
    basename = re.sub(r"-scaled(\.[a-zA-Z]+)$", r"\1", basename)
    # Strip trailing -1 only when it has a known image extension (some WP variants)
    # (leave it — could be legitimate)
    return basename


def img_path_from_root(local_name: str) -> str:
    """Path relative to repo root."""
    return "assets/images/" + local_name


def img_path_from_events(local_name: str) -> str:
    """Path relative to events/ subdirectory."""
    return "../assets/images/" + local_name


def check_img(local_name: str) -> bool:
    """Return True if the image file exists locally."""
    return (IMAGES_DIR / local_name).exists()


# ---------------------------------------------------------------------------
# Content file parser
# ---------------------------------------------------------------------------

def parse_content(path: Path):
    """Parse a content dump into a list of (tag, content) tuples.
    Tags: H1 H2 H3 H4 H5 H6 P PO PA IMG IFRAME
    """
    items = []
    if not path.exists():
        return items
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^\[([A-Z0-9]+)\s*\]\s*(.*)", line)
        if m:
            tag = m.group(1).strip()
            content = m.group(2).strip()
            items.append((tag, content))
        elif line.startswith("TITLE:"):
            items.append(("TITLE", line[6:].strip()))
        elif line.startswith("DATE:"):
            items.append(("DATE", line[5:].strip()))
    return items


def items_before_nav(items):
    """Return items up to (but not including) '[H2] Post navigation'."""
    result = []
    for tag, content in items:
        if tag == "H2" and "post navigation" in content.lower():
            break
        result.append((tag, content))
    return result


def first_img(items):
    """Return local filename of first IMG tag, or None."""
    for tag, content in items:
        if tag == "IMG":
            url = content.split(" (alt:")[0].strip()
            return url_to_local(url)
    return None


def parse_img_tag(content: str):
    """Parse '[IMG] url (alt: text)' content into (url, alt, local_name)."""
    m = re.match(r"(https?://\S+?)(?:\s+\(alt:\s*(.*?)\))?$", content.strip())
    if m:
        url = m.group(1)
        alt = m.group(2) or ""
        return url, alt, url_to_local(url)
    return content, "", url_to_local(content)


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

IG_ICON = """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>"""

EMAIL_ICON = """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>"""

CHEVRON_LEFT = """<svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>"""
CHEVRON_RIGHT = """<svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>"""
ARROW_RIGHT = """<svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>"""


def html_header(title: str, desc: str, depth: int = 0) -> str:
    """depth=0 for root pages, depth=1 for events/ subpages."""
    pre = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="icon" type="image/png" href="{pre}assets/images/cropped-CC_Logo.png">
  <link rel="stylesheet" href="{pre}assets/css/style.css">
</head>
<body>
"""


def site_header(depth: int = 0) -> str:
    pre = "../" * depth
    return f"""<header class="site-header">
  <div class="header-inner">
    <a class="logo" href="{pre}index.html" aria-label="Crafts &amp; Crates ATL &#8211; Home">
      <img src="{pre}assets/images/cropped-CC_Logo.png" alt="Crafts &amp; Crates ATL">
    </a>
    <button class="hamburger" aria-label="Toggle navigation" aria-expanded="false">
      <span></span><span></span><span></span>
    </button>
    <div class="nav-wrapper">
      <nav class="site-nav" aria-label="Main navigation">
        <a href="{pre}index.html">Home</a>
        <a href="{pre}about.html">About</a>
        <a href="{pre}events.html">Events</a>
        <a href="{pre}gallery.html">Gallery</a>
      </nav>
      <div class="nav-social">
        <a href="https://www.instagram.com/craftsandcratesatl/" target="_blank" rel="noopener" aria-label="Instagram">
          {IG_ICON}
        </a>
        <a href="mailto:mikemoore00@gmail.com" aria-label="Email us">
          {EMAIL_ICON}
        </a>
      </div>
    </div>
  </div>
</header>
"""


def site_footer(depth: int = 0) -> str:
    pre = "../" * depth
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <a class="logo" href="{pre}index.html" aria-label="Crafts &amp; Crates ATL &#8211; Home">
        <img src="{pre}assets/images/cropped-CC_Logo.png" alt="Crafts &amp; Crates ATL" style="height:44px;">
      </a>
      <nav class="footer-links" aria-label="Footer navigation">
        <a href="{pre}events.html">Previous Events</a>
        <a href="{pre}gallery.html">Gallery</a>
      </nav>
      <div class="footer-social">
        <a href="https://www.instagram.com/craftsandcratesatl/" target="_blank" rel="noopener" aria-label="Instagram">
          {IG_ICON}
        </a>
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; 2026 Crafts &amp; Crates ATL. Website by CTEC Web Design.</p>
    </div>
  </div>
</footer>
"""


def html_footer(depth: int = 0) -> str:
    pre = "../" * depth
    return f"""<script src="{pre}assets/js/main.js"></script>
</body>
</html>
"""


def format_date(date_str: str) -> str:
    """Format ISO date string to readable format."""
    try:
        d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return d.strftime("%B %d, %Y")
    except Exception:
        return date_str


def event_card_html(evt: dict, depth: int = 0, warn: list = None) -> str:
    """Render a single event card."""
    pre = "../" * depth
    slug = evt["slug"]
    title = evt["title"]
    date_fmt = format_date(evt["date"])
    href = f"{pre}events/{slug}.html"

    flyer = evt.get("flyer")
    if flyer:
        local = flyer
        if check_img(local):
            img_src = f"{pre}assets/images/{local}"
        else:
            # Try stripping WxH from flyer name (shouldn't need it, but just in case)
            local2 = url_to_local(local)
            if check_img(local2):
                img_src = f"{pre}assets/images/{local2}"
            else:
                if warn is not None:
                    warn.append(f"MISSING flyer: {local}")
                img_src = f"{pre}assets/images/{local}"
    else:
        # Fall back: try to grab first IMG from slug content
        post_items = parse_content(CONTENT_DIR / f"{slug}.txt")
        fn = first_img(post_items)
        if fn and check_img(fn):
            img_src = f"{pre}assets/images/{fn}"
        elif fn:
            if warn is not None:
                warn.append(f"MISSING fallback img for {slug}: {fn}")
            img_src = f"{pre}assets/images/{fn}"
        else:
            img_src = ""

    img_html = ""
    title_esc = escape(title)
    if img_src:
        img_html = f'<img src="{img_src}" alt="{title_esc}" loading="lazy">'

    return f"""<article class="event-card reveal">
  <a href="{href}" class="event-card-img">{img_html}</a>
  <div class="event-card-body">
    <p class="event-card-date">{date_fmt}</p>
    <h3 class="event-card-title"><a href="{href}">{title_esc}</a></h3>
    <a href="{href}" class="event-card-link">View Event {ARROW_RIGHT}</a>
  </div>
</article>
"""


# ---------------------------------------------------------------------------
# Generate events.html
# ---------------------------------------------------------------------------

def generate_events(events: list, warnings: list):
    html = html_header(
        "Previous Events – Crafts &amp; Crates ATL",
        "Browse all previous Crafts &amp; Crates ATL hip-hop events at Halfway Crooks Biergarten in Summerhill, Atlanta.",
        depth=0
    )
    html += site_header(0)
    html += """
<main>
  <section class="section">
    <div class="container">
      <p class="section-kicker">Archive</p>
      <h1 class="events-header reveal">Previous Events</h1>
      <div class="divider"></div>
      <div class="cards-grid stagger">
"""
    for evt in events:
        html += event_card_html(evt, depth=0, warn=warnings)
    html += """      </div>
    </div>
  </section>
</main>
"""
    html += site_footer(0)
    html += html_footer(0)

    out = REPO / "events.html"
    out.write_text(html, encoding="utf-8")
    print(f"  Wrote {out.relative_to(REPO)}")


# ---------------------------------------------------------------------------
# Build post body HTML from parsed items (depth=1, events/ subpage)
# ---------------------------------------------------------------------------

def build_post_body(items, flyer_local: str, warnings: list) -> str:
    """Convert parsed items (after the [H1] title line, before nav) to HTML.
    Collects consecutive IMG lines into a gallery grid.
    Returns inner HTML for the post body."""
    chunks = []
    img_buffer = []

    def flush_imgs():
        nonlocal img_buffer
        if not img_buffer:
            return
        if len(img_buffer) == 1:
            url, alt, local = img_buffer[0]
            # Skip if this is the flyer (already shown)
            if local == flyer_local:
                img_buffer = []
                return
            if not check_img(local):
                warnings.append(f"  MISSING: {local}")
            src = img_path_from_events(local)
            chunks.append(f'<div class="post-img"><img src="{src}" alt="{escape(alt)}" loading="lazy" class="img-rounded"></div>')
        else:
            # Filter out flyer from gallery
            imgs = [(u, a, l) for u, a, l in img_buffer if l != flyer_local]
            if not imgs:
                img_buffer = []
                return
            if len(imgs) == 1:
                url, alt, local = imgs[0]
                if not check_img(local):
                    warnings.append(f"  MISSING: {local}")
                src = img_path_from_events(local)
                chunks.append(f'<div class="post-img"><img src="{src}" alt="{alt}" loading="lazy" class="img-rounded"></div>')
            else:
                grid_html = '<div class="post-gallery">\n'
                for url, alt, local in imgs:
                    if not check_img(local):
                        warnings.append(f"  MISSING: {local}")
                    src = img_path_from_events(local)
                    grid_html += f'  <div class="gallery-item"><img src="{src}" alt="{escape(alt)}" loading="lazy"></div>\n'
                grid_html += '</div>\n'
                chunks.append(grid_html)
        img_buffer = []

    # Skip first item if it's a duplicate of the H1 (already shown in header)
    skip_first_h1 = True

    for tag, content in items:
        if tag in ("TITLE", "DATE", "PA"):
            continue
        if tag == "H1" and skip_first_h1:
            skip_first_h1 = False
            continue
        if tag == "IMG":
            url, alt, local = parse_img_tag(content)
            img_buffer.append((url, alt, local))
        else:
            flush_imgs()
            if tag in ("H2", "H3", "H4", "H5", "H6"):
                level = int(tag[1])
                chunks.append(f"<h{level}>{escape(content)}</h{level}>")
            elif tag in ("P", "PO"):
                chunks.append(f"<p>{escape(content)}</p>")
            elif tag == "IFRAME":
                chunks.append(f"""<div class="map-wrap"><iframe src="{content}" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Map"></iframe></div>""")

    flush_imgs()
    return "\n".join(chunks)


# ---------------------------------------------------------------------------
# Generate individual event pages
# ---------------------------------------------------------------------------

def generate_post(evt: dict, idx: int, events: list, warnings: list):
    slug = evt["slug"]
    title = evt["title"]
    date_fmt = format_date(evt["date"])
    n = len(events)

    # Determine prev/next (events.json is newest-first, so idx+1 is older/prev)
    prev_evt = events[idx + 1] if idx + 1 < n else None
    next_evt = events[idx - 1] if idx - 1 >= 0 else None

    # Parse content
    items = parse_content(CONTENT_DIR / f"{slug}.txt")
    body_items = items_before_nav(items)

    # Determine flyer
    flyer_local = evt.get("flyer") or ""
    if flyer_local and not check_img(flyer_local):
        # Try WxH-stripped version
        stripped = url_to_local(flyer_local)
        if check_img(stripped):
            flyer_local = stripped
        else:
            warnings.append(f"  MISSING flyer ({slug}): {flyer_local}")
    if not flyer_local:
        # Fall back to first IMG in content
        fn = first_img(body_items)
        if fn:
            flyer_local = fn

    # If flyer missing still, take from content
    if not flyer_local:
        fn = first_img(items)
        if fn:
            flyer_local = fn
            if not check_img(fn):
                warnings.append(f"  MISSING fallback ({slug}): {fn}")

    # Similar posts: pick 3 others, prefer adjacent
    similar_indices = []
    candidates = [i for i in range(n) if i != idx]
    # Pick 1 before and 1 after in terms of date (adjacent in list)
    if idx + 1 < n:
        similar_indices.append(idx + 1)
        candidates.remove(idx + 1)
    if idx - 1 >= 0:
        similar_indices.append(idx - 1)
        if idx - 1 in candidates:
            candidates.remove(idx - 1)
    # Fill to 3 from remaining
    import random
    random.seed(slug)  # deterministic per slug
    random.shuffle(candidates)
    while len(similar_indices) < 3 and candidates:
        similar_indices.append(candidates.pop(0))
    similar_events = [events[i] for i in similar_indices[:3]]

    # Build page
    title_esc = escape(title)
    html = html_header(
        f"{title_esc} – Crafts &amp; Crates ATL",
        f"{title_esc} at Halfway Crooks Biergarten — Crafts &amp; Crates ATL hip-hop event.",
        depth=1
    )
    html += site_header(1)

    # Post hero
    html += f"""
<main>
  <section class="post-hero">
    <div class="container">
      <span class="post-category">Previous Events</span>
      <h1>{title_esc}</h1>
      <p class="post-date">{date_fmt}</p>
    </div>
  </section>

  <section class="section">
    <div class="container post-body">
"""

    # Flyer image (prominent)
    if flyer_local:
        fsrc = img_path_from_events(flyer_local)
        if not check_img(flyer_local):
            warnings.append(f"  MISSING flyer display ({slug}): {flyer_local}")
        html += f"""      <div class="post-flyer reveal">
        <img src="{fsrc}" alt="{title_esc}">
      </div>
"""

    # Post body content
    body_html = build_post_body(body_items, flyer_local, warnings)
    if body_html.strip():
        html += f"      <div class=\"reveal\">\n{body_html}\n      </div>\n"

    # Prev/next navigation
    html += '      <nav class="post-nav" aria-label="Post navigation">\n'
    if prev_evt:
        html += f"""        <div class="post-nav-item">
          <span class="post-nav-label">&#8592; Previous</span>
          <a class="post-nav-title" href="{prev_evt['slug']}.html">{escape(prev_evt['title'])}</a>
        </div>
"""
    else:
        html += '        <div class="post-nav-item"></div>\n'

    if next_evt:
        html += f"""        <div class="post-nav-item post-nav-item--next">
          <span class="post-nav-label">Next &#8594;</span>
          <a class="post-nav-title" href="{next_evt['slug']}.html">{escape(next_evt['title'])}</a>
        </div>
"""
    else:
        html += '        <div class="post-nav-item post-nav-item--next"></div>\n'
    html += '      </nav>\n'

    # Similar posts
    if similar_events:
        html += """      <section class="section" style="padding: 0 0 40px;">
        <p class="section-kicker">More Events</p>
        <h2 class="reveal" style="margin-bottom: 24px;">Similar Posts</h2>
        <div class="cards-grid stagger">
"""
        for se in similar_events:
            html += event_card_html(se, depth=1, warn=warnings)
        html += "        </div>\n      </section>\n"

    html += "    </div>\n  </section>\n</main>\n"
    html += site_footer(1)
    html += html_footer(1)

    out = OUTPUT_EVENTS_DIR / f"{slug}.html"
    out.write_text(html, encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# Generate gallery.html
# ---------------------------------------------------------------------------

def generate_gallery(warnings: list):
    items = parse_content(CONTENT_DIR / "event-info.txt")

    seen = set()
    imgs = []
    for tag, content in items:
        if tag != "IMG":
            continue
        url, alt, local = parse_img_tag(content)
        if local in seen:
            continue
        seen.add(local)
        if not check_img(local):
            warnings.append(f"  MISSING gallery: {local}")
        imgs.append((local, alt))

    html = html_header(
        "Gallery – Crafts &amp; Crates ATL",
        "Photo gallery from Crafts &amp; Crates ATL hip-hop events at Halfway Crooks Biergarten in Summerhill.",
        depth=0
    )
    html += site_header(0)
    html += f"""
<main>
  <section class="section">
    <div class="container">
      <p class="section-kicker">Photos</p>
      <h1 class="reveal">Gallery</h1>
      <div class="divider"></div>
      <p class="section-intro reveal">{len(imgs)} photos from Crafts &amp; Crates ATL events.</p>
      <div class="gallery-grid">
"""
    for local, alt in imgs:
        src = img_path_from_root(local)
        alt_safe = escape(alt) if alt else "Crafts &amp; Crates ATL event photo"
        html += f'        <div class="gallery-item"><img src="{src}" alt="{alt_safe}" loading="lazy"></div>\n'

    html += """      </div>
    </div>
  </section>
</main>
"""
    html += site_footer(0)
    html += html_footer(0)

    out = REPO / "gallery.html"
    out.write_text(html, encoding="utf-8")
    print(f"  Wrote {out.relative_to(REPO)}")
    return len(imgs)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not EVENTS_JSON.exists():
        print(f"ERROR: events.json not found at {EVENTS_JSON}", file=sys.stderr)
        sys.exit(1)

    events = json.loads(EVENTS_JSON.read_text(encoding="utf-8"))
    warnings = []

    print(f"Generating {len(events)} event pages...")
    for idx, evt in enumerate(events):
        out = generate_post(evt, idx, events, warnings)
        print(f"  [{idx+1:02d}/{len(events)}] {out.relative_to(REPO)}")

    print("\nGenerating events.html...")
    generate_events(events, warnings)

    print("\nGenerating gallery.html...")
    count = generate_gallery(warnings)
    print(f"  Gallery: {count} unique images")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)} missing images — re-run after downloads complete):")
        for w in sorted(set(warnings)):
            print(f"  {w}")
    else:
        print("\nAll images present. No warnings.")

    print("\nDone.")


if __name__ == "__main__":
    main()
