#!/usr/bin/env python3
"""
Download videos from failures.csv by parsing HTML video containers.
Extracts video URLs from the page HTML and downloads them.
"""

import csv
import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time
from tqdm import tqdm
import argparse


def parse_video_urls_from_html(url: str, timeout: int = 10) -> list[str]:
    """
    Fetch the HTML page and extract video URLs using regex.
    The videos are embedded in the Next.js page data as JSON.
    
    Args:
        url: The exercise page URL
        timeout: Request timeout in seconds
        
    Returns:
        List of video URLs found on the page
    """
    import re
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        # Use regex to find all .mp4 URLs in the HTML
        # Look for branded videos specifically
        mp4_pattern = r'https://media\.musclewiki\.com/media/uploads/videos/branded/[^\s"\'<>]+\.mp4'
        video_urls = re.findall(mp4_pattern, response.text)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in video_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
        
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []


def infer_gender_counterpart(video_url: str, current_gender: str) -> str:
    """
    Given a video URL for one gender, infer the URL for the other gender.
    
    Args:
        video_url: The video URL (e.g., male-machine-back-extension-front.mp4)
        current_gender: The gender in the URL ('male' or 'female')
        
    Returns:
        The inferred URL for the opposite gender
    """
    other_gender = 'female' if current_gender == 'male' else 'male'
    return video_url.replace(f'{current_gender}-', f'{other_gender}-')


def download_video(video_url: str, output_path: str, timeout: int = 30) -> bool:
    """
    Download a video file.
    
    Args:
        video_url: URL of the video to download
        output_path: Local path to save the video
        timeout: Request timeout in seconds
        
    Returns:
        True if successful, False otherwise
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(video_url, headers=headers, timeout=timeout, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Download with progress
        total_size = int(response.headers.get('content-length', 0))
        with open(output_path, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        return True
        
    except Exception as e:
        print(f"Error downloading {video_url}: {e}")
        return False


def check_video_exists(video_url: str, timeout: int = 10) -> bool:
    """
    Check if a video URL exists without downloading it.
    
    Args:
        video_url: URL to check
        timeout: Request timeout in seconds
        
    Returns:
        True if the video exists, False otherwise
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.head(video_url, headers=headers, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except:
        return False


def construct_branded_video_url(equipment: str, slug: str, gender: str, angle: str) -> str:
    """
    Construct a branded video URL based on the pattern:
    https://media.musclewiki.com/media/uploads/videos/branded/{gender}-{equipment}-{simplified_slug}-{angle}.mp4
    
    Args:
        equipment: Equipment type (e.g., 'machine', 'barbell')
        slug: Exercise slug (e.g., 'machine-45-degree-back-extension')
        gender: Gender ('male' or 'female')
        angle: Camera angle ('front' or 'side')
        
    Returns:
        Constructed video URL
    """
    # Simplify the slug by removing the equipment prefix if present
    simplified_slug = slug
    
    # Remove equipment prefix from slug (e.g., 'machine-45-degree-back-extension' -> '45-degree-back-extension')
    if slug.startswith(f"{equipment}-"):
        simplified_slug = slug[len(equipment)+1:]
    
    # Construct the URL
    video_url = f"https://media.musclewiki.com/media/uploads/videos/branded/{gender}-{equipment}-{simplified_slug}-{angle}.mp4"
    
    return video_url


def main():
    parser = argparse.ArgumentParser(description='Download videos from failures.csv')
    parser.add_argument('--failures-csv', default='logs/failures.csv', help='Path to failures.csv')
    parser.add_argument('--output-dir', default='videos', help='Output directory for videos')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be downloaded without downloading')
    parser.add_argument('--skip-existing', action='store_true', help='Skip videos that already exist locally')
    parser.add_argument('--rate-limit', type=float, default=0.5, help='Seconds to wait between requests')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.failures_csv):
        print(f"Error: {args.failures_csv} not found")
        sys.exit(1)
    
    # Read failures CSV
    print(f"Reading {args.failures_csv}...")
    failures = []
    with open(args.failures_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            failures.append(row)
    
    print(f"Found {len(failures)} failed downloads")
    
    # Group by URL to avoid fetching the same page multiple times
    url_to_failures = {}
    for failure in failures:
        url = failure['page_url']
        if url not in url_to_failures:
            url_to_failures[url] = []
        url_to_failures[url].append(failure)
    
    print(f"Processing {len(url_to_failures)} unique URLs...")
    
    success_count = 0
    failure_count = 0
    skipped_count = 0
    
    for url, url_failures in tqdm(url_to_failures.items(), desc="Processing URLs"):
        # Parse the URL to get gender
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) < 4:
            print(f"Skipping invalid URL: {url}")
            continue
        
        equipment = path_parts[0]
        gender = path_parts[1]
        muscle = path_parts[2]
        slug = path_parts[3]
        
        # Get the exercise name from the first failure
        exercise_name = url_failures[0]['title'].rsplit(' - ', 1)[0]  # Remove gender suffix
        
        # Fetch video URLs from the page HTML
        video_urls = parse_video_urls_from_html(url)
        
        if not video_urls:
            print(f"\nNo videos found for {exercise_name}")
            failure_count += len(url_failures)
            time.sleep(args.rate_limit)
            continue
        
        # Process each video URL found
        videos_to_download = []
        
        for video_url in video_urls:
            # Determine the angle from the video URL
            if 'front' in video_url.lower():
                angle = 'front'
            elif 'side' in video_url.lower():
                angle = 'side'
            else:
                angle = 'unknown'
            
            # Determine gender from video URL
            if '/male-' in video_url and '/female-' not in video_url:
                video_gender = 'Male'
            elif '/female-' in video_url:
                video_gender = 'Female'
            else:
                # Fallback to URL gender
                video_gender = gender.capitalize()
            
            videos_to_download.append((video_url, video_gender, angle))
        
        # Download each video
        for video_url, video_gender, angle in videos_to_download:
            # Construct output filename: Muscle - Exercise - Gender-angle.mp4
            muscle_display = muscle.replace('-', ' ').title()
            output_filename = f"{muscle_display} - {exercise_name} - {video_gender}-{angle}.mp4"
            output_path = os.path.join(args.output_dir, output_filename)
            
            # Check if file already exists
            if args.skip_existing and os.path.exists(output_path):
                skipped_count += 1
                continue
            
            if args.dry_run:
                print(f"\nWould download: {video_url}")
                print(f"  -> {output_path}")
                success_count += 1
            else:
                if download_video(video_url, output_path):
                    print(f"\n✓ Downloaded: {output_filename}")
                    success_count += 1
                else:
                    print(f"\n✗ Failed: {output_filename}")
                    failure_count += 1
        
        time.sleep(args.rate_limit)
    
    print(f"\n{'Dry run ' if args.dry_run else ''}Summary:")
    print(f"  Success: {success_count}")
    print(f"  Failed: {failure_count}")
    print(f"  Skipped (already exist): {skipped_count}")


if __name__ == '__main__':
    main()
