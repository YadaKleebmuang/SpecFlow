import hashlib
import os

NLU_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\data\nlu.yml"
CONFIG_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\config.yml"

def calculate_md5(filepath):
    if not os.path.exists(filepath):
        return "File Not Found"
    md5_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()

if __name__ == "__main__":
    print(f"nlu.yml MD5: {calculate_md5(NLU_PATH)}")
    print(f"config.yml MD5: {calculate_md5(CONFIG_PATH)}")
