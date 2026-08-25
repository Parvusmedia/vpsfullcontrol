# NocoDB MCP (base demos)

NocoDB ya expone un MCP HTTP en `https://mpa.parvusmedia.com/mcp/<endpoint-id>`.
Cloud Agents de Cursor **no soportan** `mcp-remote` ni SSE; hay que usar transporte **HTTP** y el header `xc-mcp-token`.

## Credencial temporal en git

`.cursor/mcp.json` incluye URL + `xc-mcp-token` para que el helper funcione sin secrets de Cloud.
Cuando lo sustituyas, rota el endpoint en NocoDB y deja el token solo en secrets:

- `NOCODB_MCP_URL` — URL completa del endpoint MCP
- `NOCODB_MCP_TOKEN` — valor de `xc-mcp-token`

## Cloud Agents (Cursor)

1. Abre [cursor.com/agents](https://cursor.com/agents) → dropdown **MCP**.
2. Añade un servidor **HTTP** (no stdio / no `npx mcp-remote`) con este JSON:

```json
{
  "mcpServers": {
    "NocoDB Base - demos": {
      "url": "https://mpa.parvusmedia.com/mcp/<endpoint-id>",
      "headers": {
        "xc-mcp-token": "<token>"
      }
    }
  }
}
```

3. En un Team, el admin puede publicarlo en **Dashboard → Integrations & MCP**.
4. Arranca un **agente nuevo**. Este run no hereda MCPs añadidos a mitad de conversación.

Tras conectarlo verás ~11 tools (`getBaseInfo`, `getTablesList`, `queryRecords`, etc.).

## Cursor Desktop

La config que genera NocoDB con `npx` + `mcp-remote` vale en el IDE local:

Cursor Settings (`⇧⌘J`) → MCP → Add Custom MCP.

En este repo también está `.cursor/mcp.json` en modo HTTP (Cloud Agents no soportan `mcp-remote`).

## Helper local (este repositorio)

Mismo patrón que n8n: el agente usa el script si el MCP nativo aún no está en el dashboard.

```bash
scripts/nocodb status
scripts/nocodb tools
scripts/nocodb base
scripts/nocodb tables
scripts/nocodb schema --table-id <id>
scripts/nocodb query --table-id <id> --page-size 10
scripts/nocodb call --name queryRecords --args '{"tableId":"..."}'
```

El helper nunca imprime el token. Escrituras (`createRecords`, `updateRecords`, `deleteRecords`) solo con `call` y confirmación explícita.

## Guardrails

- El helper nunca imprime el token. Tras rotarlo, quítalo de git y usa secrets.
- Preferir `scripts/nocodb` frente a curl ad-hoc.
- NocoDB MCP opera a nivel de **records**, no crea tablas ni campos.
