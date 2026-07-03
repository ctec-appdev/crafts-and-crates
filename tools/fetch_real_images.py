#!/usr/bin/env python3
"""Replace placeholder images with the real ones from the original site.

Reads tools/image-sources.txt (tab-separated: <url> <local filename>) and
tools/placeholder-manifest.txt, downloads every file that is still a
placeholder, and removes it from the manifest once the real image is saved.
Safe to re-run any number of times; it only fetches what is still missing.

Usage: python3 tools/fetch_real_images.py [--check]
  --check   only report whether the source server is reachable and how many
            placeholders remain, without downloading.
"""
import os
import sys
import time
import urllib.request

TOOLS = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.join(TOOLS, os.pardir, "assets", "images")
SOURCES = os.path.join(TOOLS, "image-sources.txt")
MANIFEST = os.path.join(TOOLS, "placeholder-manifest.txt")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PRIMARY = "https://craftsandcratesatl.com/"
MIRROR = "https://ctecreative.com/craftsandcratesatl/"


def candidate_urls(url):
    if url.startswith(MIRROR):
        return [url, url.replace(MIRROR, PRIMARY)]
    return [url, url.replace(PRIMARY, MIRROR)]


def fetch(url, path, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tmp = path + ".part"
    with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(65536)
            if not chunk:
                break
            f.write(chunk)
    if os.path.getsize(tmp) < 1024:
        os.remove(tmp)
        raise IOError("suspiciously small response")
    os.replace(tmp, path)


def load_manifest():
    with open(MANIFEST) as f:
        return [line.strip() for line in f if line.strip()]


def server_up():
    try:
        req = urllib.request.Request(PRIMARY, headers={"User-Agent": UA})
        urllib.request.urlopen(req, timeout=15)
        return True
    except Exception:
        return False


def main():
    remaining = set(load_manifest())
    print(f"{len(remaining)} placeholder(s) still to replace.")
    if "--check" in sys.argv:
        print("server reachable:", server_up())
        return

    sources = {}
    with open(SOURCES) as f:
        for line in f:
            if "\t" in line:
                url, name = line.rstrip("\n").split("\t", 1)
                sources[name] = url

    ok = fail = 0
    for name in sorted(remaining):
        url = sources.get(name)
        if not url:
            print(f"  no source URL for {name}, skipping")
            continue
        dest = os.path.join(IMAGES, name)
        done = False
        for cand in candidate_urls(url):
            try:
                fetch(cand, dest)
                done = True
                break
            except Exception as e:
                last_err = e
        if done:
            ok += 1
            remaining.discard(name)
            if ok % 25 == 0:
                print(f"  {ok} downloaded...")
        else:
            fail += 1
            print(f"  FAILED {name}: {last_err}")
        time.sleep(0.4)  # stay polite; earlier bulk runs coincided with the host going down

    with open(MANIFEST, "w") as f:
        f.write("\n".join(sorted(remaining)) + ("\n" if remaining else ""))
    print(f"done: {ok} replaced, {fail} failed, {len(remaining)} placeholder(s) left.")


if __name__ == "__main__":
    main()
