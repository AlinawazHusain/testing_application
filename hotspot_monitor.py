import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, select
from datetime import datetime, timedelta
import pytz
# --- DB Setup ---
DATABASE_URL = "postgresql://dbmasteruser:2,Q*dU?xN7?8HD,t4K}gdFVeCTg(8!vW@ls-af2a1a18f5a6c9575bc39b94c15945068dfbfb00.cr0oymg4up2y.ap-south-1.rds.amazonaws.com:5432/Avaronn_PRODUCTION"
engine = create_engine(DATABASE_URL)
metadata = MetaData()
hotspot_route = Table("hotspot_routes", metadata, autoload_with=engine)
# --- Load Data ---
def fetch_hotspot_data():
    with engine.connect() as conn:
        stmt = select(hotspot_route)
        result = conn.execute(stmt)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    # Convert to IST
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True).dt.tz_convert('Asia/Kolkata')
    df['reached_hotspot_timestamp'] = pd.to_datetime(df['reached_hotspot_timestamp'], utc=True).dt.tz_convert('Asia/Kolkata')
    df['got_trip_at'] = pd.to_datetime(df['got_trip_at'], utc=True).dt.tz_convert('Asia/Kolkata')
    # Derived columns
    df['date'] = df['created_at'].dt.date
    df['time_to_reach'] = (df['reached_hotspot_timestamp'] - df['created_at']).dt.total_seconds() / 60
    df['wait_time_at_hotspot'] = (df['got_trip_at'] - df['reached_hotspot_timestamp']).dt.total_seconds() / 60
    df = df[df['driver_uuid'].notnull()]
    return df
# --- Daily Summary ---
def compute_daily_summary(df):
    summary = df.groupby(['driver_uuid', 'date']).agg(
        total_hotspot_requests=('id', 'count'),
        hotspot_reached=('reached_hotspot', 'sum'),
        trips_got=('got_trip', 'sum'),
        avg_time_to_reach=('time_to_reach', 'mean'),
        avg_wait_time=('wait_time_at_hotspot', 'mean'),
        first_request=('created_at', 'min'),
        last_request=('created_at', 'max')
    ).reset_index()
    return summary
# --- Nudge Detection Logic ---
def detect_nudges(df):
    df = df.sort_values(['driver_uuid', 'created_at'])
    df['idle_duration_after_reach'] = (
        df['got_trip_at'] - df['reached_hotspot_timestamp']
    ).dt.total_seconds() / 60
    df['should_nudge'] = (df['reached_hotspot'] == True) & (
        df['got_trip'].isnull() | (df['idle_duration_after_reach'] > 20)
    )
    nudges = []
    for driver_id, group in df.groupby('driver_uuid'):
        for idx, row in group.iterrows():
            if row['should_nudge']:
                next_requests = group[group['created_at'] > row['reached_hotspot_timestamp']]
                if next_requests.empty:
                    nudges.append({
                        "driver_uuid": row['driver_uuid'],
                        "nudge_at": row['reached_hotspot_timestamp'] + timedelta(minutes=20),
                        "reason": "Idle >20 min after reaching hotspot, no new request",
                        "original_request_at": row['created_at'],
                        "reached_hotspot_at": row['reached_hotspot_timestamp']
                    })
    return pd.DataFrame(nudges)
# --- Daily Run Function ---
def run_daily_hotspot_monitor():
    df = fetch_hotspot_data()
    summary = compute_daily_summary(df)
    nudges = detect_nudges(df)
    # Save or process as needed
    today = datetime.now().date()
    summary.to_csv(f"hotspot_summary_{today}.csv", index=False)
    nudges.to_csv(f"nudges_to_send_{today}.csv", index=False)
    print(f":white_check_mark: Daily hotspot monitor complete for {today}.")
if __name__ == "__main__":
    run_daily_hotspot_monitor()