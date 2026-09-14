import requests
import json

API_KEY = "AIzaSyBOfQHV_9lPonsEZSSMRZrE0JXAXmoWWtQ"
CHANNEL_HANDLE = "@Apprendrelefrench"
BASE_URL = "https://www.googleapis.com/youtube/v3"




def chunk_list(items: list, size: int = 50) -> list[list]:
    
    return [items[i:i + size] for i in range(0, len(items), size)]


def get_video_details(video_ids: list[str]) -> list[dict]:
   
    all_videos = []
    batches = chunk_list(video_ids, 50)

    for i, batch in enumerate(batches, start=1):
        print(f"Fetching batch {i}/{len(batches)} ({len(batch)} videos)...")

        response = requests.get(f"{BASE_URL}/videos", params={
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(batch),
            "key": API_KEY
        })
        response.raise_for_status()
        data = response.json()

        all_videos.extend(data.get("items", []))

    return all_videos