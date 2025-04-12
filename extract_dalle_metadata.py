import json
import os
from datetime import datetime, timezone

# Set your base path here for repo usage
BASE_DIR = os.path.abspath(".")
JSON_PATH = os.path.join(BASE_DIR, "conversations.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "dalle_metadata.json")
IMAGE_DIR = "dalle-generations"

# Helper to parse UNIX epoch timestamps
def parse_time(ts):
    try:
        return datetime.fromtimestamp(ts, timezone.utc).isoformat()
    except:
        return None

def extract_dalle_metadata():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build a lookup of all webp files from the actual folder
    existing_files = {}
    for fname in os.listdir(os.path.join(BASE_DIR, IMAGE_DIR)):
        if fname.endswith(".webp") and fname.startswith("file-"):
            short_id = fname.split(".webp")[0].split("-")[1]  # file-<short_id>-<uuid>.webp
            existing_files[short_id] = fname

    images = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("author", {}).get("role") == "tool" and node.get("content", {}).get("parts"):
                for part in node["content"]["parts"]:
                    if isinstance(part, dict) and part.get("asset_pointer", "").startswith("file-service://file-"):
                        meta = part.get("metadata", {}).get("dalle", {})
                        file_id = part["asset_pointer"].split("file-service://")[-1]
                        short_id = file_id.split("-")[1]
                        matched_filename = existing_files.get(short_id)
                        if matched_filename:
                            images.append({
                                "file_id": file_id,
                                "filename": matched_filename,
                                "path": os.path.join(IMAGE_DIR, matched_filename),
                                "prompt": meta.get("prompt"),
                                "seed": meta.get("seed"),
                                "gen_id": meta.get("gen_id"),
                                "timestamp": parse_time(node.get("create_time"))
                            })
        for value in (node.values() if isinstance(node, dict) else node):
            if isinstance(value, (dict, list)):
                walk(value)

    walk(data)

    # Sort by timestamp ascending (oldest first)
    images.sort(key=lambda x: x.get("timestamp") or "")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(images, f, indent=2, ensure_ascii=False)

    print(f"✅ Extracted {len(images)} DALL·E images to {OUTPUT_PATH}")

if __name__ == "__main__":
    extract_dalle_metadata()
