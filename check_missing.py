#!/usr/bin/env python3
"""
Check what videos and instructions are missing from the collection.
Generates reports of missing items for targeted downloading.
"""

import argparse
import json
import os
import csv
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def parse_all_exercises_from_html(html_file: str) -> list[dict]:
    """Parse all exercises from the HTML table.
    
    Each row in the table has 3 links:
    1. Exercise name (points to male version)
    2. "Male" link (same URL as exercise name - DUPLICATE)
    3. "Female" link (points to female version)
    
    We collect only the unique male and female URLs (2 per exercise).
    Expected: 1603 exercises × 2 genders = 3206 unique URLs
    """
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    exercises = []
    seen_urls = set()
    
    for row in soup.find_all('tr', class_='border-gray-200'):
        all_links = row.find_all('a', href=True)
        if len(all_links) != 3:  # Should have exactly 3 links per row
            continue
        
        # Get exercise title from first link
        exercise_link = all_links[0]
        title = exercise_link.get_text(strip=True)
        
        if title.lower() in ['male', 'female', 'exercise']:
            continue
        
        # Extract unique URLs: male (from link 1 or 2) and female (from link 3)
        male_url = all_links[0]['href']  # Exercise name link = male URL
        female_url = all_links[2]['href']  # Female link
        
        for url, gender_type in [(male_url, 'male'), (female_url, 'female')]:
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            
            if len(path_parts) < 4:
                continue
            
            equipment = path_parts[0]
            gender = path_parts[1]
            muscle = path_parts[2]
            slug = path_parts[3]
            
            # Verify gender matches expected
            if gender != gender_type:
                continue
            
            full_url = f"https://musclewiki.com{url}" if not url.startswith('http') else url
            
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                exercises.append({
                    'title': title,
                    'url': full_url,
                    'equipment': equipment,
                    'gender': gender,
                    'muscle': muscle,
                    'slug': slug,
                })
    
    return exercises


def check_video_exists(video_dir: str, title: str, gender: str, muscle: str, angle: str) -> bool:
    """Check if a video file exists."""
    muscle_cap = muscle.replace('-', ' ').title()
    gender_cap = gender.capitalize()
    filename = f"{muscle_cap} - {title} - {gender_cap}-{angle}.mp4"
    filepath = os.path.join(video_dir, filename)
    return os.path.exists(filepath)


def load_instructions_csv(csv_file: str) -> set:
    """Load URLs that have instructions."""
    urls_with_instructions = set()
    
    if not os.path.exists(csv_file):
        return urls_with_instructions
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            urls_with_instructions.add(row['url'])
    
    return urls_with_instructions


def main():
    parser = argparse.ArgumentParser(description='Check for missing videos and instructions')
    parser.add_argument('--html-file', default='table.html', help='Path to HTML table file')
    parser.add_argument('--video-dir', default='videos', help='Directory containing video files')
    parser.add_argument('--instructions-csv', default='exercise_instructions.csv', help='Path to instructions CSV')
    parser.add_argument('--angles', default='front,side', help='Comma-separated list of video angles')
    parser.add_argument('--output-missing-videos', default='missing_videos.csv', help='Output CSV for missing videos')
    parser.add_argument('--output-missing-instructions', default='missing_instructions.csv', help='Output CSV for missing instructions')
    
    args = parser.parse_args()
    
    angles = [a.strip() for a in args.angles.split(',') if a.strip()]
    
    print("Analyzing exercise collection...")
    print(f"Reading {args.html_file}...")
    
    # Parse all exercises from HTML
    all_exercises = parse_all_exercises_from_html(args.html_file)
    
    # Calculate exercise statistics
    total_exercise_rows = len(all_exercises) // 2  # 2 URLs per exercise (male + female)
    total_expected_videos = total_exercise_rows * len(angles) * 2  # exercises × angles × genders
    
    print(f"Found {len(all_exercises)} exercise URLs in HTML")
    print(f"This represents {total_exercise_rows} unique exercises")
    print(f"Expected total videos: {total_expected_videos} ({total_exercise_rows} exercises × {len(angles)} angles × 2 genders)")
    
    # Load instructions
    urls_with_instructions = load_instructions_csv(args.instructions_csv)
    print(f"Found {len(urls_with_instructions)} exercises with instructions")
    
    # Consolidate exercises by unique key (equipment|muscle|slug)
    unique_exercises = {}
    for exercise in all_exercises:
        key = f"{exercise['equipment']}|{exercise['muscle']}|{exercise['slug']}"
        if key not in unique_exercises:
            unique_exercises[key] = {
                'title': exercise['title'],
                'equipment': exercise['equipment'],
                'muscle': exercise['muscle'],
                'slug': exercise['slug'],
                'genders': {}
            }
        unique_exercises[key]['genders'][exercise['gender']] = exercise['url']
    
    print(f"Consolidated to {len(unique_exercises)} unique exercises")
    
    # Check for missing videos
    missing_videos = []
    exercises_with_all_videos = 0
    exercises_with_some_videos = 0
    exercises_with_no_videos = 0
    
    for key, exercise in unique_exercises.items():
        total_expected = len(exercise['genders']) * len(angles)  # e.g., 2 genders × 2 angles = 4 videos
        videos_found = 0
        
        for gender in exercise['genders'].keys():
            for angle in angles:
                if check_video_exists(args.video_dir, exercise['title'], gender, exercise['muscle'], angle):
                    videos_found += 1
                else:
                    missing_videos.append({
                        'title': exercise['title'],
                        'url': exercise['genders'][gender],
                        'equipment': exercise['equipment'],
                        'gender': gender,
                        'muscle': exercise['muscle'],
                        'slug': exercise['slug'],
                        'missing_angle': angle,
                    })
        
        if videos_found == total_expected:
            exercises_with_all_videos += 1
        elif videos_found > 0:
            exercises_with_some_videos += 1
        else:
            exercises_with_no_videos += 1
    
    # Check for missing instructions
    missing_instructions = []
    for exercise in all_exercises:
        if exercise['url'] not in urls_with_instructions:
            missing_instructions.append(exercise)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\nEXERCISE ANALYSIS:")
    print(f"  Total exercise URLs in HTML: {len(all_exercises)}")
    print(f"  Unique exercises: {total_exercise_rows}")
    print(f"  Expected total videos: {total_expected_videos}")
    print(f"\nVIDEO ANALYSIS:")
    print(f"  Exercises with all videos ({len(angles)} angles × 2 genders): {exercises_with_all_videos}")
    print(f"  Exercises with some videos: {exercises_with_some_videos}")
    print(f"  Exercises with no videos: {exercises_with_no_videos}")
    print(f"  Total missing video files: {len(missing_videos)}")
    videos_found = total_expected_videos - len(missing_videos)
    completion_rate = (videos_found / total_expected_videos) * 100 if total_expected_videos > 0 else 0
    print(f"  Video collection completion: {completion_rate:.1f}% ({videos_found}/{total_expected_videos})")
    print(f"\nINSTRUCTION ANALYSIS:")
    print(f"  Exercises with instructions: {len(urls_with_instructions)}")
    print(f"  Exercises missing instructions: {len(missing_instructions)}")
    instruction_completion = (len(urls_with_instructions) / len(all_exercises)) * 100 if all_exercises else 0
    print(f"  Instruction completion: {instruction_completion:.1f}% ({len(urls_with_instructions)}/{len(all_exercises)})")
    
    # Write missing videos to CSV with URLs for scraper parsing
    if missing_videos:
        print(f"\nWriting missing videos to {args.output_missing_videos}...")
        with open(args.output_missing_videos, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['title', 'url', 'equipment', 'gender', 'muscle', 'slug', 'missing_angle', 'exercise_key']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Add exercise_key for easier parsing by scraper
            for video in missing_videos:
                video['exercise_key'] = f"{video['equipment']}|{video['muscle']}|{video['slug']}"
                writer.writerow(video)
        print(f"  Wrote {len(missing_videos)} missing video entries")
        
        # Group missing videos by exercise for summary
        missing_by_exercise = {}
        for video in missing_videos:
            key = video['exercise_key']
            if key not in missing_by_exercise:
                missing_by_exercise[key] = {'title': video['title'], 'missing_count': 0, 'urls': set()}
            missing_by_exercise[key]['missing_count'] += 1
            missing_by_exercise[key]['urls'].add(video['url'])
        
        print(f"  Missing videos affect {len(missing_by_exercise)} unique exercises")
    
    # Write missing instructions to CSV
    if missing_instructions:
        print(f"\nWriting missing instructions to {args.output_missing_instructions}...")
        with open(args.output_missing_instructions, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['title', 'url', 'equipment', 'gender', 'muscle', 'slug']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(missing_instructions)
        print(f"  Wrote {len(missing_instructions)} missing instruction entries")
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
