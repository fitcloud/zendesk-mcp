# Zendesk MCP Server

Model Context Protocol (MCP) server for Zendesk Ticket Analytics

Zendesk 티켓 데이터를 활용하여 AI Agent가 고객 지원 관련 인사이트를 제공할 수 있도록 하는 MCP 서버입니다.

## Features

- **통합 티켓 검색**: 키워드, 태그, 고객사, 자유검색을 하나의 도구로 통합
- **고객사별 그룹핑**: 검색 결과를 고객사별로 자동 집계
- **티켓 링크 제공**: 각 티켓에 Zendesk 링크 포함
- **티켓 상세 조회**: 특정 티켓의 상세 정보 확인
- **담당자 성과 분석**: 기간 내 티켓 해결 담당자 순위
- **서비스 트렌드 분석**: 서비스별 문의 빈도 분석

## Prerequisites

### Environment Variables

- `ZENDESK_SUBDOMAIN` (Required): Zendesk 서브도메인
- `ZENDESK_EMAIL` (Required): Zendesk API 사용자 이메일
- `ZENDESK_API_TOKEN` (Required): Zendesk API 토큰

## Installation

### Docker Run

```bash
docker run -d \
  --name zendesk-mcp \
  -p 8000:8000 \
  -e ZENDESK_SUBDOMAIN=your-subdomain \
  -e ZENDESK_EMAIL=your-email@example.com \
  -e ZENDESK_API_TOKEN=your-api-token \
  public.ecr.aws/saltware/zendesk-mcp:latest
```

### Claude Desktop / Cursor

mcp.json 또는 mcp_settings.json에 추가:

```json
{
  "mcpServers": {
    "zendesk": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "--interactive",
        "-e", "ZENDESK_SUBDOMAIN=your-subdomain",
        "-e", "ZENDESK_EMAIL=your-email@example.com",
        "-e", "ZENDESK_API_TOKEN=your-api-token",
        "public.ecr.aws/saltware/zendesk-mcp:latest"
      ]
    }
  }
}
```

### Streamable HTTP Mode

HTTP 모드로 실행 시 다음과 같이 연결:

```json
{
  "mcpServers": {
    "zendesk": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Basic Usage

Example prompts:

- Datadog에 관심있을만한 고객사를 찾아줘
- 이지샵 고객사의 최근 티켓을 보여줘
- CloudWatch 키워드로 관심 고객사를 검색해줘
- 이번 달 티켓 해결 실적이 가장 좋은 담당자는 누구야?
- 최근 서비스별 문의 트렌드를 분석해줘

## Tools

### search_tickets

티켓을 검색하고 고객사별로 그룹핑하여 반환합니다. 각 티켓에는 Zendesk 링크가 포함됩니다.

```
search_tickets(
    keywords: list[str] = None,  # 키워드 목록 (OR 검색)
    tags: list[str] = None,      # 태그 필터
    company: str = None,         # 고객사 필터 (단독 사용 가능)
    status: str = None,          # 상태 필터
    period_days: int = 90,       # 검색 기간
    limit: int = 500             # 최대 티켓 수
)
```

> keywords, tags, company 중 하나 이상 필수

### get_ticket_details

특정 티켓의 상세 정보를 조회합니다.

```
get_ticket_details(ticket_id: int)
```

### get_top_agents

기간 내 가장 많은 티켓을 해결한 담당자를 조회합니다.

```
get_top_agents(period_days: int = 30, limit: int = 10)
```

### get_service_trends

서비스별 문의 빈도를 분석합니다.

```
get_service_trends(period_days: int = 90, limit: int = 10)
```

## Health Check

```bash
curl http://localhost:8000/health
```

## License

MIT License
