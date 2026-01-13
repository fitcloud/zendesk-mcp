"""
search_tickets Tool

자유 검색어로 티켓 검색
"""

from typing import Optional

from pydantic import Field

from src.models.schemas import SearchTicketsResult, TicketSummary
from src.services.zendesk_client import ZendeskClient
from src.utils.date_utils import get_date_range, parse_zendesk_datetime
from src.utils.query_filters import get_exclusion_query


async def search_tickets(
    query: str = Field(description="검색 쿼리"),
    status: Optional[str] = Field(
        default=None,
        description="티켓 상태 필터 (open, pending, hold, solved, closed)",
    ),
    period_days: Optional[int] = Field(
        default=None,
        description="검색 기간 (일 단위)",
    ),
    limit: int = Field(
        default=50,
        description="반환할 최대 티켓 수 (기본값: 50)",
    ),
) -> SearchTicketsResult:
    """
    자유 검색어로 티켓을 검색합니다.

    Args:
        query: 검색 쿼리 문자열
        status: 티켓 상태 필터 (선택)
        period_days: 검색 기간 (선택)
        limit: 반환할 최대 티켓 수

    Returns:
        SearchTicketsResult: 검색된 티켓 목록
    """
    client = ZendeskClient()

    # Zendesk 검색 쿼리 구성
    search_query = f"type:ticket {query} {get_exclusion_query()}"

    if status:
        search_query += f" status:{status}"

    if period_days:
        start_date, _ = get_date_range(period_days)
        search_query += f" created>{start_date}"

    tickets = await client.search_tickets(search_query)

    # 결과 변환 및 제한
    ticket_summaries = []
    for ticket in tickets[:limit]:
        ticket_summaries.append(
            TicketSummary(
                id=ticket.get("id"),
                subject=ticket.get("subject", ""),
                status=ticket.get("status", ""),
                priority=ticket.get("priority"),
                created_at=parse_zendesk_datetime(ticket.get("created_at")),
                company_name=client.extract_company_name(ticket),
            )
        )

    return SearchTicketsResult(
        query=query,
        total_count=len(tickets),
        tickets=ticket_summaries,
    )
