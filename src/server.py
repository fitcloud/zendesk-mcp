"""
Zendesk MCP Server

FastMCP 기반 MCP 서버 - Zendesk 티켓 데이터 분석
"""

import os

import uvicorn
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.http import create_streamable_http_app
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

# JSON 응답용 앱 (Claude Desktop, Cursor 등 표준 클라이언트)
json_app = create_streamable_http_app(
    mcp,
    streamable_http_path="/",
    json_response=True,
)

# SSE 스트리밍용 앱 (SSE 전용 클라이언트)
sse_app = create_streamable_http_app(
    mcp,
    streamable_http_path="/",
    json_response=False,
)


async def health_check(request):
    """헬스체크 엔드포인트"""
    return JSONResponse({"status": "healthy", "server": "zendesk-mcp"})


# 통합 앱 - 엔드포인트별로 응답 형식 분리
app = Starlette(
    routes=[
        Route("/health", health_check),
        Mount("/mcp", app=json_app),   # JSON 응답: http://host:port/mcp
        Mount("/sse", app=sse_app),    # SSE 스트리밍: http://host:port/sse
    ]
)


def main():
    """MCP 서버 시작"""
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    print(f"🚀 Starting Zendesk MCP Server...", flush=True)
    print(f"   JSON Endpoint: http://{host}:{port}/mcp", flush=True)
    print(f"   SSE Endpoint:  http://{host}:{port}/sse", flush=True)
    print(f"   Health Check:  http://{host}:{port}/health", flush=True)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
