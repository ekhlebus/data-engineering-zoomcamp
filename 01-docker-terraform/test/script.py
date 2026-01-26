from pathlib from Path # interacting with file system

current_dir = Path.cwd()
current_file = Path(__file__).name

print(f"Files in {current_dir}:")
