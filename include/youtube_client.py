import requests
from airflow.models import Variable


def get_channel_id(handle):
    api_key = Variable.get("API_KEY")
    url = f"https://www.googleapis.com/youtube/v3/channels?part=id,contentDetails&forHandle={handle}&key={api_key}"
    response = requests.get(url)
    data = response.json()

    if "items" in data and len(data["items"]) > 0:
        channel_id = data["items"][0]["id"]
        uploads_playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        return channel_id, uploads_playlist_id
    raise Exception("Chaine introuvable, veuillez vérifier le Handle de la chaine.")


def get_playlist_videos(playlist_id):
    api_key = Variable.get("API_KEY")
    video_ids = []
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "contentDetails",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": api_key,
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
    api_key = Variable.get("API_KEY")
    base_url = "https://www.googleapis.com/youtube/v3/videos"
    formatted_data = []

    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(chunk),
            "key": api_key,
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