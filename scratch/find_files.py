import os

def find_files():
    root_dir = r"c:\Users\yadak\Desktop\SpecFlow"
    for root, dirs, files in os.walk(root_dir):
        # Exclude venv and .git directories
        dirs[:] = [d for d in dirs if d not in ('venv', '.git')]
        for file in files:
            if 'nlu' in file.lower() or 'test' in file.lower() or 'config' in file.lower():
                print(os.path.join(root, file))

if __name__ == "__main__":
    find_files()
