import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("mysql+pymysql://root:$4562@localhost:3306/youtube")

def top_10_videos(channel_id):
    query = text("""
        SELECT title, views
        FROM videos join video_statistics on videos.video_id = video_statistics.video_id
        where videos.channel_id = :id
        ORDER BY video_statistics.views DESC
        LIMIT 10 ;
    """)
    return pd.read_sql(query, engine,params={"id": channel_id})

def avg_video_duration(channel_id):
    query = text("""
        SELECT c.channel_name,
        SEC_TO_TIME(AVG(TIME_TO_SEC(duration))) AS average_duration
        FROM videos join channels c on videos.channel_id = c.channel_id
        WHERE videos.channel_id = :id;
    """)
    return pd.read_sql(query, engine,params={"id": channel_id})

def engagement_rate(channel_id):
    query = text("""
        SELECT title,
        (CAST(vs.likes + vs.comments AS decimal)*100 / NULLIF(vs.views,0)) AS engagement_rate
        FROM videos join video_statistics vs on videos.video_id = vs.video_id 
        where videos.channel_id = :id;
    """)
    return pd.read_sql(query, engine,params={"id": channel_id})

def highest_engagement_videos(channel_id):
    query = text("""
        SELECT title,
        (CAST(vs.likes + vs.comments AS decimal)*100 / NULLIF(vs.views,0)) AS engagement_rate
        FROM videos join video_statistics vs on videos.video_id = vs.video_id 
        where videos.channel_id = :id
        ORDER BY engagement_rate DESC
        LIMIT 10;
    """)
    return pd.read_sql(query, engine,params={"id": channel_id})

def avg_engagement_rate(channel_id):
    query = text("""
        SELECT
        AVG(CAST(vs.likes + vs.comments AS decimal)*100 / NULLIF(vs.views,0)) AS avg_engagement_rate
        FROM videos join video_statistics vs on videos.video_id = vs.video_id 
        where videos.channel_id = :id
        GROUP BY videos.channel_id;
    """)
    df = pd.read_sql(query, engine, params={"id": channel_id})
    
    # Extract the value from the first row, first column
    return df.iloc[0, 0] if not df.empty else 0.0
    # return pd.read_sql(query, engine,params={"id": channel_id})

def posting_frequency(channel_id):
    query = text("""
        SELECT v.publish_date
        FROM videos v
        WHERE v.channel_id = :id
        ORDER By v.publish_date desc;
    """)
    df = pd.read_sql(query, engine,params={"id": channel_id})
    df["publish_date"] = pd.to_datetime(df["publish_date"])
    return df

def monthly_upload_trends(channel_id):
    query = text("""
        SELECT 
        DATE_FORMAT(publish_date, '%Y-%m-01') AS month, 
        COUNT(*) AS uploads 
        FROM videos WHERE channel_id = :id
        GROUP BY month 
        ORDER BY month 
        LIMIT 0, 1000;
    """)
    return pd.read_sql(query, engine,params={"id": channel_id})

def get_yearly_upload_distribution(channel_id, selected_year):
    # If "All Years" is selected, we remove the year filter
    year_filter = "AND YEAR(publish_date) = :year" if selected_year != "All" else ""
    
    query = text(f"""
        SELECT 
            DATE_FORMAT(publish_date, '%M') AS month, -- Get month name (January, February...)
            COUNT(*) AS uploads 
        FROM videos 
        WHERE channel_id = :id 
        {year_filter}
        GROUP BY month 
        ORDER BY FIELD(month, 'January', 'February', 'March', 'April', 'May', 'June', 
                             'July', 'August', 'September', 'October', 'November', 'December');
    """)
    
    params = {"id": channel_id}
    if selected_year != "All":
        params["year"] = selected_year
        
    return pd.read_sql(query, engine, params=params)

def years_for_dropdown(channel_id):
    return pd.read_sql(
        text("SELECT DISTINCT YEAR(publish_date) as year FROM videos WHERE channel_id = :id ORDER BY year DESC"),
        engine, params={"id": channel_id}
    )

def monthly_views_by_publish_date(channel_id):
    query = text("""
        SELECT 
        DATE_FORMAT(v.publish_date, '%Y-%m') AS month,
        SUM(vs.views) AS total_views
        FROM videos v join video_statistics vs
        WHERE v.channel_id = :id
        GROUP BY month
        ORDER BY MIN(v.publish_date);
    """)
    
    df = pd.read_sql(query, engine, params={"id": channel_id})
    df["month"] = pd.to_datetime(df["month"])
    df["month"] = df["month"].dt.strftime("%b %Y")
    
    return df

def get_engagement_scatter_data(channel_id):
    query = text("""
        SELECT v.title,vs.views,
        (CAST(vs.likes + vs.comments AS decimal)*100 / NULLIF(vs.views,0)) AS engagement_rate
        FROM videos v join video_statistics vs on v.video_id = vs.video_id 
        where v.channel_id = :id
        ORDER BY engagement_rate DESC;
    """)
    return pd.read_sql(query, engine, params={"id": channel_id})

def get_monthly_day_heatmap(channel_id):
    # Reuse function to get the base dataframe
    df = posting_frequency(channel_id)
    
    # Month and Day Names
    df["Month"] = df["publish_date"].dt.month_name()
    df["Day"] = df["publish_date"].dt.day_name()
    
    month_order = [
        'January', 'February', 'March', 'April', 'May', 'June', 
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    day_order = [
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]
    
    # Group data
    heatmap_df = df.groupby(["Month", "Day"]).size().reset_index(name="Uploads")
    
    return heatmap_df, month_order, day_order

def views_likes_comments_overtime(channel_id):
    query = text("""
        SELECT 
        DATE_FORMAT(v.publish_date, '%Y-%m') AS month,
        SUM(vs.views) AS total_views, SUM(vs.likes) AS total_likes, SUM(vs.comments)AS total_comments
        FROM videos v join video_statistics vs
        WHERE v.channel_id = :id
        GROUP BY month
        ORDER BY MIN(v.publish_date);
    """)
    
    df = pd.read_sql(query, engine, params={"id": channel_id})
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values("month")
    return df

# print(top_10_videos("UCHvDhwNuq-h2hZQRR6BwbLQ"))
# print(avg_video_duration("UCHvDhwNuq-h2hZQRR6BwbLQ"))
# print(avg_engagement_rate("UCHvDhwNuq-h2hZQRR6BwbLQ"))
# print(highest_engagement_videos("UCHvDhwNuq-h2hZQRR6BwbLQ"))
# print(posting_frequency("UCHvDhwNuq-h2hZQRR6BwbLQ"))
# print(monthly_upload_trends("UCHvDhwNuq-h2hZQRR6BwbLQ"))