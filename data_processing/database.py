from sqlalchemy import create_engine ,text
import pandas as pd
import mysql.connector

conn = mysql.connector.connect(host = 'localhost',username = 'root',password = '$4562', database = 'youtube')
my_cursor = conn.cursor()

DATABASE_URL = "mysql+pymysql://root:$4562@localhost:3306/youtube"
engine = create_engine(DATABASE_URL)

def channel_exists(channel_id):
  query = text("SELECT EXISTS(SELECT 1 FROM channels WHERE channel_id = :id)")
  # pd.read_sql returns a DataFrame
  result = pd.read_sql(query, engine, params={"id": channel_id})
  exists = result.iloc[0, 0]
  if exists:
      print("Channel exists in database")
      return True
  else:
      print("Channel doesn't exist in database, need to extract by API call")
      return False

def insert_channel(data):
  df_data = pd.DataFrame([data])

  df_data = df_data.rename(columns={
    "Channel_id" : "channel_id",
    "Channel_name" :"channel_name",
    "Description":"description",
    "Subscriber_count": "subscribers",
    "Video_count": "videos_count",
    "View_count": "total_views",
    "Created_on": "created_date",
    "Thumbnail":"thumbnail_url",
    "Playlist_id":"playlist_id"
  })
  #print(df_data)

  df_data.to_sql("channels", engine, if_exists="append", index=False)
  print("connection succesfully created to channels")
  return True

def update_channel(channel_data):
  try:
    query = text("""
          UPDATE channels 
          SET subscribers = :sub_count, 
              videos_count = :vid_count, 
              total_views = :view_count 
          WHERE channel_id = :cid
      """)
      
    with engine.begin() as conn:  # .begin() commits the changes
      conn.execute(query, {
          "sub_count": channel_data["Subscriber_count"],
          "vid_count": channel_data["Video_count"],
          "view_count": channel_data["View_count"],
          "cid": channel_data["Channel_id"]
      })
    print("Successfully updated channel:")
  except Exception as e:
    print(f"NO need of updation: {e}")

def insert_videos(df_video_stats,df_video_dynamic_stats):
  df_video_stats = df_video_stats.rename(columns={
    "Video_id" : "video_id",
    "Channel_id" :"channel_id",
    "Title":"title",
    "published_date": "publish_date",
    "Duration": "duration",
    "Thumbnail_url": "thumbnail_url"
  })

  df_video_stats.to_sql("videos", engine, if_exists="append", index=False)
  print("connection succesfully created to videos")

  df_video_dynamic_stats = df_video_dynamic_stats.rename(columns={
    "Video_id" : "video_id",
    "Views" :"views",
    "Likes":"likes",
    "Comments": "comments"
  })
  # print(df_video_stats,df_video_dynamic_stats)
  df_video_dynamic_stats.to_sql("video_statistics", engine, if_exists="append", index=False)
  print("connection succesfully created to video_statistics")

  return True

def get_ch_info(channel_id):
  query = text("""select thumbnail_url,channel_name,description,created_date,subscribers,videos_count,total_views from channels where channel_id = :id""")
  result = pd.read_sql(query, engine, params={"id": channel_id})
  if not result.empty:
      return result.iloc[0].to_dict()
  else:
      return None

def get_recent_channels():
  query = text("""SELECT DISTINCT channel_name,subscribers,channel_id FROM channels ORDER BY subscribers DESC LIMIT 5""")
  return pd.read_sql(query,engine)