# mcp-prestaciones-gt | Remote MCP Server

Guatemalan labor benefits calculator exposed as a **remote MCP server**. Unlike
a local server, the host does not launch it as a subprocess: it runs
independently in the cloud, and clients connect to it over HTTP.

The assignment allows the functionality to be trivial as long as it runs
remotely, so the interesting part here is not the calculation itself but the
transport: the same JSON-RPC 2.0 messages used by the stdio transport, now sent
inside HTTP POST requests.

## Tools

| Tool | What it calculates |
|---|---|
| `calcular_bono_14` | Bono 14, either in full or prorated based on the number of months worked |
| `calcular_aguinaldo` | Aguinaldo, including a breakdown of the two payments |
| `calcular_indemnizacion` | Severance pay for unjustified dismissal |
| `calcular_vacaciones` | Payment for unused vacation days |
| `costo_total_empleado` | The actual monthly cost of an employee |

## Run Locally

```bash
git clone https://github.com/JuanDsm04/mcp-prestaciones-gt.git
cd mcp-prestaciones-gt
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

The server listens at `http://0.0.0.0:8080/mcp`. To use a different port, run
`PORT=9000 python server.py`.

## Deploy to Render

Using Render's free plan:

1. Push this repository to GitHub (either public or private will work).
2. On [render.com](https://render.com), select **New → Web Service** and connect the repository.
3. Configure the service:
   - **Language**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
   - **Instance Type**: Free
4. Deploy. Once complete, Render will provide a URL such as
   `https://mcp-prestaciones-gt.onrender.com`.

**Note:** Your MCP endpoint is that URL plus `/mcp`. You do not need to configure
the port: Render injects the `PORT` environment variable, and the server reads
it. No additional environment variables or database are required.

### The Free Plan Spins Down

This is what causes the most problems during a demo. The service shuts down
after **15 minutes without traffic** and takes about **one minute** to wake up.
Because MCP's `initialize` request is the first message sent by the host, a cold
connection may exceed the client's timeout.

There are two ways to handle this, and it is best to use both:

- **Wake it up before the demo.** Open the URL in your browser and wait for it to
  respond. It will remain active for 15 minutes.
- **Increase the client's timeout.** Set the `timeout` field in the chatbot's
  server entry (see below).

## Connect It to a Host

In the chatbot's `config/mcp_servers.json` file:

```json
"prestaciones": {
  "enabled": true,
  "transport": "http",
  "description": "Custom remote MCP server for Guatemalan labor benefits.",
  "url": "https://mcp-prestaciones-gt.onrender.com/mcp",
  "headers": {},
  "timeout": 120
}
```

To test against the local instance instead of the deployed one, change the
`url` to `http://127.0.0.1:8080/mcp`.

## Specification

| Field | Value |
|---|---|
| Server name | `prestaciones-gt` |
| Protocol | Model Context Protocol over JSON-RPC 2.0 |
| Transport | Streamable HTTP |
| Endpoint | `POST /mcp` |
| SDK | MCP Python SDK v1 (`mcp>=1.27,<2`), `FastMCP` |
| Sessions | `stateless_http=True`: each request is independent |

The server is intentionally declared **stateless**. A stateful server preserves
state between requests and returns an `Mcp-Session-Id` that the client must send
with subsequent requests. This breaks when the platform restarts the container
or launches another instance, which is exactly what can happen on a free plan.
Without sessions, any instance can handle any request.

### Parameters

All amounts are expressed in quetzales, and every tool validates its input. A
negative salary or a number of months outside the accepted range returns an
error explaining what was expected rather than a raw exception.

| Tool | Parameters |
|---|---|
| `calcular_bono_14` | `salario_mensual` (required), `meses_trabajados` (1–12, default: 12) |
| `calcular_aguinaldo` | `salario_mensual` (required), `meses_trabajados` (1–12, default: 12) |
| `calcular_indemnizacion` | `salario_mensual` (required), `anios` (default: 0), `meses` (<12, default: 0) |
| `calcular_vacaciones` | `salario_mensual` (required), `dias_pendientes` (default: 15) |
| `costo_total_empleado` | `salario_mensual` (required) |

### Legal Constants

They are all grouped at the beginning of `calculos.py` so they can be updated
in one place if they change:

| Constant | Value |
|---|---|
| `TASA_IGSS_PATRONAL` | 12.67% |
| `TASA_IGSS_LABORAL` | 4.83% |
| `DIAS_VACACIONES_POR_ANIO` | 15 working days |

## Structure

```
mcp-prestaciones-gt/
├── calculos.py        Pure arithmetic, no dependencies
├── server.py          MCP registration and HTTP startup
├── requirements.txt
└── Dockerfile         Optional, for Cloud Run or Docker testing
```

`calculos.py` knows nothing about MCP, and `server.py` only registers tools, so
the calculations can be tested without starting the server.

## References

* [MCP transports](https://modelcontextprotocol.io/docs/learn/architecture)
* [MCP specification](https://modelcontextprotocol.io/specification/2025-06-18)
* [JSON-RPC 2.0](https://www.jsonrpc.org/)
