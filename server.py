"""Servidor MCP remoto: prestaciones laborales de Guatemala.

A diferencia de un servidor local, este no lo lanza el anfitrion como
subproceso: corre por su cuenta en la nube y los clientes se conectan por HTTP.
Usa el transporte Streamable HTTP de MCP, que lleva los mismos mensajes JSON-RPC
2.0 que el transporte stdio, solo que dentro de peticiones HTTP POST a /mcp.

Se ejecuta con: python server.py
El puerto sale de la variable PORT, que es la que inyectan los servicios de nube.
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

import calculos

# 0.0.0.0 y no 127.0.0.1: dentro de un contenedor hay que escuchar en todas las
# interfaces para que el trafico externo llegue.
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

INSTRUCTIONS = """Calculadora de prestaciones laborales de Guatemala.

Usala cuando el usuario pregunte por Bono 14, aguinaldo, indemnizacion, vacaciones
o cuanto le cuesta realmente un empleado. Todos los montos estan en quetzales (GTQ).

Para saber si conviene contratar a alguien, usa costo_total_empleado: el salario por
si solo subestima el costo real en alrededor de un 30%."""

mcp = FastMCP(
    "prestaciones-gt",
    instructions=INSTRUCTIONS,
    host=HOST,
    port=PORT,
    stateless_http=True,
)


@mcp.tool()
def calcular_bono_14(salario_mensual: float, meses_trabajados: float = 12) -> dict:
    """Calcula el Bono 14 de un trabajador en Guatemala.

    El Bono 14 equivale a un salario mensual completo al ano, se paga en julio y
    cubre del 1 de julio al 30 de junio. Si el trabajador no completo el periodo,
    se paga proporcional a los meses trabajados.

    Args:
        salario_mensual: Salario mensual ordinario en quetzales.
        meses_trabajados: Meses trabajados dentro del periodo, de 1 a 12.
    """
    return calculos.bono_14(salario_mensual, meses_trabajados)


@mcp.tool()
def calcular_aguinaldo(salario_mensual: float, meses_trabajados: float = 12) -> dict:
    """Calcula el aguinaldo de un trabajador en Guatemala.

    Equivale a un salario mensual al ano y cubre del 1 de diciembre al 30 de
    noviembre. Se paga 50% en la primera quincena de diciembre y el resto a mas
    tardar el 15 de enero.

    Args:
        salario_mensual: Salario mensual ordinario en quetzales.
        meses_trabajados: Meses trabajados dentro del periodo, de 1 a 12.
    """
    return calculos.aguinaldo(salario_mensual, meses_trabajados)


@mcp.tool()
def calcular_indemnizacion(salario_mensual: float, anios: int = 0, meses: float = 0) -> dict:
    """Calcula la indemnizacion por despido injustificado.

    Corresponde a un salario mensual por cada ano trabajado, mas la parte
    proporcional del tiempo que no llega a un ano.

    Args:
        salario_mensual: Salario mensual ordinario en quetzales.
        anios: Anos completos trabajados.
        meses: Meses adicionales, menos de 12.
    """
    return calculos.indemnizacion(salario_mensual, anios, meses)


@mcp.tool()
def calcular_vacaciones(salario_mensual: float, dias_pendientes: float = 15) -> dict:
    """Calcula el pago de vacaciones no gozadas.

    Se acumulan 15 dias habiles por ano trabajado y el valor del dia se obtiene
    dividiendo el salario mensual entre 30.

    Args:
        salario_mensual: Salario mensual ordinario en quetzales.
        dias_pendientes: Dias de vacaciones acumulados sin gozar.
    """
    return calculos.vacaciones(salario_mensual, dias_pendientes)


@mcp.tool()
def costo_total_empleado(salario_mensual: float) -> dict:
    """Calcula lo que cuesta realmente un empleado al mes, no solo su salario.

    Suma el salario, la provision mensual de Bono 14, aguinaldo y vacaciones, y
    la cuota patronal del IGSS. Es el numero que hay que mirar antes de contratar,
    porque el salario solo subestima el costo en alrededor de un 30%.

    Args:
        salario_mensual: Salario mensual ordinario en quetzales.
    """
    return calculos.costo_total_empleado(salario_mensual)


if __name__ == "__main__":
    print(f"[prestaciones-gt] escuchando en http://{HOST}:{PORT}/mcp", flush=True)
    mcp.run(transport="streamable-http")
