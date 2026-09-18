# meta-ads-mcp

MCP server (stdio) for Meta Marketing API.

## Setup

```bash
cp .env.example .env
# Set META_ACCESS_TOKEN in .env or Cursor Environment secrets
npm install && npm run build
```

## Run

```bash
npm start
```

Cursor: see [`docs/META_ADS_CURSOR.md`](../docs/META_ADS_CURSOR.md) and [`.cursor/mcp.json`](../.cursor/mcp.json).

## Tests

```bash
./scripts/smoke-read.sh
```
