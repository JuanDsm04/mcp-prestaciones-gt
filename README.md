# mcp-prestaciones-gt — servidor MCP remoto

Calculadora de prestaciones laborales de Guatemala expuesta como **servidor MCP
remoto**. A diferencia de un servidor local, no lo lanza el anfitrión como
subproceso: corre en la nube por su cuenta y los clientes se conectan por HTTP.

Proyecto para **CC3067 Redes**, Universidad del Valle de Guatemala (Proyecto 1,
requisito 7: *crear un servidor MCP que se ejecute de forma remota*).

```
   Anfitrión MCP (chatbot)                    Nube (Render)
            |                                       |
            |  POST /mcp  ── JSON-RPC 2.0 ──────>   |
            |  <────────── 200 + respuesta ──────   |
            |         HTTPS / TCP / IP              |
```

El enunciado permite que la funcionalidad sea trivial siempre que se ejecute de
forma remota, así que lo interesante aquí no es el cálculo sino el transporte:
los mismos mensajes JSON-RPC 2.0 del transporte stdio, ahora dentro de peticiones
HTTP POST.

## Herramientas

| Herramienta | Qué calcula |
|---|---|
| `calcular_bono_14` | Bono 14, completo o proporcional a los meses trabajados |
| `calcular_aguinaldo` | Aguinaldo, con el desglose de los dos pagos |
| `calcular_indemnizacion` | Indemnización por despido injustificado |
| `calcular_vacaciones` | Pago de vacaciones no gozadas |
| `costo_total_empleado` | Lo que cuesta realmente un empleado al mes |

`costo_total_empleado` es la más útil: suma salario, provisiones mensuales de
Bono 14, aguinaldo y vacaciones, y la cuota patronal del IGSS. El salario por sí
solo subestima el costo real en alrededor de un 33%.

## Correrlo en local

```bash
git clone https://github.com/JuanDsm04/mcp-prestaciones-gt.git
cd mcp-prestaciones-gt

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python server.py
```

Queda escuchando en `http://0.0.0.0:8080/mcp`. Para usar otro puerto,
`PORT=9000 python server.py`.

## Desplegarlo en Render

Render tiene plan gratuito sin tarjeta de crédito. Los pasos:

1. Sube este repositorio a GitHub (público o privado, ambos sirven).
2. En [render.com](https://render.com), **New → Web Service** y conecta el repo.
3. Configura:
   - **Language**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
   - **Instance Type**: Free
4. Deploy. Al terminar te da una URL como
   `https://mcp-prestaciones-gt.onrender.com`.

Tu endpoint MCP es esa URL más `/mcp`.

No hay que configurar el puerto: Render inyecta la variable `PORT` y el servidor
la lee. Tampoco hacen falta variables de entorno ni base de datos.

### El plan gratuito duerme

Es lo que más problemas da en una demo. El servicio se apaga tras **15 minutos
sin tráfico** y tarda alrededor de **un minuto** en despertar. Como el `initialize`
de MCP es lo primero que manda el anfitrión, una conexión en frío puede exceder el
tiempo de espera del cliente.

Dos formas de manejarlo, y conviene hacer las dos:

- **Despiértalo antes de la demo.** Abre la URL en el navegador y espera a que
  responda. Queda activo 15 minutos.
- **Sube el tiempo de espera del cliente.** En el registro del chatbot, el campo
  `timeout` (ver abajo).

## Conectarlo a un anfitrión

En `config/mcp_servers.json` del chatbot:

```json
"prestaciones": {
  "enabled": true,
  "transport": "http",
  "description": "Servidor MCP remoto propio: prestaciones laborales de Guatemala.",
  "url": "https://mcp-prestaciones-gt.onrender.com/mcp",
  "headers": {},
  "timeout": 120
}
```

Para probar contra la instancia local en lugar de la desplegada, cambia la `url`
a `http://127.0.0.1:8080/mcp`.

## Especificación

| Campo | Valor |
|---|---|
| Nombre del servidor | `prestaciones-gt` |
| Protocolo | Model Context Protocol sobre JSON-RPC 2.0 |
| Transporte | Streamable HTTP |
| Endpoint | `POST /mcp` |
| SDK | MCP Python SDK v1 (`mcp>=1.27,<2`), `FastMCP` |
| Sesiones | `stateless_http=True`: cada petición es independiente |

El servidor se declara **stateless** a propósito. Un servidor con sesión guarda
estado entre peticiones y devuelve un `Mcp-Session-Id` que el cliente debe
repetir; eso se rompe cuando la plataforma reinicia el contenedor o levanta otra
instancia, que es justo lo que hace un plan gratuito. Sin sesión, cualquier
instancia puede atender cualquier petición.

### Parámetros

Todos los montos van en quetzales y todas las herramientas validan su entrada.
Un salario negativo o unos meses fuera de rango devuelven un error explicando qué
se esperaba, no una excepción cruda.

| Herramienta | Parámetros |
|---|---|
| `calcular_bono_14` | `salario_mensual` (requerido), `meses_trabajados` (1-12, por defecto 12) |
| `calcular_aguinaldo` | `salario_mensual` (requerido), `meses_trabajados` (1-12, por defecto 12) |
| `calcular_indemnizacion` | `salario_mensual` (requerido), `anios` (0 por defecto), `meses` (<12, 0 por defecto) |
| `calcular_vacaciones` | `salario_mensual` (requerido), `dias_pendientes` (15 por defecto) |
| `costo_total_empleado` | `salario_mensual` (requerido) |

### Constantes legales

Están todas juntas al inicio de `calculos.py` para poder actualizarlas en un solo
lugar si cambian:

| Constante | Valor |
|---|---|
| `TASA_IGSS_PATRONAL` | 12.67% |
| `TASA_IGSS_LABORAL` | 4.83% |
| `DIAS_VACACIONES_POR_ANIO` | 15 días hábiles |

## Estructura

```
mcp-prestaciones-gt/
├── calculos.py        Aritmética pura, sin dependencias
├── server.py          Registro MCP y arranque HTTP
├── requirements.txt
└── Dockerfile         Opcional, para Cloud Run o pruebas con Docker
```

`calculos.py` no sabe que existe MCP y `server.py` solo registra herramientas, así
que los cálculos se pueden probar sin levantar el servidor.

## Referencias

* [MCP: transportes](https://modelcontextprotocol.io/docs/learn/architecture)
* [Especificación de MCP](https://modelcontextprotocol.io/specification/2025-06-18)
* [JSON-RPC 2.0](https://www.jsonrpc.org/)

## Licencia

MIT
