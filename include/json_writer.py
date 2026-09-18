import json
import os
from datetime import date


def save_videos_to_json(videos):
    data_dir = os.getenv("DATA_DIR", "data")
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.abspath(os.path.join(data_dir, f"YTdata{date.today()}.json"))

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=4)

    print(f"Succes ! {len(videos)} videos ont ete sauvegardees dans {file_path}")
    return file_path


def read_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)