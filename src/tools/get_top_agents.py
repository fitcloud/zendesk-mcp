"""
get_top_agents Tool

기간 내 가장 많은 티켓을 해결한 담당자 조회
"""

from pydantic import Field

from src.models.schemas import AgentPerformance, TopAgentsResult
from src.services.zendesk_client import ZendeskClient
from src.utils.date_utils import format_period_string, get_date_range
from src.utils.query_filters import get_exclusion_query


async def get_top_agents(
    period_days: int = Field(
        default=30,
        description="검색 기간 (일 단위, 기본값: 30)",
    ),
    limit: int = Field(
        default=10,
        description="반환할 담당자 수 (기본값: 10)",
    ),
) -> TopAgentsResult:
    """
    기간 내 가장 많은 티켓을 해결한 담당자를 조회합니다.

    Args:
        period_days: 검색 기간 (기본값: 30일)
        limit: 반환할 담당자 수 (기본값: 10)

    Returns:
        TopAgentsResult: 담당자 성과 순위
    """
    client = ZendeskClient()
    start_date, _ = get_date_range(period_days)

    # 해결된 티켓 검색
    query = f"type:ticket status:solved solved>{start_date} {get_exclusion_query()}"
    tickets = await client.search_tickets(query)

    # 담당자별 해결 티켓 수 집계
    agent_counts: dict[int, int] = {}
    for ticket in tickets:
        assignee_id = ticket.get("assignee_id")
        if assignee_id:
            agent_counts[assignee_id] = agent_counts.get(assignee_id, 0) + 1

    # 상위 N명 추출
    sorted_agents = sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    # 담당자 정보 조회
    agent_ids = [agent_id for agent_id, _ in sorted_agents]
    users = await client.get_users_batch(agent_ids)

    # 결과 구성
    agents = []
    for agent_id, count in sorted_agents:
        user = users.get(agent_id, {})
        agents.append(
            AgentPerformance(
                name=user.get("name", f"User #{agent_id}"),
                email=user.get("email"),
                solved_count=count,
            )
        )

    return TopAgentsResult(
        period=format_period_string(period_days),
        agents=agents,
    )
