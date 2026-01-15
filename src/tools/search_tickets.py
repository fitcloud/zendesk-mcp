"""
search_tickets Tool (통합)

키워드, 태그 기반 티켓 검색을 하나로 통합.
고객사별로 그룹핑하여 티켓 정보와 링크를 함께 제공합니다.
"""

import asyncio
from typing import Optional

from pydantic import Field

from src.models.schemas import CompanyGroup, SearchResult, TicketInfo
from src.services.zendesk_client import ZendeskClient
from src.utils.date_utils import format_period_string, get_date_range, parse_zendesk_datetime
from src.utils.query_filters import COMPANY_FIELD_ID, get_exclusion_query


def _build_keyword_queries(
    keywords: list[str], start_date: str, exclusion: str
) -> list[str]:
    """
    키워드 목록에 대한 검색 쿼리들을 생성합니다.
    각 키워드별로 tags, subject, description 필드에서 검색.
    """
    queries = []
    search_fields = ["tags", "subject", "description"]

    for keyword in keywords:
        for field in search_fields:
            if field == "tags":
                keyword_condition = f"tags:{keyword.lower().replace(' ', '-')}"
            else:
                keyword_condition = f"{field}:{keyword}"

            queries.append(
                f"type:ticket {keyword_condition} created>{start_date} {exclusion}"
            )

    return queries


def _merge_tickets(ticket_lists: list[list[dict]]) -> list[dict]:
    """여러 검색 결과를 합치고 중복을 제거합니다."""
    seen_ids: set[int] = set()
    merged: list[dict] = []

    for tickets in ticket_lists:
        for ticket in tickets:
            ticket_id = ticket.get("id")
            if ticket_id and ticket_id not in seen_ids:
                seen_ids.add(ticket_id)
                merged.append(ticket)

    return merged


def _group_by_company(
    tickets: list[dict], client: ZendeskClient, limit_per_company: int = 10
) -> list[CompanyGroup]:
    """
    티켓을 고객사별로 그룹핑합니다.

    Args:
        tickets: 티켓 목록
        client: Zendesk 클라이언트
        limit_per_company: 각 고객사당 최대 티켓 수

    Returns:
        고객사별 그룹 목록 (티켓 수 내림차순)
    """
    company_tickets: dict[str, list[TicketInfo]] = {}
    company_total_count: dict[str, int] = {}

    for ticket in tickets:
        company_name = client.extract_company_name(ticket)
        if not company_name or company_name == "Unknown":
            continue

        # 총 티켓 수 카운트
        company_total_count[company_name] = company_total_count.get(company_name, 0) + 1

        ticket_info = TicketInfo(
            id=ticket.get("id"),
            subject=ticket.get("subject", ""),
            status=ticket.get("status", ""),
            priority=ticket.get("priority"),
            created_at=parse_zendesk_datetime(ticket.get("created_at")),
            company_name=company_name,
        )

        if company_name not in company_tickets:
            company_tickets[company_name] = []

        # 각 고객사당 티켓 수 제한 (샘플링)
        if len(company_tickets[company_name]) < limit_per_company:
            company_tickets[company_name].append(ticket_info)

    # 그룹 생성 및 정렬
    groups = [
        CompanyGroup(
            name=name,
            ticket_count=company_total_count[name],  # 실제 전체 티켓 수
            tickets=tickets_list,  # 샘플 티켓 (limit_per_company개)
        )
        for name, tickets_list in company_tickets.items()
    ]

    # 티켓 수 내림차순 정렬
    groups.sort(key=lambda x: x.ticket_count, reverse=True)

    return groups


async def search_tickets(
    keywords: Optional[list[str]] = Field(
        default=None,
        description="검색 키워드 목록 (OR 조건 검색, tags/subject/description에서 검색. 예: ['cloudwatch', 'datadog'])",
    ),
    tags: Optional[list[str]] = Field(
        default=None,
        description="태그 필터 (예: ['monitoring', 'cloud-infrastructure'])",
    ),
    status: Optional[str] = Field(
        default=None,
        description="티켓 상태 필터 (open, pending, hold, solved, closed)",
    ),
    company: Optional[str] = Field(
        default=None,
        description="고객사명 필터 (Zendesk 커스텀 필드 기반 정확한 매칭). "
                    "회사명으로 검색 시 반드시 이 필드 사용. keywords와 함께 사용 가능. "
                    "예: company='이지샵', keywords=['cloudwatch']",
    ),
    period_days: int = Field(
        default=90,
        description="검색 기간 (일 단위, 기본값: 90)",
    ),
    limit: int = Field(
        default=500,
        description="최대 티켓 수 (기본값: 500)",
    ),
) -> SearchResult:
    """
    티켓을 검색하고 고객사별로 그룹핑하여 반환합니다.

    **사용 예시:**
    - 키워드로 검색: keywords=["cloudwatch"]
    - 여러 키워드 OR 검색: keywords=["cloudwatch", "datadog", "모니터링"]
    - 특정 회사의 키워드 검색: company="이지샵", keywords=["cloudwatch"]
    - 특정 회사의 모든 티켓: company="이지샵"
    - 태그 기반 검색: tags=["aws-support"]

    **중요:** 회사명으로 필터링할 때는 반드시 company 파라미터를 사용하세요.

    검색 조건 (keywords, tags, company 중 하나 이상 필수):
    - keywords: 키워드 목록으로 OR 조건 검색 (tags, subject, description 필드)
    - tags: 특정 태그가 있는 티켓만 검색
    - company: 특정 고객사의 티켓만 검색 (커스텀 필드 기반 정확한 매칭)

    결과:
    - 고객사별로 그룹핑하여 티켓 목록과 URL 제공
    - 티켓 수 기준 내림차순 정렬
    - 각 고객사당 최대 10개 티켓 샘플 제공

    Args:
        keywords: 검색 키워드 목록 (OR 조건)
        tags: 태그 필터
        status: 티켓 상태 필터
        company: 고객사명 필터
        period_days: 검색 기간
        limit: 최대 티켓 수

    Returns:
        SearchResult: 고객사별 그룹핑된 검색 결과
    """
    # 검색 조건 검증 (company도 단독 검색 가능)
    if not any([keywords, tags, company]):
        return SearchResult(
            search_params="검색 조건 없음",
            total_tickets=0,
            period=format_period_string(period_days),
            companies=[],
        )

    client = ZendeskClient()
    start_date, _ = get_date_range(period_days)
    exclusion = get_exclusion_query()

    # 공통 쿼리 조건 생성
    def build_common_conditions() -> str:
        """공통 조건 (기간, 상태, 고객사, 제외조건) 생성"""
        parts = [f"created>{start_date}", exclusion]
        if status:
            parts.append(f"status:{status}")
        if company:
            # 요청 회사 커스텀 필드로 검색
            parts.append(f"custom_field_{COMPANY_FIELD_ID}:{company}")
        return " ".join(parts)

    common_conditions = build_common_conditions()
    all_tickets: list[dict] = []

    # 1. 키워드 검색 처리 (병렬)
    if keywords:
        queries = _build_keyword_queries(keywords, start_date, exclusion)

        # 상태/고객사 필터 추가
        additional = ""
        if status:
            additional += f" status:{status}"
        if company:
            additional += f" custom_field_{COMPANY_FIELD_ID}:{company}"
        if additional:
            queries = [f"{q}{additional}" for q in queries]

        search_tasks = [client.search_tickets(q) for q in queries]
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        valid_results = [r for r in results if isinstance(r, list)]
        keyword_tickets = _merge_tickets(valid_results)
        all_tickets.extend(keyword_tickets)

    # 2. 태그 검색 처리
    if tags:
        for tag in tags:
            normalized_tag = tag.lower().replace(" ", "-")
            tag_query = f"type:ticket tags:{normalized_tag} {common_conditions}"
            tickets = await client.search_tickets(tag_query)
            all_tickets.extend(tickets)

    # 3. company만 지정된 경우 (keywords, tags 없이)
    if company and not any([keywords, tags]):
        company_query = f"type:ticket {common_conditions}"
        tickets = await client.search_tickets(company_query)
        all_tickets.extend(tickets)

    # 중복 제거
    all_tickets = _merge_tickets([all_tickets])

    # 제한 적용
    all_tickets = all_tickets[:limit]

    # 고객사별 그룹핑
    company_groups = _group_by_company(all_tickets, client)

    # 검색 조건 요약 생성
    search_parts = []
    if keywords:
        search_parts.append(f"keywords={keywords}")
    if tags:
        search_parts.append(f"tags={tags}")
    if status:
        search_parts.append(f"status={status}")
    if company:
        search_parts.append(f"company='{company}'")
    search_params = ", ".join(search_parts) if search_parts else "전체"

    return SearchResult(
        search_params=search_params,
        total_tickets=len(all_tickets),
        period=format_period_string(period_days),
        companies=company_groups,
    )
