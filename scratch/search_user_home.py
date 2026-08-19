import os

def search_user_home():
    home_dir = r"c:\Users\yadak"
    print(f"Searching in {home_dir}...")
    for root, dirs, files in os.walk(home_dir):
        # Exclude directories to make the search fast
        dirs[:] = [d for d in dirs if d not in (
            'venv', '.git', 'node_modules', 'AppData', 'Local', 'Roaming', 
            '3D Objects', 'Searches', 'Contacts', 'Links', 'Saved Games',
            'MicrosoftEdgeBackups', 'Music', 'Videos', 'Pictures'
        )]
        for file in files:
            if 'nlu_test.yml' in file or 'nlu_test' in file:
                print(f"FOUND: {os.path.join(root, file)}")

if __name__ == "__main__":
    search_user_home()
