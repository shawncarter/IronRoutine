#!/usr/bin/env python3
"""
Build an exercise database from the scraped HTML table.
Creates a JSON file with all exercises, their metadata, and video file paths.
"""

import argparse
import json
import os
import re
import csv
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be a valid filename."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def parse_exercise_table(html_file: str) -> list[dict]:
    """Parse the HTML table and extract exercise information."""
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Use a dict to consolidate exercises by unique key
    exercises_dict = {}
    
    # Find all table rows
    for row in soup.find_all('tr', class_='border-gray-200'):
        # Find ALL links in this row
        all_links = row.find_all('a', href=True)
        if not all_links:
            continue
        
        # The first link is the exercise title
        exercise_link = all_links[0]
        title = exercise_link.get_text(strip=True)
        
        # Skip header rows or invalid entries
        if title.lower() in ['male', 'female', 'exercise']:
            continue
        
        # Extract difficulty from the last column
        difficulty_span = row.find('span', class_='text-gray-50')
        difficulty = difficulty_span.get_text(strip=True) if difficulty_span else None
        
        # Process all links in the row (exercise title + male/female video links)
        for link in all_links:
            url = link['href']
            link_text = link.get_text(strip=True).lower()
            
            # Parse URL to extract metadata
            # Expected format: /equipment/gender/muscle/exercise-slug
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            
            if len(path_parts) < 4:
                continue
            
            equipment = path_parts[0]
            gender = path_parts[1]
            muscle = path_parts[2]
            slug = path_parts[3]
            
            # Create unique key for this exercise (without gender)
            key = f"{equipment}|{muscle}|{slug}"
            
            # If this exercise doesn't exist yet, create it
            if key not in exercises_dict:
                exercises_dict[key] = {
                    "title": title,
                    "slug": slug,
                    "equipment": equipment,
                    "muscle": muscle,
                    "difficulty": difficulty,
                    "urls": {},
                }
            
            # Add the gender-specific URL
            full_url = f"https://musclewiki.com{url}" if not url.startswith('http') else url
            exercises_dict[key]["urls"][gender] = full_url
    
    # Convert dict to list
    return list(exercises_dict.values())


def find_video_files(output_dir: str, title: str, gender: str, muscle: str, angles: list[str]) -> dict[str, str]:
    """Find video files for an exercise."""
    # Video files are named: {Muscle} - {Exercise} - {Gender}-{angle}.mp4
    # e.g., "Biceps - Barbell Curl - Male-front.mp4"
    gender_cap = gender.capitalize()
    muscle_cap = muscle.replace('-', ' ').title()  # Convert "traps-middle" to "Traps Middle"
    
    # Build the full title as it appears in the filename
    full_title = f"{muscle_cap} - {title} - {gender_cap}"
    title_safe = sanitize_filename(full_title)
    videos = {}
    
    for angle in angles:
        video_path = os.path.join(output_dir, f"{title_safe}-{angle}.mp4")
        if os.path.exists(video_path):
            videos[angle] = video_path
    
    return videos


def load_instructions(instructions_csv: str) -> dict:
    """Load exercise instructions from CSV file."""
    instructions_dict = {}
    
    if not os.path.exists(instructions_csv):
        print(f"Warning: Instructions file not found: {instructions_csv}")
        return instructions_dict
    
    with open(instructions_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Create key from equipment, muscle, slug
            key = f"{row['equipment']}|{row['muscle']}|{row['slug']}"
            instructions_dict[key] = {
                'instructions': json.loads(row['instructions']) if row['instructions'] else [],
                'difficulty': row.get('difficulty'),
                'force': row.get('force'),
                'grips': row.get('grips'),
                'mechanic': row.get('mechanic'),
            }
    
    print(f"Loaded instructions for {len(instructions_dict)} exercises")
    return instructions_dict


def build_database(html_file: str, video_dir: str, angles: list[str], instructions_csv: str = None) -> dict:
    """Build the complete exercise database."""
    exercises = parse_exercise_table(html_file)
    
    # Load instructions if CSV provided
    instructions_dict = {}
    if instructions_csv:
        instructions_dict = load_instructions(instructions_csv)
    
    # Add video file paths and instructions for each exercise
    for exercise in exercises:
        exercise['videos'] = {}
        
        # Find videos for each gender
        for gender in ['male', 'female']:
            if gender in exercise['urls']:
                gender_videos = find_video_files(video_dir, exercise['title'], gender, exercise['muscle'], angles)
                if gender_videos:
                    exercise['videos'][gender] = gender_videos
        
        exercise['has_videos'] = len(exercise['videos']) > 0
        
        # Merge in instructions if available
        key = f"{exercise['equipment']}|{exercise['muscle']}|{exercise['slug']}"
        if key in instructions_dict:
            exercise['instructions'] = instructions_dict[key]['instructions']
            # Update difficulty from instructions if available (more detailed than table)
            if instructions_dict[key]['difficulty']:
                exercise['difficulty'] = instructions_dict[key]['difficulty']
            exercise['force'] = instructions_dict[key]['force']
            exercise['grips'] = instructions_dict[key]['grips']
            exercise['mechanic'] = instructions_dict[key]['mechanic']
        else:
            exercise['instructions'] = []
            exercise['force'] = None
            exercise['grips'] = None
            exercise['mechanic'] = None
    
    # Build indices for quick filtering
    db = {
        "exercises": exercises,
        "metadata": {
            "total_exercises": len(exercises),
            "equipment_types": sorted(list(set(e['equipment'] for e in exercises))),
            "muscle_groups": sorted(list(set(e['muscle'] for e in exercises))),
        }
    }
    
    # Count exercises with videos
    with_videos = sum(1 for e in exercises if e['has_videos'])
    db["metadata"]["exercises_with_videos"] = with_videos
    db["metadata"]["exercises_without_videos"] = len(exercises) - with_videos
    
    # Count videos by gender
    male_videos = sum(1 for e in exercises if 'male' in e.get('videos', {}))
    female_videos = sum(1 for e in exercises if 'female' in e.get('videos', {}))
    db["metadata"]["exercises_with_male_videos"] = male_videos
    db["metadata"]["exercises_with_female_videos"] = female_videos
    
    return db


def filter_exercises(db: dict, muscle: str = None, equipment: str = None, gender: str = None, has_videos: bool = None) -> list[dict]:
    """Filter exercises by criteria."""
    results = db['exercises']
    
    if muscle:
        results = [e for e in results if e['muscle'] == muscle]
    
    if equipment:
        results = [e for e in results if e['equipment'] == equipment]
    
    if gender:
        results = [e for e in results if e['gender'] == gender]
    
    if has_videos is not None:
        results = [e for e in results if e['has_videos'] == has_videos]
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Build exercise database from HTML table")
    parser.add_argument("--html-file", default="table.html", help="Path to HTML table file")
    parser.add_argument("--video-dir", default="videos", help="Directory containing video files")
    parser.add_argument("--output", default="exercise_db.json", help="Output JSON file")
    parser.add_argument("--instructions-csv", default="exercise_instructions.csv", help="Path to instructions CSV file")
    parser.add_argument("--angles", default="front,side", help="Comma-separated list of video angles")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()
    
    angles = [a.strip() for a in args.angles.split(',') if a.strip()]
    
    print(f"Building exercise database from {args.html_file}...")
    db = build_database(args.html_file, args.video_dir, angles, args.instructions_csv)
    
    # Write to JSON file
    with open(args.output, 'w', encoding='utf-8') as f:
        if args.pretty:
            json.dump(db, f, indent=2, ensure_ascii=False)
        else:
            json.dump(db, f, ensure_ascii=False)
    
    print(f"\nDatabase created: {args.output}")
    print(f"Total exercises: {db['metadata']['total_exercises']}")
    print(f"Exercises with videos: {db['metadata']['exercises_with_videos']}")
    print(f"Exercises without videos: {db['metadata']['exercises_without_videos']}")
    print(f"\nEquipment types ({len(db['metadata']['equipment_types'])}): {', '.join(db['metadata']['equipment_types'])}")
    print(f"Muscle groups ({len(db['metadata']['muscle_groups'])}): {', '.join(db['metadata']['muscle_groups'])}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
