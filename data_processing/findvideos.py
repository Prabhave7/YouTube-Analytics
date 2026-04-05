import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("mysql+pymysql://root:$4562@localhost:3306/youtube")

def search_videos(keyword):
    query = text("""
        select v.title, v.publish_date, 
        ROUND(TIME_TO_SEC(v.duration)/60) AS duration, vs.views, vs.likes, vs.comments
        from videos v join video_statistics vs on v.video_id = vs.video_id 
        WHERE title LIKE :keyword
        ORDER BY duration DESC
    """)
    return pd.read_sql(query, engine,params={"keyword": f"%{keyword}%"})
