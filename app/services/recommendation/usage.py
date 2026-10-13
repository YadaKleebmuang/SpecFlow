"""Shared usage classification for recommendations and analytics.

For mixed workloads, the first specific workload wins. General office/study
words are considered only if no specific workload is present. Unknown input
retains the historical gaming default.
"""

import re

USAGE_LABELS = {
    "gaming": "เล่นเกม",
    "graphic": "กราฟิก",
    "video_editing": "ตัดต่อวิดีโอ",
    "programming": "เขียนโปรแกรม",
    "office": "ออฟฟิศ",
}

CORE_ALLOCATIONS = {
    "gaming": {"gpu": .40, "cpu": .30, "ram": .15, "storage": .15},
    "graphic": {"gpu": .35, "cpu": .30, "ram": .20, "storage": .15},
    "video_editing": {"gpu": .25, "cpu": .35, "ram": .25, "storage": .15},
    "programming": {"gpu": .15, "cpu": .40, "ram": .25, "storage": .20},
    "office": {"gpu": .15, "cpu": .35, "ram": .25, "storage": .25},
}
INTEGRATED_ALLOCATION = {"gpu": 0.0, "cpu": .45, "ram": .25, "storage": .30}

_KEYWORDS = {
    "gaming": ("เล่นเกม", "เกมส์", "เกม", "gaming", "game", "games", "fps", "moba"),
    "graphic": ("กราฟิก", "กราฟิค", "วาดรูป", "ออกแบบ", "เขียนแบบ", "โมเดล",
                "เรนเดอร์", "graphic", "graphics", "design", "render", "3d",
                "photoshop", "illustrator", "autocad", "blender", "sketchup", "lightroom", "cad"),
    "video_editing": ("ตัดต่อ", "วิดีโอ", "วีดีโอ", "สตรีม", "ทำเพลง", "video_editing",
                      "video", "editing", "edit", "stream", "streaming", "premiere",
                      "after effects", "after effect", "davinci"),
    "programming": ("เขียนโปรแกรม", "เขียนโค้ด", "พัฒนาโปรแกรม", "พัฒนาเว็บ", "ทำเว็บ",
                    "programming", "coding", "code", "develop", "developer", "development",
                    "python", "javascript", "docker", "ide", "vm", "vms", "compile"),
    "office": ("ทั่วไป", "ออฟฟิศ", "พิมพ์งาน", "เอกสาร", "เรียน", "เทรด", "ดูหนัง",
               "ฟังเพลง", "สำนักงาน", "บัญชี", "ศึกษา", "office", "study", "learn",
               "trade", "excel", "word", "powerpoint", "youtube", "netflix", "surf", "browse"),
}


def classify_usage(usage: str) -> str:
    text = (usage or "").lower().strip()
    # LINE preprocessing inserts spaces between Thai tokens. Rejoin Thai words
    # while preserving English token boundaries (e.g. "decode" versus "code").
    text = re.sub(r"(?<=[\u0e00-\u0e7f])\s+(?=[\u0e00-\u0e7f])", "", text)
    if text in USAGE_LABELS:
        return text
    matches = []
    for category, keywords in _KEYWORDS.items():
        for keyword in keywords:
            pattern = re.escape(keyword)
            if keyword.isascii():
                pattern = r"(?<![a-z0-9_])" + pattern + r"(?![a-z0-9_])"
            match = re.search(pattern, text)
            if match:
                matches.append((match.start(), category))
    specific = [match for match in matches if match[1] != "office"]
    return min(specific or matches)[1] if matches else "gaming"
