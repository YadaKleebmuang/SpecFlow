import os
import tarfile
import json

MODELS_DIR = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\models"

def search_models():
    if not os.path.exists(MODELS_DIR):
        print("Models directory not found")
        return
        
    for file in os.listdir(MODELS_DIR):
        if not file.endswith(".tar.gz"):
            continue
        path = os.path.join(MODELS_DIR, file)
        try:
            with tarfile.open(path, "r:gz") as tar:
                names = tar.getnames()
                # Search inside names
                for name in names:
                    if "nlu" in name.lower() or "test" in name.lower():
                        print(f"Model {file} contains: {name}")
                # Check metadata.json inside model
                if "metadata.json" in names:
                    meta_file = tar.extractfile("metadata.json")
                    if meta_file:
                        meta = json.loads(meta_file.read().decode("utf-8"))
                        fingerprint = meta.get("project_fingerprint")
                        print(f"Model {file}: project_fingerprint={fingerprint}")
        except Exception as e:
            print(f"Error reading model {file}: {e}")

if __name__ == "__main__":
    search_models()
