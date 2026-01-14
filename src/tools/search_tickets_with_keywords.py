"""
search_tickets_with_keywords Tool

키워드 기반으로 티켓을 검색하고 고객사별로 집계
(서비스 태그가 없는 과거 티켓 검색용)
"""

import asyncio

from pydantic import Field

from src.models.schemas import CompanyTicketCount, SearchByKeywordsResult
from src.services.zendesk_client import ZendeskClient
from src.utils.date_utils import format_period_string, get_date_range
from src.utils.query_filters import get_exclusion_query


def _build_single_keyword_query(
    field: str, keyword: str, start_date: str, exclusion: str
) -> str:
    """
    단일 키워드에 대한 Zendesk 검색 쿼리를 생성합니다.

    Args:
        field: 검색할 필드 (tags, subject, description)
        keyword: 검색할 키워드
        start_date: 검색 시작 날짜
        exclusion: 제외 조건 쿼리

    Returns:
        Zendesk 검색 쿼리 문자열
    """
    if field == "tags":
        # 태그는 공백을 하이픈으로 변환
        keyword_condition = f"tags:{keyword.lower().replace(' ', '-')}"
    else:
        keyword_condition = f"{field}:{keyword}"

    return f"type:ticket {keyword_condition} created>{start_date} {exclusion}"


def _merge_tickets(ticket_lists: list[list[dict]]) -> list[dict]:
    """
    여러 검색 결과를 합치고 중복을 제거합니다.

    Args:
        ticket_lists: 검색 결과 목록들

    Returns:
        중복이 제거된 티켓 목록
    """
    seen_ids: set[int] = set()
    merged: list[dict] = []

    for tickets in ticket_lists:
        for ticket in tickets:
            ticket_id = ticket.get("id")
            if ticket_id and ticket_id not in seen_ids:
                seen_ids.add(ticket_id)
                merged.append(ticket)

    return merged


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

    검색 전략:
    - 각 키워드별로 tags, subject, description 필드에서 개별 검색
    - 모든 검색 결과를 병합하고 중복 제거
    - 고객사별로 집계

    Args:
        keywords: 검색할 키워드 목록 (OR 조건으로 검색)
        period_days: 검색 기간 (기본값: 365일)

    Returns:
        SearchByKeywordsResult: 키워드별 고객사 집계 결과
    """
    client = ZendeskClient()
    start_date, _ = get_date_range(period_days)
    exclusion = get_exclusion_query()

    # Zendesk 검색 쿼리 구성
    # 참고: https://support.zendesk.com/hc/en-us/articles/4408886879258
    #
    # Zendesk 검색 특성:
    # - 같은 속성을 여러 번 사용해도 AND 로직으로 동작하는 경우가 있음
    # - 따라서 각 키워드별로 개별 검색 후 결과를 병합
    search_fields = ["tags", "subject", "description"]

    # 각 키워드 + 각 필드 조합에 대해 개별 쿼리 생성
    queries = []
    for keyword in keywords:
        for field in search_fields:
            queries.append(
                _build_single_keyword_query(field, keyword, start_date, exclusion)
            )

    # 병렬로 검색 수행
    search_tasks = [client.search_tickets(query) for query in queries]
    results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # 에러가 아닌 결과만 수집
    valid_results = [r for r in results if isinstance(r, list)]

    # 결과 병합 및 중복 제거
    tickets = _merge_tickets(valid_results)

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
