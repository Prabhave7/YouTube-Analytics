from datetime import datetime
def get_channel_statistics(youtube, channel_id):
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_id
    )
    response = request.execute()
    
    # Check if items exist to avoid IndexErrors
    if not response.get('items'):
        return None

    item = response['items'][0]
    date = item['snippet']['publishedAt']
    date = datetime.fromisoformat(date.replace("Z", "+00:00"))

    data = {
        "Channel_id":channel_id,
        "Channel_name": item['snippet']['title'],
        "Description": item['snippet']['description'],
        "Subscriber_count": int(item['statistics']['subscriberCount']),
        "Video_count": int(item['statistics']['videoCount']),
        "View_count": int(item['statistics']['viewCount']),
        "Created_on": date,
        "Thumbnail": item['snippet']['thumbnails']['high']['url'],
        "Playlist_id": item['contentDetails']['relatedPlaylists']['uploads']
    }
    return data
