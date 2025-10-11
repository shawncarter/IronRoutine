#!/usr/bin/env python3
"""
Query the exercise database to find exercises by muscle, equipment, etc.
"""

import argparse
import json
import sys


def load_database(db_file: str) -> dict:
    """Load the exercise database."""
    with open(db_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def filter_exercises(db: dict, muscle: str = None, equipment: str = None, 
                     gender: str = None, has_videos: bool = None) -> list[dict]:
    """Filter exercises by criteria."""
    results = db['exercises']
    
    if muscle:
        results = [e for e in results if e['muscle'].lower() == muscle.lower()]
    
    if equipment:
        results = [e for e in results if e['equipment'].lower() == equipment.lower()]
    
    if gender:
        # Filter by whether the exercise has videos for this gender
        results = [e for e in results if gender.lower() in e.get('videos', {})]
    
    if has_videos is not None:
        results = [e for e in results if e['has_videos'] == has_videos]
    
    return results


def print_exercises(exercises: list[dict], show_videos: bool = False):
    """Print exercises in a readable format."""
    for i, ex in enumerate(exercises, 1):
        video_status = "✓" if ex['has_videos'] else "✗"
        
        # Show which genders have videos
        genders_with_videos = list(ex.get('videos', {}).keys())
        gender_str = ", ".join(genders_with_videos) if genders_with_videos else "none"
        
        # Get difficulty
        difficulty = ex.get('difficulty', 'Unknown')
        
        print(f"{i}. [{video_status}] {ex['title']}")
        print(f"   Equipment: {ex['equipment']}, Muscle: {ex['muscle']}, Difficulty: {difficulty}")
        print(f"   Videos available for: {gender_str}")
        
        if show_videos and ex['videos']:
            for gender, angles in ex['videos'].items():
                print(f"   {gender.capitalize()}:")
                for angle, path in angles.items():
                    print(f"     - {angle}: {path}")
        
        print()


def main():
    parser = argparse.ArgumentParser(description="Query exercise database")
    parser.add_argument("--db", default="exercise_db.json", help="Path to exercise database JSON")
    parser.add_argument("--muscle", help="Filter by muscle group")
    parser.add_argument("--equipment", help="Filter by equipment type")
    parser.add_argument("--gender", help="Filter by gender (male/female)")
    parser.add_argument("--has-videos", action="store_true", help="Only show exercises with videos")
    parser.add_argument("--no-videos", action="store_true", help="Only show exercises without videos")
    parser.add_argument("--show-videos", action="store_true", help="Show video file paths")
    parser.add_argument("--list-muscles", action="store_true", help="List all muscle groups")
    parser.add_argument("--list-equipment", action="store_true", help="List all equipment types")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    args = parser.parse_args()
    
    # Load database
    db = load_database(args.db)
    
    # Show statistics
    if args.stats:
        print("=== Exercise Database Statistics ===")
        print(f"Total exercises: {db['metadata']['total_exercises']}")
        print(f"Exercises with videos: {db['metadata']['exercises_with_videos']}")
        print(f"Exercises without videos: {db['metadata']['exercises_without_videos']}")
        print(f"Equipment types: {len(db['metadata']['equipment_types'])}")
        print(f"Muscle groups: {len(db['metadata']['muscle_groups'])}")
        print(f"Genders: {len(db['metadata']['genders'])}")
        return 0
    
    # List muscles
    if args.list_muscles:
        print("=== Muscle Groups ===")
        for muscle in db['metadata']['muscle_groups']:
            count = len([e for e in db['exercises'] if e['muscle'] == muscle])
            print(f"- {muscle}: {count} exercises")
        return 0
    
    # List equipment
    if args.list_equipment:
        print("=== Equipment Types ===")
        for equipment in db['metadata']['equipment_types']:
            count = len([e for e in db['exercises'] if e['equipment'] == equipment])
            print(f"- {equipment}: {count} exercises")
        return 0
    
    # Filter exercises
    has_videos = None
    if args.has_videos:
        has_videos = True
    elif args.no_videos:
        has_videos = False
    
    results = filter_exercises(db, 
                              muscle=args.muscle, 
                              equipment=args.equipment,
                              gender=args.gender,
                              has_videos=has_videos)
    
    # Print results
    print(f"=== Found {len(results)} exercises ===\n")
    print_exercises(results, show_videos=args.show_videos)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
