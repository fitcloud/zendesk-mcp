"""
Zendesk MCP Server

FastMCP 기반 MCP 서버 - Zendesk 티켓 데이터 분석
"""

import os

import uvicorn
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

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

# Streamable HTTP 앱 (JSON 응답)
mcp_app = mcp.http_app(
    path="/",
    json_response=True,
)


async def health_check(request):
    """헬스체크 엔드포인트"""
    return JSONResponse({"status": "healthy", "server": "zendesk-mcp"})


# 메인 앱 - lifespan 전달 필수!
app = Starlette(
    routes=[
        Route("/health", health_check),
        Mount("/mcp", app=mcp_app),
    ],
    lifespan=mcp_app.lifespan,  # FastMCP lifespan 전달
)


def main():
    """MCP 서버 시작"""
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    print(f"🚀 Starting Zendesk MCP Server...", flush=True)
    print(f"   Endpoint: http://{host}:{port}/mcp", flush=True)
    print(f"   Health:   http://{host}:{port}/health", flush=True)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
