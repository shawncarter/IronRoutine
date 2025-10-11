#!/usr/bin/env python3
"""
Extract exercise instructions and metadata from exercise pages.
Parses HTML to get instructions, difficulty, force, grips, mechanic, etc.
"""

import csv
import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
from tqdm import tqdm
import argparse
import json
import re


def parse_exercise_metadata(url: str, timeout: int = 10) -> dict:
    """
    Fetch the HTML page and extract exercise metadata and instructions.
    
    Args:
        url: The exercise page URL
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with exercise metadata
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        metadata = {
            'url': url,
            'instructions': [],
            'difficulty': None,
            'force': None,
            'grips': None,
            'mechanic': None,
        }
        
        # Extract instructions from the JSON data embedded in the page
        # The data is in "correct_steps" array with "text" fields
        
        # Method 1: Extract from correct_steps JSON structure
        correct_steps_pattern = r'correct_steps.*?\[(.*?)\]'
        matches = re.findall(correct_steps_pattern, response.text, re.DOTALL)
        
        if matches:
            steps_json = matches[0]
            # Extract individual step objects - use flexible pattern for text field
            step_pattern = r'text.*?:.*?"([^"]{20,})"'
            step_texts = re.findall(step_pattern, steps_json)
            
            # Remove duplicates (text and text_en_us often have same content)
            seen = set()
            for text in step_texts:
                # Unescape JSON strings
                clean_text = text.replace('\\n', ' ').replace('\\/', '/').replace('\\"', '"').replace('\\\\', '\\')
                clean_text = clean_text.strip()
                
                if clean_text and len(clean_text) > 10 and clean_text not in seen:
                    seen.add(clean_text)
                    metadata['instructions'].append(clean_text)
        
        # Method 2: Fallback - look for numbered instructions in text
        if not metadata['instructions']:
            instruction_lists = soup.find_all('ol')
            for ol in instruction_lists:
                items = ol.find_all('li')
                for item in items:
                    text = item.get_text(strip=True)
                    if text and len(text) > 10:
                        metadata['instructions'].append(text)
        
        # Extract metadata fields
        # Look for spans, divs, or text containing these labels
        html_text = soup.get_text()
        
        # Try to find difficulty (already have this from table, but can verify)
        difficulty_match = re.search(r'Difficulty[:\s]+([A-Za-z]+)', html_text, re.IGNORECASE)
        if difficulty_match:
            metadata['difficulty'] = difficulty_match.group(1).strip()
        
        # Extract Force
        force_match = re.search(r'Force[:\s]+([A-Za-z\s]+?)(?:\n|$|[A-Z])', html_text, re.IGNORECASE)
        if force_match:
            metadata['force'] = force_match.group(1).strip()
        
        # Extract Grips
        grips_match = re.search(r'Grips?[:\s]+([A-Za-z\s,]+?)(?:\n|$|[A-Z])', html_text, re.IGNORECASE)
        if grips_match:
            metadata['grips'] = grips_match.group(1).strip()
        
        # Extract Mechanic
        mechanic_match = re.search(r'Mechanic[:\s]+([A-Za-z\s]+?)(?:\n|$|[A-Z])', html_text, re.IGNORECASE)
        if mechanic_match:
            metadata['mechanic'] = mechanic_match.group(1).strip()
        
        # Also look for these in structured data (JSON-LD or meta tags)
        # Check for JSON data in script tags
        script_tags = soup.find_all('script', type='application/json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                # Recursively search for instruction-like data
                def find_instructions(obj, key_path=''):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if 'instruction' in k.lower() or 'step' in k.lower():
                                if isinstance(v, list):
                                    for item in v:
                                        if isinstance(item, str) and len(item) > 20:
                                            metadata['instructions'].append(item)
                                        elif isinstance(item, dict) and 'text' in item:
                                            metadata['instructions'].append(item['text'])
                            elif 'difficulty' in k.lower() and isinstance(v, str):
                                metadata['difficulty'] = v
                            elif 'force' in k.lower() and isinstance(v, str):
                                metadata['force'] = v
                            elif 'grip' in k.lower() and isinstance(v, str):
                                metadata['grips'] = v
                            elif 'mechanic' in k.lower() and isinstance(v, str):
                                metadata['mechanic'] = v
                            else:
                                find_instructions(v, f"{key_path}.{k}")
                    elif isinstance(obj, list):
                        for item in obj:
                            find_instructions(item, key_path)
                
                find_instructions(data)
            except:
                pass
        
        return metadata
        
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Extract exercise instructions and metadata')
    parser.add_argument('--html-file', default='table.html', help='Path to HTML table file')
    parser.add_argument('--output-csv', default='exercise_instructions.csv', help='Output CSV file')
    parser.add_argument('--rate-limit', type=float, default=0.5, help='Seconds to wait between requests')
    parser.add_argument('--max-exercises', type=int, help='Maximum number of exercises to process (for testing)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.html_file):
        print(f"Error: {args.html_file} not found")
        sys.exit(1)
    
    # Parse the HTML table to get all exercise URLs
    print(f"Reading {args.html_file}...")
    with open(args.html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Find all unique exercise URLs
    exercise_urls = {}
    
    for row in soup.find_all('tr', class_='border-gray-200'):
        links = row.find_all('a', href=True)
        if not links:
            continue
        
        # First link is the exercise title
        exercise_link = links[0]
        title = exercise_link.get_text(strip=True)
        
        if title.lower() in ['male', 'female', 'exercise']:
            continue
        
        url = exercise_link['href']
        if not url.startswith('http'):
            url = f"https://musclewiki.com{url}"
        
        # Parse URL to extract metadata
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) < 4:
            continue
        
        equipment = path_parts[0]
        gender = path_parts[1]
        muscle = path_parts[2]
        slug = path_parts[3]
        
        # Create unique key (without gender)
        key = f"{equipment}|{muscle}|{slug}"
        
        if key not in exercise_urls:
            exercise_urls[key] = {
                'title': title,
                'url': url,
                'equipment': equipment,
                'muscle': muscle,
                'slug': slug,
            }
    
    print(f"Found {len(exercise_urls)} unique exercises")
    
    if args.max_exercises:
        print(f"Limiting to {args.max_exercises} exercises for testing")
        exercise_urls = dict(list(exercise_urls.items())[:args.max_exercises])
    
    # Extract metadata for each exercise and write incrementally
    print(f"Writing results to {args.output_csv}...")
    
    # Check if CSV exists and load already-processed exercises
    processed_urls = set()
    file_exists = os.path.exists(args.output_csv)
    
    if file_exists:
        print(f"Found existing CSV, loading processed exercises...")
        with open(args.output_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_urls.add(row['url'])
        print(f"  {len(processed_urls)} exercises already processed")
    
    # Open CSV file for writing (append mode if exists, write mode if new)
    mode = 'a' if file_exists else 'w'
    with open(args.output_csv, mode, newline='', encoding='utf-8') as f:
        fieldnames = ['title', 'url', 'equipment', 'muscle', 'slug', 'instructions', 
                      'difficulty', 'force', 'grips', 'mechanic']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # Only write header if creating new file
        if not file_exists:
            writer.writeheader()
        
        # Track statistics
        success_count = 0
        skipped_count = len(processed_urls)
        
        for key, exercise in tqdm(exercise_urls.items(), desc="Extracting metadata"):
            # Skip if already processed
            if exercise['url'] in processed_urls:
                continue
            
            metadata = parse_exercise_metadata(exercise['url'])
            
            if metadata:
                result = {
                    'title': exercise['title'],
                    'url': metadata['url'],
                    'equipment': exercise['equipment'],
                    'muscle': exercise['muscle'],
                    'slug': exercise['slug'],
                    'instructions': json.dumps(metadata['instructions']),
                    'difficulty': metadata['difficulty'],
                    'force': metadata['force'],
                    'grips': metadata['grips'],
                    'mechanic': metadata['mechanic'],
                }
                writer.writerow(result)
                f.flush()  # Flush to disk immediately
                success_count += 1
            
            time.sleep(args.rate_limit)
    
    print(f"\nComplete!")
    print(f"  Total exercises in database: {len(exercise_urls)}")
    print(f"  Exercises processed this run: {success_count}")
    print(f"  Exercises skipped (already done): {skipped_count}")
    print(f"  Output saved to: {args.output_csv}")


if __name__ == '__main__':
    main()
