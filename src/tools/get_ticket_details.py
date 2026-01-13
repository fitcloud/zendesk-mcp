"""
get_ticket_details Tool

특정 티켓의 상세 정보 조회
"""

from pydantic import Field

from src.models.schemas import TicketDetails
from src.services.zendesk_client import ZendeskClient
from src.utils.date_utils import parse_zendesk_datetime


async def get_ticket_details(
    ticket_id: int = Field(description="Zendesk 티켓 ID"),
) -> TicketDetails:
    """
    특정 티켓의 상세 정보를 조회합니다.

    Args:
        ticket_id: Zendesk 티켓 ID

    Returns:
        TicketDetails: 티켓 상세 정보
    """
    client = ZendeskClient()

    # 티켓 조회
    ticket = await client.get_ticket(ticket_id)

    # 담당자 및 요청자 정보 조회
    assignee_name = None
    requester_name = None

    user_ids = []
    if ticket.get("assignee_id"):
        user_ids.append(ticket["assignee_id"])
    if ticket.get("requester_id"):
        user_ids.append(ticket["requester_id"])

    if user_ids:
        users = await client.get_users_batch(user_ids)
        if ticket.get("assignee_id"):
            assignee = users.get(ticket["assignee_id"], {})
            assignee_name = assignee.get("name")
        if ticket.get("requester_id"):
            requester = users.get(ticket["requester_id"], {})
            requester_name = requester.get("name")

    return TicketDetails(
        id=ticket.get("id"),
        subject=ticket.get("subject", ""),
        description=ticket.get("description"),
        status=ticket.get("status", ""),
        priority=ticket.get("priority"),
        created_at=parse_zendesk_datetime(ticket.get("created_at")),
        updated_at=parse_zendesk_datetime(ticket.get("updated_at")),
        assignee_name=assignee_name,
        requester_name=requester_name,
        company_name=client.extract_company_name(ticket),
        tags=client.extract_tags(ticket),
    )
