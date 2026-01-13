"""
search_tickets_with_keywords Tool

키워드 기반으로 티켓을 검색하고 고객사별로 집계
(서비스 태그가 없는 과거 티켓 검색용)
"""

from pydantic import Field

from src.models.schemas import CompanyTicketCount, SearchByKeywordsResult
from src.services.zendesk_client import ZendeskClient
from src.utils.date_utils import format_period_string, get_date_range
from src.utils.query_filters import get_exclusion_query


async def search_tickets_with_keywords(
    keywords: list[str] = Field(
        description="검색할 키워드 목록 (예: ['Datadog', '모니터링', 'APM']). OR 조건으로 검색됩니다."
    ),
    period_days: int = Field(
        default=365,
        description="검색 기간 (일 단위, 기본값: 365)",
    ),
) -> SearchByKeywordsResult:
    """
    키워드 기반으로 티켓을 검색하고 고객사별로 집계합니다.

    서비스 태그가 설정되지 않은 과거 티켓을 검색할 때 유용합니다.
    Agent가 ISV 카테고리를 관련 키워드로 매핑한 후 이 도구를 호출합니다.

    Args:
        keywords: 검색할 키워드 목록 (OR 조건으로 검색)
        period_days: 검색 기간 (기본값: 365일)

    Returns:
        SearchByKeywordsResult: 키워드별 고객사 집계 결과
    """
    client = ZendeskClient()
    start_date, _ = get_date_range(period_days)

    # 키워드를 OR 조건으로 결합하여 Zendesk 검색 쿼리 구성
    # 예: "Datadog" OR "모니터링" OR "APM"
    keyword_query = " ".join(f'"{kw}"' for kw in keywords)
    query = f"type:ticket ({keyword_query}) created>{start_date} {get_exclusion_query()}"

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

    return SearchByKeywordsResult(
        keywords=keywords,
        total_tickets=len(tickets),
        period=format_period_string(period_days),
        companies=sorted_companies,
    )
