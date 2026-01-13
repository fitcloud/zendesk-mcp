"""
get_service_trends Tool

서비스별 문의 빈도 분석
"""

from collections import Counter

from pydantic import Field

from src.models.schemas import ServiceTrend, ServiceTrendsResult
from src.services.zendesk_client import ZendeskClient
from src.utils.date_utils import format_period_string, get_date_range
from src.utils.query_filters import get_exclusion_query

# 서비스 관련 태그 목록 (필터링용)
SERVICE_TAGS = {
    "monitoring",
    "cloud_infrastructure",
    "cloud infrastructure",
    "security",
    "devops",
    "database",
    "networking",
    "storage",
    "compute",
    "analytics",
    "machine_learning",
    "machine learning",
    "ai",
    "iot",
    "serverless",
    "containers",
    "kubernetes",
    "docker",
    "aws",
    "gcp",
    "azure",
    "datadog",
    "newrelic",
    "prometheus",
    "grafana",
}


async def get_service_trends(
    period_days: int = Field(
        default=90,
        description="검색 기간 (일 단위, 기본값: 90)",
    ),
    limit: int = Field(
        default=10,
        description="반환할 서비스 수 (기본값: 10)",
    ),
) -> ServiceTrendsResult:
    """
    서비스별 문의 빈도를 분석합니다.

    Args:
        period_days: 검색 기간 (기본값: 90일)
        limit: 반환할 서비스 수 (기본값: 10)

    Returns:
        ServiceTrendsResult: 서비스별 문의 트렌드
    """
    client = ZendeskClient()
    start_date, _ = get_date_range(period_days)

    # 기간 내 모든 티켓 검색
    query = f"type:ticket created>{start_date} {get_exclusion_query()}"
    tickets = await client.search_tickets(query)

    # 태그별 집계
    tag_counter: Counter[str] = Counter()
    for ticket in tickets:
        tags = client.extract_tags(ticket)
        for tag in tags:
            # 서비스 관련 태그만 집계 (소문자로 비교)
            tag_lower = tag.lower()
            if tag_lower in SERVICE_TAGS:
                tag_counter[tag] += 1

    # 상위 N개 추출
    top_services = tag_counter.most_common(limit)

    services = [
        ServiceTrend(category=tag, ticket_count=count)
        for tag, count in top_services
    ]

    return ServiceTrendsResult(
        period=format_period_string(period_days),
        total_tickets=len(tickets),
        services=services,
    )
