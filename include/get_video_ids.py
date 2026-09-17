import os
import json
import requests
from dotenv import load_dotenv
from datetime import date

load_dotenv()

API_KEY = os.getenv("API_KEY")
CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE")


def get_channel_id(handle):
    url = f"https://www.googleapis.com/youtube/v3/channels?part=id,contentDetails&forHandle={handle}&key={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "items" in data and len(data["items"]) > 0:
        channel_id = data["items"][0]["id"]
        uploads_playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        return channel_id, uploads_playlist_id
    raise Exception("Chaine introuvable, veuillez vérifier le Handle de la chaine.")


def get_playlist_videos(playlist_id):
    video_ids = []
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "contentDetails",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": API_KEY,
    }

    while True:
        response = requests.get(base_url, params=params)
        data = response.json()
        for item in data.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break
        params["pageToken"] = next_page_token

    return video_ids


def get_videos_details(video_ids):
    base_url = "https://www.googleapis.com/youtube/v3/videos"
    formatted_data = []

    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(chunk),
            "key": API_KEY,
        }
        response = requests.get(base_url, params=params)
        data = response.json()

        for item in data.get("items", []):
            video_info = {
                "videoId": item["id"],
                "title": item["snippet"]["title"],
                "publishedAt": item["snippet"]["publishedAt"],
                "duration": item["contentDetails"]["duration"],
                "viewCount": item["statistics"].get("viewCount", "0"),
                "likeCount": item["statistics"].get("likeCount", "0"),
                "commentCount": item["statistics"].get("commentCount", "0"),
            }
            formatted_data.append(video_info)

    return formatted_data

from datetime import date


def save_ytdata(videos):
    data_dir = os.getenv("DATA_DIR", "data")
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, f"YTdata{date.today()}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=4)

    print(f"Succes ! {len(videos)} videos ont ete sauvegardees dans {file_path}")
    return file_path


def run_youtube_extraction(uploads_playlist):
    print("Extraction des donnees YouTube en cours...")

    v_ids = get_playlist_videos(uploads_playlist)
    youtube_data = get_videos_details(v_ids)

    return save_ytdata(youtube_data)


if __name__ == "__main__":
    channel_id, uploads_playlist_id = get_channel_id(CHANNEL_HANDLE)
    run_youtube_extraction(uploads_playlist_id)