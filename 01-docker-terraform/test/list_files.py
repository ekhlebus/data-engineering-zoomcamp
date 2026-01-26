#!/usr/bin/env python3

# This script lists all files in the current directory,
# excluding itself, and prints their contents.

from pathlib import Path # interacting with file system

current_dir = Path.cwd() # returns the current working directory (where the script is being run from).
current_file = Path(__file__).name # extracts the filename of the current script (__file__ does not work in Jupyter, only in .py scripts).

print(f"Files in {current_dir}:")

for filepath in current_dir.iterdir():  # iterdir() loops over everything inside the directory
    if filepath.name == current_file: # skip the current script file, to avoid reading itself
        continue

    print(f"  - {filepath.name}")

    if filepath.is_file():
        content = filepath.read_text(encoding='utf-8')
        print(f"    Content: {content}")