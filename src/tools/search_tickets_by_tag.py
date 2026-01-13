"""
search_tickets_by_tag Tool

서비스 분류 태그 기반으로 티켓을 검색하고 고객사별로 집계
"""

from pydantic import Field

from src.models.schemas import CompanyTicketCount, SearchByTagResult
from src.services.zendesk_client import ZendeskClient
from src.utils.date_utils import format_period_string, get_date_range
from src.utils.query_filters import get_exclusion_query


async def search_tickets_by_tag(
    service_tag: str = Field(
        description="검색할 서비스 분류 태그 (예: 'Monitoring', 'Cloud Infrastructure')"
    ),
    period_days: int = Field(
        default=365,
        description="검색 기간 (일 단위, 기본값: 365)",
    ),
) -> SearchByTagResult:
    """
    서비스 분류 태그 기반으로 티켓을 검색하고 고객사별로 집계합니다.

    키워드→태그 매핑은 LLM이 수행하며, 이 함수는 전달받은 태그로 검색만 수행합니다.

    Args:
        service_tag: 검색할 서비스 분류 태그
        period_days: 검색 기간 (기본값: 365일)

    Returns:
        SearchByTagResult: 태그별 고객사 집계 결과
    """
    client = ZendeskClient()
    start_date, _ = get_date_range(period_days)

    # Zendesk 검색 쿼리 구성
    query = f"type:ticket tags:{service_tag} created>{start_date} {get_exclusion_query()}"

    tickets = await client.search_tickets(query)

    # 요청 회사별 집계
    company_counts: dict[str, int] = {}
    for ticket in tickets:
        company_name = client.extract_company_name(ticket)
        if company_name and company_name != "Unknown":
            company_counts[company_name] = company_counts.get(company_name, 0) + 1

    # 결과 정렬 (티켓 수 내림차순)
    sorted_companies = sorted(
        [
            CompanyTicketCount(name=name, ticket_count=count)
            for name, count in company_counts.items()
        ],
        key=lambda x: x.ticket_count,
        reverse=True,
    )

    return SearchByTagResult(
        service_tag=service_tag,
        total_tickets=len(tickets),
        period=format_period_string(period_days),
        companies=sorted_companies,
    )
