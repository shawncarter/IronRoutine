#!/usr/bin/env python3
import argparse
import sys
import re
import os
import csv
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

try:
    import yt_dlp as ytdlp
except Exception as e:
    print("yt-dlp is required. Please install dependencies: pip install -r requirements.txt", file=sys.stderr)
    raise


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape exercise listing page and download videos.")
    parser.add_argument("listing_url", help="Full URL to the listing/table page containing exercise rows")
    parser.add_argument("--origin", help="Site origin to prefix relative hrefs (e.g., https://example.com). If omitted, derived from listing_url.")
    parser.add_argument("--output-dir", default="downloads", help="Directory to save videos (default: downloads)")
    parser.add_argument("--gender", choices=["male", "female", "both"], default="both", help="Filter by gender link (default: both)")
    parser.add_argument("--limit", type=int, default=None, help="Download at most N videos (for testing)")
    parser.add_argument("--rate-limit", default=None, help="Max download rate, e.g. 2M or 500K (passed to yt-dlp)")
    parser.add_argument("--cookies", default=None, help="Path to cookies.txt (Netscape format) to pass to yt-dlp")
    parser.add_argument("--cookies-from-browser", default=None, help="Load cookies from a browser profile, e.g. 'chrome' or 'firefox' (passed to yt-dlp)")
    parser.add_argument("--dry-run", action="store_true", help="Only list the videos that would be downloaded")
    parser.add_argument("--format", default="bv*+ba/b", help="yt-dlp format selector (default: best video+audio)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip downloads if file already exists")
    # New input methods
    parser.add_argument("--html-file", default=None, help="Read listing HTML from a local file instead of fetching listing_url")
    parser.add_argument("--stdin-html", action="store_true", help="Read listing HTML from STDIN (paste the table HTML)")
    # Download method
    parser.add_argument("--method", choices=["yt-dlp", "direct-mp4", "guess-mp4", "auto"], default="yt-dlp", help="Use yt-dlp (default), resolve .mp4 URLs from pages, guess predictable media URLs, or auto (guess then parse)")
    # Guessing controls
    parser.add_argument("--guess-media-origin", default="https://media.musclewiki.com", help="Base origin for guessed media URLs (default: https://media.musclewiki.com)")
    parser.add_argument("--angles", default="front,side", help="Comma-separated list of angles to try for guessed URLs (default: front,side)")
    parser.add_argument("--middle-tokens", default="bench,incline,decline,flat,standing,seated", help="Comma-separated optional tokens to insert between equipment and slug (e.g., bench)")
    parser.add_argument("--log-dir", default=None, help="Directory to write successes.csv and failures.csv logs (not used in --dry-run)")
    parser.add_argument("--max-workers", type=int, default=10, help="Max concurrent workers for URL existence checks (default: 10)")
    return parser.parse_args()


def fetch_listing(url: str) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def read_listing_html(args) -> str:
    """Return HTML for the listing. Priority: --stdin-html > --html-file > fetch listing_url."""
    if args.stdin_html:
        data = sys.stdin.read()
        if not data.strip():
            raise ValueError("--stdin-html specified but no data was provided on STDIN")
        return data
    if args.html_file:
        with open(args.html_file, "r", encoding="utf-8") as f:
            return f.read()
    return fetch_listing(args.listing_url)


def sanitize_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", " ", name)
    return name


def extract_entries(html: str, origin: str, gender_filter: str):
    soup = BeautifulSoup(html, "html.parser")
    tbody = soup.find("tbody")
    if not tbody:
        # fallback to entire doc
        tbody = soup

    entries = []
    rows = tbody.find_all("tr")
    current_section = None

    for tr in rows:
        # Section headers are <th colspan="4">..
        th = tr.find("th")
        if th and th.get("colspan"):
            sec = th.get_text(strip=True)
            if sec:
                current_section = sec
            continue

        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        # First column has exercise name link
        exercise_link = tds[0].find("a")
        exercise_name = exercise_link.get_text(strip=True) if exercise_link else tds[0].get_text(strip=True)
        exercise_name = sanitize_filename(exercise_name)
        # Derive equipment and slug from href path when available
        equipment = None
        slug = None
        if exercise_link and exercise_link.get("href"):
            try:
                href_path = exercise_link.get("href")
                # Example: /dumbbells/male/biceps/dumbbell-curl
                parts = href_path.strip("/").split("/")
                if len(parts) >= 4:
                    equipment = parts[0]
                    slug = parts[-1]
            except Exception:
                pass

        # Second column contains Male/Female links
        gender_cell = tds[1]
        gender_links = gender_cell.find_all("a")

        for a in gender_links:
            label = a.get_text(strip=True).lower()
            if label not in ("male", "female"):
                continue
            if gender_filter != "both" and label != gender_filter:
                continue

            href = a.get("href")
            if not href:
                continue
            full_url = urljoin(origin, href)

            # Build a filename-friendly title
            title_parts = []
            if current_section:
                title_parts.append(current_section)
            title_parts.append(exercise_name)
            title_parts.append(label.capitalize())
            title = " - ".join(title_parts)

            entries.append({
                "title": title,
                "gender": label,
                "url": full_url,
                "equipment": equipment,
                "slug": slug,
            })

    # Deduplicate by url
    seen = set()
    unique = []
    for e in entries:
        if e["url"] in seen:
            continue
        seen.add(e["url"])
        unique.append(e)

    return unique


def build_ytdlp_opts(args, entry_title: str):
    outtmpl = f"{args.output_dir}/%(title)s.%(ext)s"

    # We’ll override %(title)s with our own title via 'postprocessor_args' filename? Easier: use 'outtmpl' with sanitized custom title
    safe_title = sanitize_filename(entry_title)
    outtmpl = f"{args.output_dir}/{safe_title}.%(ext)s"

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": args.format,
        "noplaylist": True,
        "quiet": False,
        "merge_output_format": "mp4",
        "continuedl": True,
        "ratelimit": args.rate_limit,
        "retries": 5,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": 5,
        "ignoreerrors": True,
        "nooverwrites": args.skip_existing,
    }
    if args.cookies:
        ydl_opts["cookiefile"] = args.cookies
    if args.cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (args.cookies_from_browser, )
    return ydl_opts


UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def find_mp4_in_page(page_url: str) -> str | None:
    """Fetch a page and attempt to find a direct .mp4 URL.
    Strategies:
    - <video> or <source> tags with src ending in .mp4
    - <a href> links ending in .mp4
    Returns the first found .mp4 URL or None.
    """
    try:
        r = requests.get(page_url, timeout=30, headers=UA_HEADERS, allow_redirects=True)
        r.raise_for_status()
    except Exception:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    # Look for <video src> directly
    for v in soup.find_all("video"):
        src = v.get("src") or v.get("data-src")
        if src and src.lower().split("?")[0].endswith(".mp4"):
            return urljoin(page_url, src)
        # Look at child <source> tags
        for source in v.find_all("source"):
            s = source.get("src") or source.get("data-src")
            if s and s.lower().split("?")[0].endswith(".mp4"):
                return urljoin(page_url, s)
    # Look for simple <a href="...mp4">
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and href.lower().split("?")[0].endswith(".mp4"):
            return urljoin(page_url, href)
    return None


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _append_csv(path: str, headers: list[str], row: dict):
    ensure_dir(os.path.dirname(path))
    file_exists = os.path.exists(path)
    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in headers})


def log_success(args, row: dict):
    if not getattr(args, "log_dir", None):
        return
    path = os.path.join(args.log_dir, "successes.csv")
    headers = [
        "title",
        "page_url",
        "method",
        "angle",
        "final_url",
        "filename",
        "equipment",
        "slug",
    ]
    _append_csv(path, headers, row)


def log_failure(args, row: dict):
    if not getattr(args, "log_dir", None):
        return
    path = os.path.join(args.log_dir, "failures.csv")
    headers = [
        "title",
        "page_url",
        "method",
        "angle",
        "reason",
        "equipment",
        "slug",
    ]
    _append_csv(path, headers, row)


def check_all_angles_exist(output_dir: str, title_safe: str, angles: list[str]) -> bool:
    """Check if all expected angle videos already exist locally."""
    for angle in angles:
        path = os.path.join(output_dir, f"{title_safe}-{angle}.mp4")
        if not os.path.exists(path):
            return False
    return True


def download_mp4(mp4_url: str, dest_path: str, skip_existing: bool = False) -> bool:
    """Download a direct .mp4 URL to dest_path. Returns True on success."""
    ensure_dir(os.path.dirname(dest_path))
    if skip_existing and os.path.exists(dest_path):
        return True
    try:
        with requests.get(mp4_url, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length", 0))
            with open(dest_path, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=os.path.basename(dest_path)) as pbar:
                for chunk in resp.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        return True
    except Exception as ex:
        print(f"Direct download failed: {mp4_url} -> {dest_path} : {ex}", file=sys.stderr)
        return False


def _variants_equipment(equipment: str | None) -> list[str]:
    if not equipment:
        return []
    base = equipment.strip("/")
    candidates = set()
    
    # Original
    candidates.add(base)
    
    # Singular: remove trailing 's'
    if base.endswith("s"):
        candidates.add(base[:-1])
    
    # Title case (first letter capitalized)
    candidates.add(base.capitalize())
    if base.endswith("s"):
        candidates.add(base[:-1].capitalize())
    
    # Full title case for compound words (e.g., "kettlebells" → "Kettlebells")
    candidates.add(base.title())
    
    # Remove hyphens and capitalize (e.g., "smith-machine" → "Smithmachine")
    no_hyphen = base.replace("-", "")
    candidates.add(no_hyphen)
    candidates.add(no_hyphen.capitalize())
    candidates.add(no_hyphen.title())
    
    # Remove hyphens from singular form too
    if base.endswith("s"):
        no_hyphen_singular = base[:-1].replace("-", "")
        candidates.add(no_hyphen_singular)
        candidates.add(no_hyphen_singular.capitalize())
        candidates.add(no_hyphen_singular.title())
    
    return list(candidates)


def guess_mp4_candidates(media_origin: str, gender: str, equipment: str | None, slug: str | None, angles: list[str], middle_tokens: list[str] | None = None) -> list[str]:
    """Build candidate URLs like:
    {media_origin}/media/uploads/videos/branded/{gender}-{Equipment}-{slug}-{angle}.mp4
    Try variants of Equipment casing/singular/plural and slug variations.
    """
    if not slug:
        return []
    media_origin = media_origin.rstrip("/")
    
    # Generate slug variants
    slug_variants = [slug]
    
    # Remove "variation-" prefix if present (e.g., "stretch-variation-1" → "stretch-1")
    if "variation" in slug:
        slug_variants.append(slug.replace("-variation", ""))
    
    # Convert word numbers to digits (e.g., "variation-five" → "variation-5")
    number_words = {
        "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
        "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"
    }
    for word, digit in number_words.items():
        if word in slug:
            slug_variants.append(slug.replace(word, digit))
            # Also try with variation removed
            if "variation" in slug:
                slug_variants.append(slug.replace(word, digit).replace("-variation", ""))
    
    # Word substitutions for known variations/typos
    word_substitutions = {
        "supinating": "rotating",
        "row-bar": "v-bar",
        "corpe": "corpse",  # typo in the site
    }
    for old_word, new_word in word_substitutions.items():
        if old_word in slug:
            slug_variants.append(slug.replace(old_word, new_word))
    
    # Remove equipment name from slug if it's a prefix (e.g., "kettlebell-alternating-row" → "alternating-row")
    if equipment:
        eq_lower = equipment.lower()
        slug_lower = slug.lower()
        # Try removing equipment as prefix
        for eq_prefix in [eq_lower, eq_lower.rstrip('s'), eq_lower.replace('-', '')]:
            if slug_lower.startswith(eq_prefix + '-'):
                simplified = slug[len(eq_prefix)+1:]  # +1 for the hyphen
                slug_variants.append(simplified)
    
    # Remove common prefixes/modifiers (e.g., "single-arm-bayesian-curl" → "bayesian-curl")
    common_prefixes = ["single-arm-", "double-", "alternating-", "single-leg-", "dual-"]
    for prefix in common_prefixes:
        if prefix in slug:
            simplified = slug.replace(prefix, "")
            if simplified not in slug_variants:
                slug_variants.append(simplified)
            # Also try with equipment prefix removed
            if equipment:
                eq_lower = equipment.lower()
                for eq_prefix in [eq_lower, eq_lower.rstrip('s')]:
                    if simplified.startswith(eq_prefix + '-'):
                        double_simplified = simplified[len(eq_prefix)+1:]
                        if double_simplified not in slug_variants:
                            slug_variants.append(double_simplified)
    
    # Remove hyphens and 's' for compact forms (e.g., "chin-ups" → "chinup")
    slug_no_hyphen = slug.replace("-", "")
    if slug_no_hyphen not in slug_variants:
        slug_variants.append(slug_no_hyphen)
    
    # Remove 's' from end (e.g., "chin-ups" → "chin-up", "chinups" → "chinup")
    if slug.endswith("s"):
        slug_singular = slug[:-1]
        slug_variants.append(slug_singular)
        slug_singular_no_hyphen = slug_singular.replace("-", "")
        if slug_singular_no_hyphen not in slug_variants:
            slug_variants.append(slug_singular_no_hyphen)
    
    # Always include a no-equipment variant even if equipment is present,
    # since some media files omit the equipment token (e.g., male-{slug}-{angle}.mp4)
    eq_variants = [""]
    eq_variants += _variants_equipment(equipment)
    
    urls: list[str] = []
    mids = [""]
    if middle_tokens:
        mids += [m.strip() for m in middle_tokens if m.strip()]
    
    for slug_var in slug_variants:
        for eq in eq_variants:
            # If no equipment, omit the hyphen slot
            eq_part = f"-{eq}" if eq else ""
            for mid in mids:
                mid_part = f"-{mid}" if mid else ""
                for angle in angles:
                    # Standard pattern: gender-equipment-slug-angle
                    urls.append(f"{media_origin}/media/uploads/videos/branded/{gender}{eq_part}{mid_part}-{slug_var}-{angle}.mp4")
    
    return urls


def _check_url_exists(url: str) -> tuple[str | None, int]:
    """Check if a URL exists. Returns (url, priority) where priority is the index in the original list.
    Returns (None, priority) if URL doesn't exist."""
    try:
        # HEAD first for efficiency; some servers may not allow HEAD, fallback to GET
        r = requests.head(url, timeout=5, allow_redirects=True, headers=UA_HEADERS)
        if r.ok and int(r.headers.get("Content-Length", "0")) >= 1:
            return (url, 0)
        # fallback GET small
        r = requests.get(url, stream=True, timeout=5, headers=UA_HEADERS)
        if r.ok:
            return (url, 0)
    except Exception:
        pass
    return (None, 0)


def first_existing_url(candidates: list[str], max_workers: int = 10) -> str | None:
    """Check multiple URLs concurrently and return the first one that exists.
    Maintains order preference: returns the first candidate in the list that exists."""
    if not candidates:
        return None
    
    # Use a dict to track which URLs exist and their original position
    url_to_index = {url: i for i, url in enumerate(candidates)}
    found_urls = []
    
    # Check all URLs concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(_check_url_exists, url): url for url in candidates}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result_url, _ = future.result()
                if result_url:
                    found_urls.append((result_url, url_to_index[result_url]))
            except Exception:
                continue
    
    # Return the first URL in original order that was found
    if found_urls:
        found_urls.sort(key=lambda x: x[1])  # Sort by original index
        return found_urls[0][0]
    
    return None


def main():
    args = parse_args()

    # Determine origin
    if args.origin:
        origin = args.origin.rstrip("/") + "/"
    else:
        parsed = urlparse(args.listing_url)
        origin = f"{parsed.scheme}://{parsed.netloc}/"

    html = read_listing_html(args)
    entries = extract_entries(html, origin, args.gender)

    if args.limit:
        entries = entries[: args.limit]

    if not entries:
        print("No video page links found. If the page renders via JavaScript, consider providing a static HTML export or use --cookies/--cookies-from-browser.")
        return 1

    print(f"Discovered {len(entries)} video page links")

    if args.dry_run:
        if args.method == "direct-mp4":
            for e in entries:
                resolved = e["url"] if e["url"].lower().endswith(".mp4") else (find_mp4_in_page(e["url"]) or "<no mp4 found>")
                print(f"- {e['title']}\n  page: {e['url']}\n  mp4:  {resolved}")
        elif args.method == "guess-mp4":
            angles = [a.strip() for a in (args.angles.split(",") if args.angles else []) if a.strip()]
            media_origin = args.guess_media_origin
            middle_tokens = [m.strip() for m in (args.middle_tokens.split(",") if args.middle_tokens else []) if m.strip()]
            for e in entries:
                print(f"- {e['title']}")
                for angle in angles:
                    candidates = guess_mp4_candidates(media_origin, e["gender"], e.get("equipment"), e.get("slug"), [angle], middle_tokens)
                    chosen = first_existing_url(candidates, max_workers=args.max_workers)
                    print(f"  angle: {angle}\n    page: {e['url']}\n    guess: {chosen or '<no mp4 found>'}")
        elif args.method == "auto":
            angles = [a.strip() for a in (args.angles.split(",") if args.angles else []) if a.strip()]
            media_origin = args.guess_media_origin
            middle_tokens = [m.strip() for m in (args.middle_tokens.split(",") if args.middle_tokens else []) if m.strip()]
            for e in entries:
                print(f"- {e['title']}")
                for angle in angles:
                    candidates = guess_mp4_candidates(media_origin, e["gender"], e.get("equipment"), e.get("slug"), [angle], middle_tokens)
                    chosen = first_existing_url(candidates, max_workers=args.max_workers)
                    if chosen:
                        print(f"  angle: {angle}\n    page: {e['url']}\n    guess: {chosen}")
                    else:
                        resolved = find_mp4_in_page(e["url"]) or "<no mp4 found>"
                        print(f"  angle: {angle}\n    page: {e['url']}\n    parse: {resolved}")
        else:
            for e in entries:
                print(f"- {e['title']}\n  {e['url']}")
        return 0

    failures = 0
    if args.method == "direct-mp4":
        for e in tqdm(entries, desc="Downloading", unit="vid"):
            title_safe = sanitize_filename(e["title"]) or "video"
            out_path = os.path.join(args.output_dir, f"{title_safe}.mp4")
            mp4_url = e["url"] if e["url"].lower().endswith(".mp4") else find_mp4_in_page(e["url"])  # type: ignore
            if not mp4_url:
                failures += 1
                print(f"No .mp4 found on page: {e['url']}", file=sys.stderr)
                log_failure(args, {
                    "title": e["title"],
                    "page_url": e["url"],
                    "method": "direct-mp4",
                    "angle": "",
                    "reason": "no_mp4_in_page",
                    "equipment": e.get("equipment", ""),
                    "slug": e.get("slug", ""),
                })
                continue
            ok = download_mp4(mp4_url, out_path, skip_existing=args.skip_existing)
            if not ok:
                failures += 1
                log_failure(args, {
                    "title": e["title"],
                    "page_url": e["url"],
                    "method": "direct-mp4",
                    "angle": "",
                    "reason": "download_failed",
                    "equipment": e.get("equipment", ""),
                    "slug": e.get("slug", ""),
                })
            else:
                log_success(args, {
                    "title": e["title"],
                    "page_url": e["url"],
                    "method": "direct-mp4",
                    "angle": "",
                    "final_url": mp4_url,
                    "filename": out_path,
                    "equipment": e.get("equipment", ""),
                    "slug": e.get("slug", ""),
                })
    elif args.method == "guess-mp4":
        angles = [a.strip() for a in (args.angles.split(",") if args.angles else []) if a.strip()]
        media_origin = args.guess_media_origin
        middle_tokens = [m.strip() for m in (args.middle_tokens.split(",") if args.middle_tokens else []) if m.strip()]
        for e in tqdm(entries, desc="Downloading", unit="vid"):
            title_safe = sanitize_filename(e["title"]) or "video"
            # attempt each requested angle separately so we can get both front and side
            for angle in angles:
                candidates = guess_mp4_candidates(media_origin, e["gender"], e.get("equipment"), e.get("slug"), [angle], middle_tokens)
                chosen = first_existing_url(candidates, max_workers=args.max_workers)
                if not chosen:
                    failures += 1
                    print(f"No guessed .mp4 for angle '{angle}' on: {e['url']} (equipment={e.get('equipment')}, slug={e.get('slug')})", file=sys.stderr)
                    log_failure(args, {
                        "title": e["title"],
                        "page_url": e["url"],
                        "method": "guess-mp4",
                        "angle": angle,
                        "reason": "no_guess",
                        "equipment": e.get("equipment", ""),
                        "slug": e.get("slug", ""),
                    })
                    continue
                out_path = os.path.join(args.output_dir, f"{title_safe}-{angle}.mp4")
                ok = download_mp4(chosen, out_path, skip_existing=args.skip_existing)
                if not ok:
                    failures += 1
                    log_failure(args, {
                        "title": e["title"],
                        "page_url": e["url"],
                        "method": "guess-mp4",
                        "angle": angle,
                        "reason": "download_failed",
                        "equipment": e.get("equipment", ""),
                        "slug": e.get("slug", ""),
                    })
                else:
                    log_success(args, {
                        "title": e["title"],
                        "page_url": e["url"],
                        "method": "guess-mp4",
                        "angle": angle,
                        "final_url": chosen,
                        "filename": out_path,
                        "equipment": e.get("equipment", ""),
                        "slug": e.get("slug", ""),
                    })
    elif args.method == "auto":
        angles = [a.strip() for a in (args.angles.split(",") if args.angles else []) if a.strip()]
        media_origin = args.guess_media_origin
        middle_tokens = [m.strip() for m in (args.middle_tokens.split(",") if args.middle_tokens else []) if m.strip()]
        
        skipped = 0
        for e in tqdm(entries, desc="Downloading", unit="vid"):
            title_safe = sanitize_filename(e["title"]) or "video"
            
            # Check if all expected angle videos already exist
            if args.skip_existing and check_all_angles_exist(args.output_dir, title_safe, angles):
                skipped += 1
                continue
            
            any_downloaded = False
            for angle in angles:
                candidates = guess_mp4_candidates(media_origin, e["gender"], e.get("equipment"), e.get("slug"), [angle], middle_tokens)
                chosen = first_existing_url(candidates, max_workers=args.max_workers)
                out_path = os.path.join(args.output_dir, f"{title_safe}-{angle}.mp4")
                if chosen:
                    ok = download_mp4(chosen, out_path, skip_existing=args.skip_existing)
                    any_downloaded = any_downloaded or ok
                    if not ok:
                        failures += 1
                        log_failure(args, {
                            "title": e["title"],
                            "page_url": e["url"],
                            "method": "auto-guess",
                            "angle": angle,
                            "reason": "download_failed",
                            "equipment": e.get("equipment", ""),
                            "slug": e.get("slug", ""),
                        })
                    else:
                        log_success(args, {
                            "title": e["title"],
                            "page_url": e["url"],
                            "method": "auto-guess",
                            "angle": angle,
                            "final_url": chosen,
                            "filename": out_path,
                            "equipment": e.get("equipment", ""),
                            "slug": e.get("slug", ""),
                        })
                    continue
                # Fallback: parse page for a single mp4 (angle-agnostic)
                mp4_url = find_mp4_in_page(e["url"])  # may be None
                if mp4_url:
                    # save under angle-less filename for fallback
                    out_path_fallback = os.path.join(args.output_dir, f"{title_safe}.mp4")
                    ok = download_mp4(mp4_url, out_path_fallback, skip_existing=args.skip_existing)
                    any_downloaded = any_downloaded or ok
                    if not ok:
                        failures += 1
                        log_failure(args, {
                            "title": e["title"],
                            "page_url": e["url"],
                            "method": "auto-parse",
                            "angle": angle,
                            "reason": "download_failed",
                            "equipment": e.get("equipment", ""),
                            "slug": e.get("slug", ""),
                        })
                    else:
                        log_success(args, {
                            "title": e["title"],
                            "page_url": e["url"],
                            "method": "auto-parse",
                            "angle": angle,
                            "final_url": mp4_url,
                            "filename": out_path_fallback,
                            "equipment": e.get("equipment", ""),
                            "slug": e.get("slug", ""),
                        })
                else:
                    failures += 1
                    print(f"No .mp4 found via guess or parse: {e['url']}", file=sys.stderr)
                    log_failure(args, {
                        "title": e["title"],
                        "page_url": e["url"],
                        "method": "auto",
                        "angle": angle,
                        "reason": "no_guess_or_parse",
                        "equipment": e.get("equipment", ""),
                        "slug": e.get("slug", ""),
                    })
    else:
        # Download each entry via yt-dlp
        for e in tqdm(entries, desc="Downloading", unit="vid"):
            ydl_opts = build_ytdlp_opts(args, e["title"]) 
            try:
                with ytdlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([e["url"]])
                # Log a best-effort success entry (final URL unknown here)
                predicted = os.path.join(args.output_dir, f"{sanitize_filename(e['title'])}.mp4")
                log_success(args, {
                    "title": e["title"],
                    "page_url": e["url"],
                    "method": "yt-dlp",
                    "angle": "",
                    "final_url": e["url"],
                    "filename": predicted,
                    "equipment": e.get("equipment", ""),
                    "slug": e.get("slug", ""),
                })
            except Exception as ex:
                failures += 1
                print(f"Failed: {e['title']} -> {e['url']} : {ex}", file=sys.stderr)
                log_failure(args, {
                    "title": e["title"],
                    "page_url": e["url"],
                    "method": "yt-dlp",
                    "angle": "",
                    "reason": str(ex)[:200],
                    "equipment": e.get("equipment", ""),
                    "slug": e.get("slug", ""),
                })

    # Print summary
    if args.method == "auto" and args.skip_existing:
        print(f"\nSummary: {skipped} videos skipped (already exist), {failures} failures")
    elif failures:
        print(f"Completed with {failures} failures.")
    else:
        print("All downloads completed.")
    
    return 2 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
