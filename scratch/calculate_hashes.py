import hashlib
import os

NLU_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\data\nlu.yml"
CONFIG_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\config.yml"

def calculate_sha256(filepath):
    if not os.path.exists(filepath):
        return "File Not Found"
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

if __name__ == "__main__":
    print(f"nlu.yml SHA-256: {calculate_sha256(NLU_PATH)}")
    print(f"config.yml SHA-256: {calculate_sha256(CONFIG_PATH)}")
