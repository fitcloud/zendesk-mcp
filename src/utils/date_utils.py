"""
날짜 유틸리티 함수들
"""

from datetime import datetime, timedelta


def get_date_range(period_days: int) -> tuple[str, str]:
    """
    현재 날짜 기준으로 기간 범위 계산

    Args:
        period_days: 기간 (일 단위)

    Returns:
        (시작일, 종료일) 튜플 (ISO 8601 형식: YYYY-MM-DD)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)

    return (
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
    )


def format_period_string(period_days: int) -> str:
    """
    기간을 사람이 읽기 쉬운 형식으로 변환

    Args:
        period_days: 기간 (일 단위)

    Returns:
        "YYYY-MM-DD ~ YYYY-MM-DD" 형식의 문자열
    """
    start_date, end_date = get_date_range(period_days)
    return f"{start_date} ~ {end_date}"


def parse_zendesk_datetime(datetime_str: str | None) -> datetime | None:
    """
    Zendesk API 날짜 문자열을 datetime 객체로 변환

    Args:
        datetime_str: ISO 8601 형식의 날짜 문자열 (예: "2025-01-07T10:30:00Z")

    Returns:
        datetime 객체 또는 None
    """
    if not datetime_str:
        return None

    try:
        # Zendesk는 ISO 8601 형식 사용
        return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
    except ValueError:
        return None
