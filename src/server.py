"""
Zendesk MCP Server

FastMCP 기반 MCP 서버 - Zendesk 티켓 데이터 분석
"""

import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from src.tools import (
    get_service_trends,
    get_ticket_details,
    get_top_agents,
    search_tickets,
    search_tickets_by_tag,
    search_tickets_with_keywords,
)

# 환경변수 로드
load_dotenv()

# FastMCP 서버 인스턴스 생성
mcp = FastMCP(
    name="zendesk-mcp",
    instructions="Zendesk 티켓 데이터 분석을 위한 MCP 서버입니다. 서비스 태그 기반 티켓 검색, 담당자 성과 분석, 트렌드 분석 등을 제공합니다.",
    version="1.0.0",
)

# Tools 등록
mcp.tool(search_tickets_by_tag)
mcp.tool(search_tickets)
mcp.tool(search_tickets_with_keywords)
mcp.tool(get_ticket_details)
mcp.tool(get_top_agents)
mcp.tool(get_service_trends)


def main():
    """MCP 서버 시작"""
    # 환경변수에서 설정 읽기 (기본값: HTTP 모드)
    transport = os.getenv("MCP_TRANSPORT", "http")
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    print(f"🚀 Starting Zendesk MCP Server...", flush=True)
    print(f"   Transport: {transport}", flush=True)
    print(f"   Host: {host}", flush=True)
    print(f"   Port: {port}", flush=True)

    mcp.run(transport=transport, host=host, port=port)


if __name__ == "__main__":
    main()
