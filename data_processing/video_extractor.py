import pandas as pd
import isodate
from datetime import datetime
def get_videos_ids(youtube,Playlist_id):
  request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId = Playlist_id,
            maxResults = 50)
  response = request.execute()

  videos_ids = []
  for i in range(len(response['items'])):
    videos_ids.append(response['items'][i]['contentDetails']['videoId'])
  if len(response['items']) > 50:
    next_page_token = response['nextPageToken']
    more_pages = True
  else:
    next_page_token = None
    more_pages = False
  while more_pages:
    if next_page_token is None:
      more_pages= False
    else:
      request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId = Playlist_id,
                maxResults = 50,
                pageToken = next_page_token)
      response = request.execute()
      for i in range(len(response['items'])):
        videos_ids.append(response['items'][i]['contentDetails']['videoId'])
      next_page_token = response.get('nextPageToken')

  return videos_ids

def get_video_details(youtube, video_ids,channel_id):
  all_video_stats = []
  all_video_dynamic_stats = []

  for i in range(0, len(video_ids),50):
    request = youtube.videos().list(
              part='snippet,statistics,contentDetails',
              id=','.join(video_ids[i:i+50]))
    response = request.execute()

    for video in response['items']:
      current_video_id = video.get('id')
      snippet = video.get('snippet', {})
      stats = video.get('statistics', {})
      content = video.get('contentDetails', {})
      duration_obj = isodate.parse_duration(content.get('duration', "PT0S"))
      formatted_duration = str(duration_obj)
      date = snippet.get('publishedAt', "")
      date = datetime.fromisoformat(date.replace("Z", "+00:00"))
      video_stats = dict(
          Video_id = current_video_id,
          Channel_id = channel_id,
          Title = snippet.get('title', "Unknown Title"),
          published_date = date, 
          Duration = formatted_duration,
          Thumbnail_url = snippet.get('thumbnails', {}).get('high', {}).get('url', "No Thumbnail")
      )
      all_video_stats.append(video_stats)

      video_dynamic_stats = dict(
        Video_id = current_video_id,
        Views = int(stats.get('viewCount', 0)),
        Likes = int(stats.get('likeCount', 0)),
        Comments = int(stats.get('commentCount', 0))
      )
      all_video_dynamic_stats.append(video_dynamic_stats)

      
  df_video_stats = pd.DataFrame(all_video_stats)
  df_video_dynamic_stats = pd.DataFrame(all_video_dynamic_stats)
  return df_video_stats,df_video_dynamic_stats
