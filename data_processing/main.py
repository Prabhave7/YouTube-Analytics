import os
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from dotenv import load_dotenv
from sqlalchemy import create_engine
from googleapiclient.discovery import build
import extractor 
import video_extractor
import database
import queries
import plotly.express as px
import findvideos
import io
# import metrics_calculator
# import re
page_bg_img = """
<style>
[data-testid="stMain"]{
background-color:#8494FF;
background-size: cover;
}
[data-testid = "stToolbar"]{
background-color:#8494FF;
background-size: cover;
}
[data-testid = "stSidebar"]{ 
background: rgba(99, 103, 255, 0.6);
box-shadow: 2px 0 5px rgba(0,0,0,0.5);
}
[class="main-svg"]{
border-radius:5px;
# background-color:rgba(255, 219, 253, 0.1);
box-shadow: 0 10px 10px rgba(0, 0, 0, 0.3);
box-sizing: 1px;
}
.stVegaLiteChart {
  border-radius: 6px;
  box-shadow: 0 10px 10px rgba(0, 0, 0, 0.3);
  box-sizing: 1px;
  overflow: hidden;
}
section .stMainBlockContainer > div > div:nth-child(8) {
    # height:48px;
    border-radius: 6px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    overflow: hidden;
}
</style>
"""

load_dotenv()
api_key = os.getenv("API_KEY")

# YouTube API
youtube = build('youtube', 'v3', developerKey=api_key)

# # channel_id="UCHvDhwNuq-h2hZQRR6BwbLQ"

def display_dashboard(channel_id):
    st.title("YouTube Channel Analytics")
    ch_info = database.get_ch_info(channel_id)
    st.success(f"Channel Exists in database and have {ch_info['videos_count']:,} videos")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(ch_info['thumbnail_url'], width=200)
    with col2:
        st.header(ch_info['channel_name'])
        st.write(f"**Description:** {ch_info['description']}")
        st.caption(f"Created on: {ch_info['created_date']}")

    # Metrics Bar
    m1, m2, m3 ,m4= st.columns(4)
    m1.metric("Subscribers", f"{ch_info['subscribers']:,}")
    m2.metric("Total Videos", f"{ch_info['videos_count']:,}")
    m3.metric("Total Views", f"{ch_info['total_views']:,}")
    engagement_rate = queries.avg_engagement_rate(channel_id)
    m4.metric("Engagement Rate",f"{engagement_rate:.2f}%")

    st.divider()
    st.write(f"Displaying deep-dive metrics for {ch_info['channel_name']}...")

    selected = option_menu(
        menu_title=None,
        options=["View over Time","Top 10 videos","Monthly upload","View vs Engage","Heatmap","Multiline chart","Funnel chart"],
        default_index = 0,
        orientation ="horizontal",
        styles={
            "nav-link":{
                "font-size": "10px",
                "text-align":"left",
                "margin": "0px",
            },
            "nav-link-selected":{"background-color":"#6367FF"},
        }
    )
    if selected == "View over Time":
        st.subheader("Views over Time")
        plot_linechart(channel_id)
    if selected == "Top 10 videos":
        st.subheader("Top 10 Videos by Views")
        plot_videos_barchart(channel_id)
    if selected == "Monthly upload":
        st.subheader("Yearly Upload Distribution")
        plot_piechart(channel_id)
    if selected == "View vs Engage":
        st.subheader("Views vs Engagement")
        plot_scatter_chart(channel_id)

    if selected == "Heatmap":
        st.subheader("Upload Seasonality: Day of Week vs. Month of Year")
        plot_heat_map(channel_id)
    if selected == "Multiline chart":
        st.subheader("Views, Likes & Comments Over Time")
        plot_multiline_chart(channel_id)
        st.subheader("Monthly Views")
        plot_histogram(channel_id)
    if selected == "Funnel chart": 
        st.subheader("Funnel chart")
        plot_funnel_chart(channel_id)
    return True

def plot_linechart(channel_id):
    df = queries.monthly_views_by_publish_date(channel_id)
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values("month")
    st.line_chart(df.set_index("month"))
    return True

def plot_videos_barchart(channel_id):
    df_videos = queries.top_10_videos(channel_id)
    if not df_videos.empty:
        fig = px.bar(
        df_videos,
        x='views',
        y='title',
        orientation='h',
        # title="Top 10 Videos by View Count",
        labels={'views': 'Total Views', 'title': 'Video Title'},
        color='views',
        color_continuous_scale='Viridis'
    )
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'}, # highest views at the top
            showlegend=False,
            height=500
        )
        st.plotly_chart(fig,width='stretch')
    else:
        st.write("No video data found for this channel.")
    return True

def plot_scatter_chart(channel_id):
    df_scatter = queries.get_engagement_scatter_data(channel_id)
    df_scatter['engagement_rate'] = df_scatter['engagement_rate'].fillna(0)
    if not df_scatter.empty:
        fig = px.scatter(
            df_scatter,
            x="views",
            y="engagement_rate",
            hover_name="title",
            # title="Views vs. Engagement Rate",
            labels={
                "views": "Total Views",
                "engagement_rate": "Engagement Rate (%)"
            },
            size="engagement_rate",
            color="engagement_rate",
            color_continuous_scale="Viridis",
            template="plotly_white"
        )
        fig.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
        fig.update_xaxes(type="log") 
        st.plotly_chart(fig, width ='stretch')
        st.write(f"**Insight:** The highest engagement rate found is {df_scatter['engagement_rate'].max():.2f}%")
    else:
        st.info("No data available to generate scatter plot.")
    return True

def plot_piechart(channel_id):
    # Get list of unique years for the dropdown
    years_df = queries.years_for_dropdown(channel_id)
    year_options = ["All"] + years_df['year'].tolist()

    selected_year = st.selectbox("Select Year to View Upload Distribution", options=year_options)
    # Fetch data based on selection
    df_yearly = queries.get_yearly_upload_distribution(channel_id, selected_year)
    if not df_yearly.empty:
        title_suffix = f"in {selected_year}" if selected_year != "All" else "(All Time)"
        fig = px.pie(
            df_yearly, 
            values='uploads', 
            names='month', 
            title=f'Upload Distribution by Month {title_suffix}',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_traces(textinfo='percent+label', pull=[0.05] * len(df_yearly))
        st.plotly_chart(fig, width ='stretch')
    else:
        st.warning(f"No data available for {selected_year}.")
    return True

def plot_heat_map(channel_id):
    df_hm, m_order, d_order = queries.get_monthly_day_heatmap(channel_id)

    if not df_hm.empty:
        fig = px.density_heatmap(
            df_hm,
            x="Month",
            y="Day",
            z="Uploads",
            color_continuous_scale="Viridis",
            # title="Upload Seasonality: Day of Week vs. Month of Year",
            labels={'Month': 'Month', 'Day': 'Day of Week', 'Uploads': 'Total Videos'},
            category_orders={
                "Month": m_order, 
                "Day": d_order
            },
            text_auto=True # Displays numbers inside the heat squares
        )
        fig.update_layout(
            xaxis_title="Month of Year",
            yaxis_title="Day of Week",
            coloraxis_colorbar=dict(title="Uploads")
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No data found for this channel's posting history.")
    return True

def plot_histogram(channel_id):
    df = queries.monthly_views_by_publish_date(channel_id)
    fig = px.bar(
        df,
        x="month",
        y="total_views",
        color="total_views",
        color_continuous_scale="Viridis",
        labels={"total_views": "Total Views", "month": "Month"},
    )
    fig.update_layout(
        # title="Monthly Views by Publish Date",
        xaxis_title="Month",
        yaxis_title="Total Views",
        xaxis=dict(tickformat="%b %Y"),
    )
    st.plotly_chart(fig,width='stretch')
    return True

def plot_multiline_chart(channel_id):
    df = queries.views_likes_comments_overtime(channel_id)
    df_long = df.melt(
        id_vars="month",
        value_vars=["total_views", "total_likes", "total_comments"],
        var_name="Metric",
        value_name="Value"
    )

    fig = px.line(
        df_long,
        x="month",
        y="Value",
        color="Metric",
        markers=True,
        labels={
            "month": "Month",
            "Value": "Count",
            "Metric": "Metric Type"
        }
    )

    fig.update_layout(
        # title="Views, Likes & Comments Over Time",
        xaxis=dict(tickformat="%b %Y"),
        hovermode="x unified"
    )

    st.plotly_chart(fig, width='stretch')
    return True

def plot_funnel_chart(channel_id):
    df = queries.views_likes_comments_overtime(channel_id)
    funnel_df = pd.DataFrame({
        "Stage": ["Views", "Likes", "Comments"],
        "Value": [
            df["total_views"].sum(),
            df["total_likes"].sum(),
            df["total_comments"].sum()
        ]
    })

    fig = px.funnel(
        funnel_df,
        x="Value",
        y="Stage",
        color="Value",
        # color_continuous_scale="Viridis"
    )

    # fig.update_layout(title="Overall Engagement Funnel")
    st.plotly_chart(fig, width='stretch')
    return True

def enable_print_mode():
    st.markdown(
        """
        <style>
        @media print {
            section[data-testid="stSidebar"] {
                display: none;
            }
            header {
                display: none !important;
            }
            .stButton, .stDownloadButton {
                display: none !important;
            }
            .main .block-container {
                padding: 0 !important;
                margin: 0 !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Call the function at the top of your page
enable_print_mode()

# --- PAGE CONFIG ---
st.markdown(page_bg_img,unsafe_allow_html=True)
st.set_page_config(page_title="YouTube Analytics Hub", layout="wide")
page = st.sidebar.radio(
    "Navigation",
    ["Channel Analysis", "Channel Comparison","Search Videos"]
)

if page == "Channel Analysis":
    df_channels = database.get_recent_channels()
    # Sidebar Navigation UI
    st.sidebar.header("Configuration")
    channel_id = st.sidebar.text_input("Enter YouTube Channel ID", placeholder="UCxxxxxxxxxxxx")
    fetch_button = st.sidebar.button("Fetch Data")
    if fetch_button and channel_id and database.channel_exists(channel_id) is False:
        try:
            with st.spinner("Extracting data..."):
                channel_info = extractor.get_channel_statistics(youtube,channel_id)
                print(database.insert_channel(channel_info))
                video_ids = video_extractor.get_videos_ids(youtube,channel_info['Playlist_id'])
                df_vid_stat,df_vid_dyn_stat = video_extractor.get_video_details(youtube,video_ids,channel_id)
                print(database.insert_videos(df_vid_stat,df_vid_dyn_stat))
                st.success(f"Channel Successfully stored to database!")
                display_dashboard(channel_id)
        except Exception as e:
            st.error(f"An error occurred: {e}")
    st.sidebar.subheader("Select a channel to view details:")

    # Button for each channel
    for index, row in df_channels.iterrows():
        if st.sidebar.button(f"{row['channel_name']} ({row['subscribers']:,} subs) {row['channel_id']}", key=row['channel_id']):
            st.session_state['selected_channel'] = row['channel_id']

    # Main Content Area
    if 'selected_channel' in st.session_state:
        selected = st.session_state['selected_channel']
        channel_id = selected
        display_dashboard(channel_id)
    else:
        st.header("Welcome!")
        st.info("Please select a channel from the sidebar to begin.")

elif page == "Channel Comparison":
    st.title("Compare Multiple Channels")
    st.sidebar.title("Navigation & Filters")
    df_recent = database.get_recent_channels()
    if not df_recent.empty:
        id_to_name = dict(zip(df_recent['channel_id'], df_recent['channel_name']))

        selected_channel_ids = st.sidebar.multiselect(
            "Select Channels to Analyze",
            options=list(id_to_name.keys()),
            default=list(id_to_name.keys())[:1],
            format_func=lambda cid: f"{id_to_name[cid]} ({cid})"
        )
    
    if not selected_channel_ids:
        st.warning("Please select at least two channels from the sidebar.")
    else:
        is_comparison = len(selected_channel_ids) > 1

        st.subheader("Key Performance Indicators")
        cols = st.columns(len(selected_channel_ids) * 4 if is_comparison else 4)
        
        all_stats =[]
        for i, ch_id in enumerate(selected_channel_ids):
            # print(ch_id)
            stats = database.get_ch_info(ch_id)
            all_stats.append(stats)
            with st.container():
                st.markdown(stats['channel_name'])
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Subscribers", f"{stats['subscribers']:,}", delta="1.2%")
                m2.metric("Total Videos", f"{stats['videos_count']:,}")
                m3.metric("Total Views", f"{stats['total_views']:,}", delta="5.4%")
                # Engagement rate for m4 metric
                eng_df = queries.engagement_rate(ch_id)
                avg_eng = eng_df['engagement_rate'].mean()
                m4.metric("Avg Engagement", f"{avg_eng:.2f}%", delta="-0.5%")
        
        st.divider()
        df_leaderboard = pd.DataFrame(all_stats)
        st.header("🏆 Channel Leaderboard")
        tab1, tab2 = st.tabs(["Subscribers Rank", "Total Views Rank"])

        with tab1:
            # Sort and plot
            df_subs = df_leaderboard.sort_values("subscribers", ascending=False)
            st.bar_chart(data=df_subs, x="channel_name", y="subscribers", color="#EFC12A")

        with tab2:
            df_views = df_leaderboard.sort_values("total_views", ascending=False)
            st.bar_chart(data=df_views, x="channel_name", y="total_views", color="#29B5E8")

        st.divider()
        with st.container():
            charts_per_row = 2

            for i in range(0, len(selected_channel_ids), charts_per_row):
                row_ids = selected_channel_ids[i:i + charts_per_row]
                cols = st.columns(len(row_ids))

                for col, ch_id in zip(cols, row_ids):
                    with col:
                        plot_linechart(ch_id)
                        plot_videos_barchart(ch_id)
                        plot_scatter_chart(ch_id)
                        plot_piechart(ch_id)

        st.subheader("📥 Export Report")

        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_leaderboard.to_excel(writer, sheet_name='Leaderboard', index=False)
            eng_df.to_excel(writer, sheet_name='Summary', index=False)

        st.download_button(
            label="Download Multi-Sheet Report (Excel)",
            data=buffer.getvalue(),
            file_name="full_report.xlsx",
            mime="application/vnd.ms-excel"
        )

        # Convert DataFrame to CSV
        csv_data = df_leaderboard.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="Download Comparison Report (CSV)",
            data=csv_data,
            file_name="channel_comparison_report.csv",
            mime="text/csv",
            help="Press ctrl+v to save comparison report in pdf."
        )

elif page == "Search Videos":
    st.title("Video Searcher 🔎")
    st.set_page_config(layout="wide")

    # 1. Initialize Session State
    if "df_raw" not in st.session_state:
        st.session_state.df_raw = None
    if "page" not in st.session_state:
        st.session_state.page = 1

    keyword = st.text_input("Enter search keyword:")
    if st.button("Search") and keyword:
        df = findvideos.search_videos(keyword)
        # Using your sample data columns
        st.session_state.df_raw = df 
        st.session_state.page = 1 

    if st.session_state.df_raw is not None:
        # Create a copy for filtering
        df_filtered = st.session_state.df_raw.copy()

        # Pre-processing for filtering
        df_filtered['publish_date'] = pd.to_datetime(df_filtered['publish_date']).dt.date

        # --- SIDEBAR FILTERS ---
        st.sidebar.header("Filter Results")

        # Views Filter
        min_v, max_v = int(df_filtered['views'].min()), int(df_filtered['views'].max())
        v_range = st.sidebar.slider("Views", min_v, max_v, (min_v, max_v))
        
        # Duration Filter
        min_dur, max_dur = int(df_filtered['duration'].min()), int(df_filtered['duration'].max())
        dur_range = st.sidebar.slider("Duration (Minutes)", min_dur, max_dur, (min_dur, max_dur))
        
        # Date Filter
        min_d, max_d = df_filtered['publish_date'].min(), df_filtered['publish_date'].max()
        d_range = st.sidebar.date_input("Publish Date Range", [min_d, max_d])
        
        # Apply Filters
        df_filtered = df_filtered[
            (df_filtered['views'].between(v_range[0], v_range[1])) &
            (df_filtered['duration'].between(dur_range[0], dur_range[1]))
        ]
        if len(d_range) == 2:
            df_filtered = df_filtered[df_filtered['publish_date'].between(d_range[0], d_range[1])]

        # --- PAGINATION ---
        ROWS_PER_PAGE = 20
        total_rows = len(df_filtered)
        total_pages = max(1, (total_rows - 1) // ROWS_PER_PAGE + 1)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅ Previous") and st.session_state.page > 1:
                st.session_state.page -= 1
                st.rerun()
        with col2:
            st.write(f"### Page {st.session_state.page} of {total_pages}")
        with col3:
            if st.button("Next ➡") and st.session_state.page < total_pages:
                st.session_state.page += 1
                st.rerun()

        # Display Data
        start = (st.session_state.page - 1) * ROWS_PER_PAGE
        end = start + ROWS_PER_PAGE
        # Dropping the helper column before showing the user
        st.data_editor(df_filtered.drop(columns=['duration']).iloc[start:end], width='stretch')

        st.write(f"Showing {len(df_filtered)} matching videos.")

# Date Range Filter
# st.sidebar.subheader("Date Range")
# date_range = st.sidebar.date_input("Select Date Range", [])