"""Fetch a random 5-minute guided meditation from YouTube.

Strategy:
  1. Scrape YouTube search results for "5 minute guided meditation"
     -> get up to ~20 candidate video IDs.
  2. For each candidate, call YouTube oEmbed:
       - HTTP 200 = video exists AND allows embedding (good)
       - HTTP 401 = embedding disabled by uploader (skip)
       - HTTP 404 = removed / private (skip)
  3. Return the first embeddable hit (with its real title).
  4. If nothing in the search is embeddable, fall back to a curated
     list of videos verified to allow embedding.
"""

import urllib.request
import urllib.error
import urllib.parse
import re
import random
import json
import sys
import time


# Verified-embeddable curated fallbacks.
VERIFIED_FALLBACKS = [
    {"id": "inpok4MKVLM", "title": "5-Minute Meditation You Can Do Anywhere | Goodful"},
    {"id": "MR57rug8NsM", "title": "5 Minute Quick Anxiety Reduction - Guided Mindfulness Meditation"},
    {"id": "ssss7V1_eyA", "title": "5 Minute Mindfulness Meditation | Great Meditation"},
    {"id": "z6X5oEIg6Ak", "title": "10-Minute Meditation For Stress | Goodful"},
    {"id": "O-6f5wQXSu8", "title": "10-Minute Meditation For Anxiety | Goodful"},
]

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def oembed_info(vid, timeout=4):
    """Return (embeddable: bool, title: str|None) for a YouTube video id."""
    url = (
        "https://www.youtube.com/oembed?url="
        + urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}", safe="")
        + "&format=json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                return False, None
            data = json.loads(r.read().decode("utf-8"))
            return True, data.get("title")
    except urllib.error.HTTPError:
        # 401 (not embeddable) or 404 (missing) — both = skip.
        return False, None
    except Exception:
        return False, None


def search_candidates():
    """Scrape the YouTube search results page for candidate video IDs."""
    search_url = "https://www.youtube.com/results?search_query=5+minute+guided+meditation"
    req = urllib.request.Request(search_url, headers={"User-Agent": UA})
    html = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", errors="ignore")
    ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
    # Dedupe while preserving order
    seen = set()
    unique = []
    for vid in ids:
        if vid not in seen:
            seen.add(vid)
            unique.append(vid)
    return unique[:20]


def fetch_meditation():
    """Pick a fresh embeddable meditation, with curated fallback."""
    chosen_id = None
    chosen_title = None
    source = "search"

    try:
        candidates = search_candidates()
        # Try them in shuffled order so we don't always pick the first one.
        random.shuffle(candidates)
        for vid in candidates:
            ok, title = oembed_info(vid)
            if ok:
                chosen_id = vid
                chosen_title = title or "5 Minute Guided Meditation"
                break
    except Exception:
        pass

    if not chosen_id:
        # Fall back to a verified curated list. Shuffle for variety.
        source = "fallback"
        pool = VERIFIED_FALLBACKS[:]
        random.shuffle(pool)
        for entry in pool:
            ok, title = oembed_info(entry["id"])
            if ok:
                chosen_id = entry["id"]
                chosen_title = title or entry["title"]
                break

    if not chosen_id:
        # Last-resort hard default (Goodful — known stable).
        source = "hard_default"
        chosen_id = VERIFIED_FALLBACKS[0]["id"]
        chosen_title = VERIFIED_FALLBACKS[0]["title"]

    print(json.dumps({
        "status": "success",
        "id": chosen_id,
        "title": chosen_title,
        "url": f"https://www.youtube.com/watch?v={chosen_id}",
        "source": source,
        "ts": int(time.time()),
    }, ensure_ascii=False))


if __name__ == "__main__":
    fetch_meditation()
