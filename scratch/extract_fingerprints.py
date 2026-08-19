import tarfile
import json
import os

MODEL_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\models\20260606-212000-relaxed-lagoon.tar.gz"
FINGERPRINT_FILE = "components/finetuning_validator/fingerprints-for-validation.json"

def extract_fingerprint():
    if not os.path.exists(MODEL_PATH):
        print("Model file not found")
        return
        
    with tarfile.open(MODEL_PATH, "r:gz") as tar:
        try:
            member = tar.getmember(FINGERPRINT_FILE)
            f = tar.extractfile(member)
            if f:
                data = json.loads(f.read().decode("utf-8"))
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print("Could not extract fingerprints file")
        except KeyError:
            print(f"File {FINGERPRINT_FILE} not found in archive")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    extract_fingerprint()
