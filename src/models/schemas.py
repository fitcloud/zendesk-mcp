"""
Pydantic 모델 정의

MCP Tool 응답 및 내부 데이터 구조 정의
"""

import os
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field


# ============================================================
# 공통 모델
# ============================================================

# Zendesk 서브도메인 (티켓 URL 생성용)
ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN", "saltware")


class TicketInfo(BaseModel):
    """티켓 기본 정보"""

    id: int = Field(description="티켓 ID")
    subject: str = Field(description="티켓 제목")
    status: str = Field(description="티켓 상태")
    priority: Optional[str] = Field(default=None, description="우선순위")
    created_at: Optional[datetime] = Field(default=None, description="생성일시")
    company_name: Optional[str] = Field(default=None, description="요청 회사명")

    @computed_field
    @property
    def url(self) -> str:
        """티켓 URL"""
        return f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/agent/tickets/{self.id}"


class CompanyGroup(BaseModel):
    """고객사별 그룹 (티켓 포함)"""

    name: str = Field(description="회사명")
    ticket_count: int = Field(description="티켓 수")
    tickets: list[TicketInfo] = Field(description="해당 회사의 티켓 목록")


# ============================================================
# search_tickets 통합 결과 모델
# ============================================================


class SearchResult(BaseModel):
    """통합 검색 결과"""

    search_params: str = Field(description="검색 조건 요약")
    total_tickets: int = Field(description="총 티켓 수")
    period: str = Field(description="검색 기간")
    companies: list[CompanyGroup] = Field(
        description="회사별 그룹 (티켓 수 내림차순)"
    )


# ============================================================
# get_top_agents 관련 모델
# ============================================================


class AgentPerformance(BaseModel):
    """담당자 성과 정보"""

    name: str = Field(description="담당자 이름")
    email: Optional[str] = Field(default=None, description="담당자 이메일")
    solved_count: int = Field(description="해결한 티켓 수")


class TopAgentsResult(BaseModel):
    """담당자 순위 결과"""

    period: str = Field(description="검색 기간")
    agents: list[AgentPerformance] = Field(description="담당자 목록 (성과순)")


# ============================================================
# get_service_trends 관련 모델
# ============================================================


class ServiceTrend(BaseModel):
    """서비스 트렌드 정보"""

    category: str = Field(description="서비스 카테고리 (태그)")
    ticket_count: int = Field(description="티켓 수")


class ServiceTrendsResult(BaseModel):
    """서비스 트렌드 분석 결과"""

    period: str = Field(description="분석 기간")
    total_tickets: int = Field(description="총 티켓 수")
    services: list[ServiceTrend] = Field(description="서비스별 티켓 수 (내림차순)")


# ============================================================
# get_ticket_details 관련 모델
# ============================================================


class TicketDetails(BaseModel):
    """티켓 상세 정보"""

    id: int = Field(description="티켓 ID")
    subject: str = Field(description="티켓 제목")
    description: Optional[str] = Field(default=None, description="티켓 설명")
    status: str = Field(description="티켓 상태")
    priority: Optional[str] = Field(default=None, description="우선순위")
    created_at: Optional[datetime] = Field(default=None, description="생성일시")
    updated_at: Optional[datetime] = Field(default=None, description="수정일시")
    assignee_name: Optional[str] = Field(default=None, description="담당자 이름")
    requester_name: Optional[str] = Field(default=None, description="요청자 이름")
    company_name: Optional[str] = Field(default=None, description="요청 회사명")
    tags: list[str] = Field(default_factory=list, description="태그 목록")

    @computed_field
    @property
    def url(self) -> str:
        """티켓 URL"""
        return f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/agent/tickets/{self.id}"
