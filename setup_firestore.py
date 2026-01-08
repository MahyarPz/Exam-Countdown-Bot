#!/usr/bin/env python3
"""
Setup script for Firestore migration.
Use this to convert Firebase credentials to Heroku-compatible format.
"""

import json
import sys


def firebase_json_to_heroku_string(json_file: str) -> str:
    """Convert Firebase JSON key file to single-line Heroku config string."""
    try:
        with open(json_file, 'r') as f:
            creds = json.load(f)
        
        # Return as single-line JSON
        return json.dumps(creds)
    except FileNotFoundError:
        print(f"Error: File {json_file} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: {json_file} is not valid JSON")
        sys.exit(1)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python setup_firestore.py <firebase-key.json>")
        print("\nThis will output a single-line JSON string for Heroku.")
        print("Copy the output and add to Heroku Config Vars as FIREBASE_CREDENTIALS")
        sys.exit(1)
    
    json_file = sys.argv[1]
    result = firebase_json_to_heroku_string(json_file)
    
    print("\n" + "="*70)
    print("Add this to Heroku Config Vars:")
    print("="*70)
    print(f"FIREBASE_CREDENTIALS='{result}'")
    print("="*70)
    print("\nAlso add:")
    print(f"USE_FIRESTORE=1")
    print(f"FIREBASE_PROJECT_ID=your-project-id")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
