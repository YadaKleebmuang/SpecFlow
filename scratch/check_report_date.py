import os
import datetime

MODEL_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\models\20260606-212000-relaxed-lagoon.tar.gz"
INTENT_REPORT = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\results\intent_report.json"
DIET_REPORT = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\results\DIETClassifier_report.json"

def get_mod_date(filepath):
    if not os.path.exists(filepath):
        return "File Not Found"
    mtime = os.path.getmtime(filepath)
    dt = datetime.datetime.fromtimestamp(mtime)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    print(f"Model modified date: {get_mod_date(MODEL_PATH)}")
    print(f"intent_report.json modified date: {get_mod_date(INTENT_REPORT)}")
    print(f"DIETClassifier_report.json modified date: {get_mod_date(DIET_REPORT)}")
