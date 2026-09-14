
CHANNEL_HANDLE = "@Apprendrelefrench"
API_KEY = "AIzaSyBOfQHV_9lPonsEZSSMRZrE0JXAXmoWWtQ"
PLAYLIST_ID = "UUpHM28yYMzkq193ZDJSEPiQ"

BASE_URL = "https://www.googleapis.com/youtube/v3"

import requests
import json


def get_video_ids(playlist_id):

    url = f"{BASE_URL}/playlistItems"

    video_ids = []
    page_token = None
    page = 1

    while True:

        params = {
            "playlistId": playlist_id,
            "part": "snippet",
            "maxResults": 50,
            "key": API_KEY
        }

        if page_token:
            params["pageToken"] = page_token

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        print(f"Page {page}: {len(data['items'])} videos")

        for item in data["items"]:

            video_id = item["snippet"]["resourceId"]["videoId"]

            video_ids.append(video_id)

        page_token = data.get("nextPageToken")

        print("Total collected:", len(video_ids))

        if not page_token:
            break

        page += 1

    return video_ids

