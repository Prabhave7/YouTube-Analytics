import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("mysql+pymysql://root:$4562@localhost:3306/youtube")

def engagement_rate(channel_id):
    query = text("""
        SELECT title,
        ROUND((CAST(vs.likes + vs.comments AS decimal)*100 / NULLIF(vs.views,0)),2) AS engagement_rate
        FROM videos join video_statistics vs on videos.video_id = vs.video_id 
        where videos.channel_id = :id;
    """)
    return pd.read_sql(query, engine,params={"id": channel_id})

def avg_views_per_vid(channel_id):
    query = text("""
        SELECT AVG(vs.views) AS avg_views
        FROM videos v JOIN video_statistics vs
        ON v.video_id = vs.video_id
        where v.channel_id = :id;
    """)
    return pd.read_sql(query, engine,params={"id": channel_id})

def subs_to_view_ratio(channel_id):
    query = text("""
        SELECT (CAST(c.subscribers as dec)/ NULLIF(c.total_views,0)) AS subs_to_view_ratio
        FROM channels c
        where c.channel_id = :id ;
    """)
    return pd.read_sql(query, engine,params={"id": channel_id})

def vid_performance(channel_id):
    query = text("""
                 SELECT v.title,
                vs.views,
                ((vs.views - MIN(vs.views) OVER (PARTITION BY v.channel_id)) * 10.0
                    / NULLIF(MAX(vs.views) OVER (PARTITION BY v.channel_id) - MIN(vs.views) OVER (PARTITION BY v.channel_id), 0)
                ) AS performance
                FROM videos v
                JOIN video_statistics vs ON v.video_id = vs.video_id
                WHERE v.channel_id = :id;
    """)
    return pd.read_sql(query, engine,params={"id": channel_id})

def optimal_posting_time(channel_id):
    query = text("""
                SELECT EXTRACT(HOUR FROM v.publish_date) AS posting_hour,
                AVG(vs.views) AS avg_views
                FROM videos v
                where v.channel_id = :id
                JOIN video_statistics vs ON v.video_id = vs.video_id
                GROUP BY posting_hour
                ORDER BY avg_views DESC;
    """)
    return pd.read_sql(query, engine,params={"id": channel_id})

def performance_benchmark(channel_id):
    query = text("""
                SELECT v.title,
                vs.views,
                AVG(vs.views) OVER (PARTITION BY v.channel_id) AS channel_avg_views,
                vs.views - AVG(vs.views) OVER (PARTITION BY v.channel_id) AS performance
                FROM videos v
                JOIN video_statistics vs ON v.video_id = vs.video_id
                WHERE v.channel_id = :id;
    """)
    return pd.read_sql(query, engine,params={"id": channel_id})