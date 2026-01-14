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


def _build_field_query(
    field: str, keywords: list[str], start_date: str, exclusion: str
) -> str:
    """
    특정 필드에 대한 Zendesk 검색 쿼리를 생성합니다.

    Args:
        field: 검색할 필드 (tags, subject, description)
        keywords: 검색할 키워드 목록
        start_date: 검색 시작 날짜
        exclusion: 제외 조건 쿼리

    Returns:
        Zendesk 검색 쿼리 문자열
    """
    # 같은 필드를 여러 번 사용하면 OR 조건으로 동작
    # 예: subject:cloudwatch subject:monitoring
    if field == "tags":
        # 태그는 공백을 하이픈으로 변환
        keyword_conditions = " ".join(
            f"tags:{kw.lower().replace(' ', '-')}" for kw in keywords
        )
    else:
        keyword_conditions = " ".join(f"{field}:{kw}" for kw in keywords)

    return f"type:ticket {keyword_conditions} created>{start_date} {exclusion}"


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
    - tags, subject, description 필드에서 각각 검색
    - 서로 다른 필드 간에는 OR 연산이 불가하므로 별도 검색 후 결과 병합
    - 동일 티켓 중복 제거

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
    # - 같은 속성을 여러 번 사용하면 OR 로직으로 동작
    # - 서로 다른 속성 간에는 AND 로직이 기본
    # - 따라서 tags, subject, description을 각각 검색하고 결과를 병합
    search_fields = ["tags", "subject", "description"]

    # 각 필드에 대해 병렬로 검색 수행
    queries = [
        _build_field_query(field, keywords, start_date, exclusion)
        for field in search_fields
    ]

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
