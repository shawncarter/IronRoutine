#!/usr/bin/env python3
"""
Retry script for failed video downloads.
Reads failures.csv and attempts to download using improved URL guessing and HTML parsing.
"""
import argparse
import csv
import os
import sys
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

UA_HEADERS = {"User-Agent": "Mozilla/5.0"}


def sanitize_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", " ", name)
    return name


def download_mp4(mp4_url: str, dest_path: str, skip_existing: bool = False) -> bool:
    """Download a direct .mp4 URL to dest_path. Returns True on success."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    if skip_existing and os.path.exists(dest_path):
        return True
    try:
        with requests.get(mp4_url, stream=True, timeout=60, headers=UA_HEADERS) as resp:
            resp.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as ex:
        print(f"Download failed: {mp4_url} -> {dest_path} : {ex}", file=sys.stderr)
        return False


def extract_videos_from_page(page_url: str) -> list[str]:
    """Extract video URLs from the page by parsing <video> tags."""
    try:
        resp = requests.get(page_url, timeout=30, headers=UA_HEADERS, allow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch page {page_url}: {e}", file=sys.stderr)
        return []
    
    soup = BeautifulSoup(resp.text, "html.parser")
    video_urls = []
    
    # Look for <video src> directly
    for v in soup.find_all("video"):
        src = v.get("src") or v.get("data-src")
        if src and src.lower().endswith(".mp4"):
            video_urls.append(urljoin(page_url, src))
        # Look at child <source> tags
        for source in v.find_all("source"):
            s = source.get("src") or source.get("data-src")
            if s and s.lower().endswith(".mp4"):
                video_urls.append(urljoin(page_url, s))
    
    return video_urls


def generate_improved_guesses(media_origin: str, gender: str, equipment: str, slug: str, angle: str) -> list[str]:
    """Generate improved URL guesses based on observed patterns."""
    candidates = []
    
    # Generate equipment variants (similar to main scraper)
    equipment_variants = [""]  # Always try without equipment
    if equipment:
        equipment_variants.append(equipment)  # Original
        equipment_variants.append(equipment.capitalize())  # First letter cap
        equipment_variants.append(equipment.title())  # Title case
        
        # Remove hyphens and try variations
        no_hyphen = equipment.replace("-", "")
        equipment_variants.append(no_hyphen)
        equipment_variants.append(no_hyphen.capitalize())
        equipment_variants.append(no_hyphen.title())
        
        # Singular forms (remove trailing 's')
        if equipment.endswith("s"):
            equipment_variants.append(equipment[:-1])
            equipment_variants.append(equipment[:-1].capitalize())
            equipment_variants.append(equipment[:-1].title())
            
            no_hyphen_singular = equipment[:-1].replace("-", "")
            equipment_variants.append(no_hyphen_singular)
            equipment_variants.append(no_hyphen_singular.capitalize())
            equipment_variants.append(no_hyphen_singular.title())
    
    # Generate slug variants
    slug_variants = [slug]
    
    # Remove "variation-" if present
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
    
    # Generate URLs with all combinations of equipment and slug variants
    for eq_var in equipment_variants:
        for slug_var in slug_variants:
            # Build equipment part
            eq_part = f"-{eq_var}" if eq_var else ""
            
            # Pattern 1: branded folder (most common)
            candidates.append(f"{media_origin}/media/uploads/videos/branded/{gender}{eq_part}-{slug_var}-{angle}.mp4")
            
            # Pattern 2: without branded folder
            candidates.append(f"{media_origin}/media/uploads/videos/{gender}{eq_part}-{slug_var}-{angle}.mp4")
    
    return candidates


def check_url_exists(url: str) -> bool:
    """Check if a URL exists."""
    try:
        resp = requests.head(url, timeout=5, allow_redirects=True, headers=UA_HEADERS)
        if resp.ok:
            return True
        # Fallback to GET
        resp = requests.get(url, stream=True, timeout=5, headers=UA_HEADERS)
        return resp.ok
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Retry failed video downloads")
    parser.add_argument("--failures-csv", default="logs/failures.csv", help="Path to failures.csv")
    parser.add_argument("--output-dir", default="downloads_retry", help="Output directory for videos")
    parser.add_argument("--skip-existing", action="store_true", help="Skip if file exists")
    parser.add_argument("--media-origin", default="https://media.musclewiki.com", help="Media origin URL")
    parser.add_argument("--method", choices=["guess", "parse", "both"], default="both", 
                        help="Method: guess URLs, parse page, or try both")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    # Read failures CSV
    if not os.path.exists(args.failures_csv):
        print(f"Failures CSV not found: {args.failures_csv}", file=sys.stderr)
        return 1
    
    failures = []
    with open(args.failures_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            failures.append(row)
    
    print(f"Found {len(failures)} failed downloads to retry")
    
    successes = 0
    still_failed = 0
    
    for entry in tqdm(failures, desc="Retrying", unit="vid", disable=args.verbose):
        title = entry["title"]
        page_url = entry["page_url"]
        angle = entry["angle"]
        equipment = entry.get("equipment", "")
        slug = entry.get("slug", "")
        
        # Extract gender from page URL
        gender = "male" if "/male/" in page_url else "female"
        
        title_safe = sanitize_filename(title)
        out_path = os.path.join(args.output_dir, f"{title_safe}-{angle}.mp4")
        
        if args.verbose:
            print(f"\n{'='*60}")
            print(f"Processing: {title} ({angle})")
            print(f"  Page: {page_url}")
            print(f"  Equipment: {equipment}, Slug: {slug}")
        
        found_url = None
        
        # Method 1: Parse page for video tags
        if args.method in ["parse", "both"]:
            if args.verbose:
                print(f"  Trying method: parse page HTML...")
            video_urls = extract_videos_from_page(page_url)
            if args.verbose:
                print(f"    Found {len(video_urls)} video URLs on page")
                for vurl in video_urls:
                    print(f"      - {vurl}")
            # Find the one matching the angle
            for vurl in video_urls:
                if f"-{angle}.mp4" in vurl.lower():
                    found_url = vurl
                    if args.verbose:
                        print(f"    ✓ Matched angle: {found_url}")
                    break
        
        # Method 2: Improved guessing
        if not found_url and args.method in ["guess", "both"]:
            if equipment and slug:
                if args.verbose:
                    print(f"  Trying method: guess URLs...")
                candidates = generate_improved_guesses(args.media_origin, gender, equipment, slug, angle)
                if args.verbose:
                    print(f"    Generated {len(candidates)} candidate URLs")
                for i, candidate in enumerate(candidates):
                    if args.verbose:
                        print(f"    [{i+1}/{len(candidates)}] Checking: {candidate}")
                    if check_url_exists(candidate):
                        found_url = candidate
                        if args.verbose:
                            print(f"    ✓ Found: {found_url}")
                        break
            elif args.verbose:
                print(f"  Skipping guess method: missing equipment or slug")
        
        if found_url:
            if args.dry_run:
                print(f"✓ Would download: {title} ({angle})")
                print(f"  URL: {found_url}")
                print(f"  Dest: {out_path}")
                successes += 1
            else:
                ok = download_mp4(found_url, out_path, skip_existing=args.skip_existing)
                if ok:
                    successes += 1
                    print(f"✓ {title} ({angle})")
                else:
                    still_failed += 1
                    print(f"✗ {title} ({angle}) - download failed", file=sys.stderr)
        else:
            still_failed += 1
            print(f"✗ {title} ({angle}) - no URL found", file=sys.stderr)
    
    print(f"\nResults: {successes} succeeded, {still_failed} still failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
