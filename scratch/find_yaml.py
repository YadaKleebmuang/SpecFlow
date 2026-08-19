import os

def find_yaml_files():
    root_dir = r"c:\Users\yadak\Desktop"
    for root, dirs, files in os.walk(root_dir):
        # Skip venv and .git to avoid slow runs
        if 'venv' in root or '.git' in root or 'AppData' in root or 'node_modules' in root:
            continue
        for file in files:
            if file.endswith('.yml') or file.endswith('.yaml'):
                print(os.path.join(root, file))

if __name__ == "__main__":
    find_yaml_files()
