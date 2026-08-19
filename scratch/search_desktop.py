import os

def search_folders():
    paths = [
        r"c:\Users\yadak\Desktop",
        r"c:\Users\yadak\Downloads",
        r"c:\Users\yadak\Documents",
        r"c:\Users\yadak\.gemini"
    ]
    for p in paths:
        if not os.path.exists(p):
            continue
        print(f"Searching in {p}...")
        for root, dirs, files in os.walk(p):
            # Skip heavy folders to avoid slow runs
            if 'venv' in root or '.git' in root or 'AppData' in root or 'node_modules' in root:
                continue
            for file in files:
                if 'nlu_test.yml' in file or 'nlu_test' in file:
                    print(f"FOUND: {os.path.join(root, file)}")

if __name__ == "__main__":
    search_folders()
