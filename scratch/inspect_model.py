import tarfile
import json
import os

MODEL_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\models\20260606-212000-relaxed-lagoon.tar.gz"

def inspect_model():
    if not os.path.exists(MODEL_PATH):
        print("Model file not found")
        return
        
    with tarfile.open(MODEL_PATH, "r:gz") as tar:
        try:
            metadata_file = tar.extractfile("metadata.json")
            if metadata_file:
                metadata = json.loads(metadata_file.read().decode("utf-8"))
                print("Model ID:", metadata.get("model_id"))
                print("Assistant ID:", metadata.get("assistant_id"))
                print("Rasa Open Source Version:", metadata.get("rasa_open_source_version"))
                print("Trained At:", metadata.get("trained_at"))
                print("Project Fingerprint:", metadata.get("project_fingerprint"))
                print("Language:", metadata.get("language"))
                print("Training Type:", metadata.get("training_type"))
            else:
                print("metadata.json not found in archive")
        except Exception as e:
            print(f"Error reading metadata.json: {e}")

if __name__ == "__main__":
    inspect_model()
