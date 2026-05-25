# MCP Server

Baby Buddy has a [Model Context Protocol](https://modelcontextprotocol.io) (MCP)
server that lets AI assistants — like Claude Desktop — log and query Baby Buddy
data using natural language. Ask your assistant to record a feeding, check last
night's sleep, or summarize the day, and it reads and writes through Baby Buddy's
[API](api.md).

The server lives in its own repository:
[**babybuddy/babybuddy-mcp**](https://github.com/babybuddy/babybuddy-mcp).

## What it can do

The server exposes tools grouped by domain, covering create, list, update, and
delete operations where applicable:

- Children
- Diaper changes
- Feedings
- Sleep
- Pumping
- Tummy times
- Timers
- Measurements (weight, height, head circumference, BMI, temperature)
- Notes (and tags)

## Setup

The MCP server connects to a running Baby Buddy instance and authenticates with an
API token. Generate a token from the User Settings page of the user the assistant
should act as (see [Authentication](api.md#authentication)).

!!! note
Installation and configuration — including Docker (`http` transport) and Claude
Desktop (`stdio` transport) setups and the `BABYBUDDY_URL` / `BABYBUDDY_TOKEN`
environment variables — are documented in the
[babybuddy/babybuddy-mcp](https://github.com/babybuddy/babybuddy-mcp) repository.
Because the server is maintained there, that repository is the source of truth
for setup steps.
