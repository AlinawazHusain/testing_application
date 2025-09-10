from datetime import datetime, timedelta, timezone


def get_utc_time():
    """
    Returns the current time in UTC without timezone information.

    This function fetches the current UTC time and removes the timezone
    info to ensure compatibility with timezone-naive datetime operations.

    Returns:
        datetime: A timezone-naive UTC datetime object.
    """
    
    return datetime.now(timezone.utc).replace(tzinfo=None)
    
  




def convert_utc_to_ist(utc_time: datetime) -> datetime:
    """
    Converts a given UTC datetime to Indian Standard Time (IST).

    IST is UTC+5:30, so this function adds 5 hours and 30 minutes
    to the provided UTC datetime.

    Args:
        utc_time (datetime): A timezone-naive or aware datetime object representing UTC time.

    Returns:
        datetime: The corresponding datetime in IST.
    """
    
    return utc_time + timedelta(hours=5, minutes=30)



def unix_to_utc(unix_timestamp: int = 1747161000000) -> str:

    timestamp_s = unix_timestamp / 1000

    dt_utc = datetime.fromtimestamp(timestamp_s)

    return dt_utc.isoformat()




def get_unix_timestamp(dt):
    return int(dt.timestamp() * 1000)




if __name__ == "__main__":
    print(get_unix_timestamp(get_utc_time()))