"""
Pydantic 모델 정의

MCP Tool 응답 및 내부 데이터 구조 정의
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# search_tickets_by_tag 관련 모델
# ============================================================


class CompanyTicketCount(BaseModel):
    """회사별 티켓 수"""

    name: str = Field(description="회사명")
    ticket_count: int = Field(description="티켓 수")


class SearchByTagResult(BaseModel):
    """태그 기반 검색 결과"""

    service_tag: str = Field(description="검색한 서비스 태그")
    total_tickets: int = Field(description="총 티켓 수")
    period: str = Field(description="검색 기간")
    companies: list[CompanyTicketCount] = Field(description="회사별 티켓 수 목록")


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


# ============================================================
# search_tickets 관련 모델
# ============================================================


class TicketSummary(BaseModel):
    """티켓 요약 정보"""

    id: int = Field(description="티켓 ID")
    subject: str = Field(description="티켓 제목")
    status: str = Field(description="티켓 상태")
    priority: Optional[str] = Field(default=None, description="우선순위")
    created_at: Optional[datetime] = Field(default=None, description="생성일시")
    company_name: Optional[str] = Field(default=None, description="요청 회사명")


class SearchTicketsResult(BaseModel):
    """티켓 검색 결과"""

    query: str = Field(description="검색 쿼리")
    total_count: int = Field(description="검색된 티켓 수")
    tickets: list[TicketSummary] = Field(description="티켓 목록")


# ============================================================
# search_tickets_with_keywords 관련 모델
# ============================================================


class SearchByKeywordsResult(BaseModel):
    """키워드 기반 검색 결과 (고객사별 집계)"""

    keywords: list[str] = Field(description="검색에 사용된 키워드 목록")
    total_tickets: int = Field(description="총 티켓 수")
    period: str = Field(description="검색 기간")
    companies: list[CompanyTicketCount] = Field(description="회사별 티켓 수 목록 (내림차순)")
