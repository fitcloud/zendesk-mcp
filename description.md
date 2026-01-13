# Zendesk MCP Server

Model Context Protocol (MCP) server for Zendesk Ticket Analytics

Zendesk 티켓 데이터를 활용하여 AI Agent가 고객 지원 관련 인사이트를 제공할 수 있도록 하는 MCP 서버입니다.

## Features

- 서비스 태그 기반 검색: 서비스 분류 태그로 티켓 검색 및 고객사별 집계
- 키워드 기반 검색: 키워드로 티켓 검색 (태그 없는 과거 티켓 지원)
- 자유 검색: 자유 검색어로 티켓 검색
- 티켓 상세 조회: 특정 티켓의 상세 정보 확인
- 담당자 성과 분석: 기간 내 티켓 해결 담당자 순위
- 서비스 트렌드 분석: 서비스별 문의 빈도 분석

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

- 최근 90일간 모니터링 관련 문의가 많은 고객사를 찾아줘
- Datadog, Prometheus, 관제 키워드로 관심 고객사를 검색해줘
- 이번 달 티켓 해결 실적이 가장 좋은 담당자는 누구야?
- 최근 서비스별 문의 트렌드를 분석해줘

## Tools

### search_tickets_by_tag

서비스 분류 태그 기반으로 티켓을 검색하고 고객사별로 집계합니다.

```
search_tickets_by_tag(service_tag: str, period_days: int = 365)
```

### search_tickets_with_keywords

키워드 기반으로 티켓을 검색하고 고객사별로 집계합니다. 서비스 태그가 없는 과거 티켓 검색에 유용합니다.

```
search_tickets_with_keywords(keywords: list[str], period_days: int = 365)
```

### search_tickets

자유 검색어로 티켓을 검색합니다.

```
search_tickets(query: str, status: str = None, period_days: int = None, limit: int = 50)
```

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
