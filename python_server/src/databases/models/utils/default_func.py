import datetime
from zoneinfo import ZoneInfo


def aware_now() -> datetime.datetime:
    """タイムゾーン "aware" な現在時刻を返す (local tz)"""
    return datetime.datetime.now(tz=ZoneInfo("Asia/Tokyo"))


def local_now() -> datetime.datetime:
    """sqlalchemy の default func に渡す用"""
    return aware_now()
