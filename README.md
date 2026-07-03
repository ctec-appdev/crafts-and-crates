# Crafts & Crates ATL — Static Site

Static HTML/CSS/JS conversion of the WordPress site [craftsandcratesatl.com](https://craftsandcratesatl.com/),
preserving the original layout, branding (Kadence palette, Staatliches headings), content, and images,
with added scroll-reveal animations, a vanilla-JS carousel, and a full-screen lightbox.

## Structure

```
index.html            Home — hero, photo carousel, map, venue info, Instagram, JB's Record Lounge
about.html            About — story, venue, vinyl pop-up, team (Mike Moore, DJ Dainja, Peppermint Gatty, DJ Mafioso)
events.html           Previous Events — card grid of all 34 event posts, newest first
events/<slug>.html    One page per event post (flyer, date, gallery, prev/next, similar posts)
gallery.html          Full photo gallery (~470 images) with lightbox
404.html              Not-found page
assets/css/style.css  Shared stylesheet (responsive, prefers-reduced-motion aware)
assets/js/main.js     Carousel, lightbox, mobile nav, scroll reveals (no dependencies)
assets/fonts/         Vendored Staatliches webfont
assets/images/        All site images (flat; original filenames, size suffixes stripped)
tools/generate.py     Regenerates events.html, gallery.html, events/*.html from scraped content dumps
tools/check.py        Verifies all internal links and image references resolve
tools/fetch_real_images.py  Replaces placeholder images with the originals (see below)
```

## Placeholder images

The original web host went down partway through the image download, so the files listed in
`tools/placeholder-manifest.txt` are branded placeholder images, not the real photos. When the
host is reachable again, run:

```sh
python3 tools/fetch_real_images.py          # downloads the real images, updates the manifest
python3 tools/fetch_real_images.py --check  # just report reachability + how many remain
```

`tools/image-sources.txt` maps each remaining filename to its original URL (with an automatic
primary/mirror host fallback). The script is idempotent — re-run it until the manifest is empty.

## Development

Serve locally (any static server works):

```sh
python3 -m http.server 8000
```

`tools/generate.py` reads the scraped WordPress content dumps (scratchpad paths are configured at the
top of the script) and rewrites the generated pages. `tools/check.py` reports any broken internal
references. Everything is relative-path based, so the site also works opened directly via `file://`.
