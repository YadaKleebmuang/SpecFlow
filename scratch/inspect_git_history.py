import subprocess
import os

def check_git_history():
    cwd = r"c:\Users\yadak\Desktop\SpecFlow"
    # Get all commit hashes
    result = subprocess.run(["git", "log", "--format=%H"], capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    commits = result.stdout.strip().split("\n")
    print(f"Total commits in history: {len(commits)}")
    
    found_nlu_test = False
    for commit in commits:
        if not commit:
            continue
        # Show files in this commit
        res = subprocess.run(["git", "show", "--name-only", "--format=", commit], capture_output=True, text=True, encoding="utf-8", errors="ignore", cwd=cwd)
        files = res.stdout.strip().split("\n")
        for f in files:
            if "nlu_test" in f:
                print(f"Found nlu_test in commit {commit}: {f}")
                found_nlu_test = True
                
        # Let's check nlu.yml content in this commit
        nlu_file = "app/rasa/data/nlu.yml"
        res_show = subprocess.run(["git", "show", f"{commit}:{nlu_file}"], capture_output=True, text=True, encoding="utf-8", errors="ignore", cwd=cwd)
        if res_show.returncode == 0 and res_show.stdout:
            content = res_show.stdout
            lines = content.split("\n")
            # Count lines starting with "    - "
            examples = [l for l in lines if l.startswith("    - ")]
            print(f"Commit {commit[:7]}: nlu.yml has {len(examples)} examples")
            
    if not found_nlu_test:
        print("No nlu_test.yml found in any git commit history.")

if __name__ == "__main__":
    check_git_history()
