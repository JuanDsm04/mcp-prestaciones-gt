"""Calculos de prestaciones laborales de Guatemala.

Aritmetica pura, sin base de datos ni dependencias. Se separa del servidor para
poder probar los calculos por su cuenta.

Las constantes de abajo son tasas legales que pueden cambiar; estan aqui arriba
justamente para poder actualizarlas en un solo lugar.
"""

from __future__ import annotations

# Cuota patronal del IGSS sobre el salario ordinario.
TASA_IGSS_PATRONAL = 0.1267

# Cuota laboral del IGSS, la que se le descuenta al trabajador.
TASA_IGSS_LABORAL = 0.0483

# Dias habiles de vacaciones que se acumulan por ano trabajado.
DIAS_VACACIONES_POR_ANIO = 15

MESES_DEL_ANIO = 12


def _validar_salario(salario_mensual: float) -> None:
    """Rechaza salarios que no tienen sentido para un calculo laboral."""
    if salario_mensual <= 0:
        raise ValueError(
            f"El salario mensual debe ser mayor que 0 (recibido: {salario_mensual})."
        )


def _validar_meses(meses: float, maximo: int = MESES_DEL_ANIO) -> None:
    """Rechaza periodos fuera del rango que admite la prestacion."""
    if not 0 < meses <= maximo:
        raise ValueError(
            f"Los meses trabajados deben estar entre 0 y {maximo} (recibido: {meses})."
        )


def bono_14(salario_mensual: float, meses_trabajados: float = 12) -> dict:
    """Calcula el Bono 14, que equivale a un salario mensual al ano.

    Se paga en julio y cubre del 1 de julio al 30 de junio. Si el trabajador no
    completo el periodo, se paga la parte proporcional.
    """
    _validar_salario(salario_mensual)
    _validar_meses(meses_trabajados)

    monto = salario_mensual * (meses_trabajados / MESES_DEL_ANIO)
    return {
        "prestacion": "Bono 14",
        "salario_mensual": round(salario_mensual, 2),
        "meses_trabajados": meses_trabajados,
        "proporcional": meses_trabajados < MESES_DEL_ANIO,
        "monto": round(monto, 2),
        "se_paga_en": "julio",
        "periodo_que_cubre": "1 de julio al 30 de junio",
    }


def aguinaldo(salario_mensual: float, meses_trabajados: float = 12) -> dict:
    """Calcula el aguinaldo, que tambien equivale a un salario mensual al ano.

    Cubre del 1 de diciembre al 30 de noviembre. Se paga 50% en la primera
    quincena de diciembre y el resto a mas tardar el 15 de enero.
    """
    _validar_salario(salario_mensual)
    _validar_meses(meses_trabajados)

    monto = salario_mensual * (meses_trabajados / MESES_DEL_ANIO)
    return {
        "prestacion": "Aguinaldo",
        "salario_mensual": round(salario_mensual, 2),
        "meses_trabajados": meses_trabajados,
        "proporcional": meses_trabajados < MESES_DEL_ANIO,
        "monto": round(monto, 2),
        "primer_pago_50pct": round(monto / 2, 2),
        "segundo_pago_50pct": round(monto - round(monto / 2, 2), 2),
        "se_paga_en": "50% en la primera quincena de diciembre, 50% a mas tardar el 15 de enero",
    }


def indemnizacion(salario_mensual: float, anios: int = 0, meses: float = 0) -> dict:
    """Calcula la indemnizacion por despido injustificado.

    Corresponde a un salario mensual por cada ano trabajado, mas la parte
    proporcional del tiempo que no completa un ano.
    """
    _validar_salario(salario_mensual)
    if anios < 0 or meses < 0:
        raise ValueError("El tiempo trabajado no puede ser negativo.")
    if meses >= MESES_DEL_ANIO:
        raise ValueError(
            f"Los meses deben ser menos de {MESES_DEL_ANIO}; usa el parametro 'anios' "
            f"para los anos completos (recibido: {meses} meses)."
        )
    if anios == 0 and meses == 0:
        raise ValueError("Indica al menos un ano o un mes trabajado.")

    tiempo_total = anios + meses / MESES_DEL_ANIO
    monto = salario_mensual * tiempo_total

    return {
        "prestacion": "Indemnizacion",
        "salario_mensual": round(salario_mensual, 2),
        "tiempo_trabajado": f"{anios} ano(s) y {meses} mes(es)",
        "equivalente_en_anios": round(tiempo_total, 4),
        "monto": round(monto, 2),
        "nota": "Aplica en despido injustificado o renuncia con causa justificada.",
    }


def vacaciones(salario_mensual: float, dias_pendientes: float = DIAS_VACACIONES_POR_ANIO) -> dict:
    """Calcula el pago de vacaciones no gozadas.

    Se acumulan 15 dias habiles por ano trabajado. El valor del dia se saca
    dividiendo el salario mensual entre 30.
    """
    _validar_salario(salario_mensual)
    if dias_pendientes <= 0:
        raise ValueError(f"Los dias pendientes deben ser mayores que 0 (recibido: {dias_pendientes}).")

    valor_dia = salario_mensual / 30
    monto = valor_dia * dias_pendientes

    return {
        "prestacion": "Vacaciones",
        "salario_mensual": round(salario_mensual, 2),
        "valor_del_dia": round(valor_dia, 2),
        "dias_pendientes": dias_pendientes,
        "monto": round(monto, 2),
        "nota": f"Se acumulan {DIAS_VACACIONES_POR_ANIO} dias habiles por ano trabajado.",
    }


def costo_total_empleado(salario_mensual: float) -> dict:
    """Calcula lo que realmente cuesta un empleado al mes, no solo su salario.

    Suma el salario, la provision mensual de Bono 14 y aguinaldo (un doceavo de
    cada uno), la provision de vacaciones y la cuota patronal del IGSS. Es el
    numero que necesita un dueno de negocio antes de contratar.
    """
    _validar_salario(salario_mensual)

    provision_bono14 = salario_mensual / MESES_DEL_ANIO
    provision_aguinaldo = salario_mensual / MESES_DEL_ANIO
    provision_vacaciones = (salario_mensual / 30 * DIAS_VACACIONES_POR_ANIO) / MESES_DEL_ANIO
    igss_patronal = salario_mensual * TASA_IGSS_PATRONAL

    costo = (
        salario_mensual
        + provision_bono14
        + provision_aguinaldo
        + provision_vacaciones
        + igss_patronal
    )
    sobrecosto = costo - salario_mensual

    return {
        "salario_mensual": round(salario_mensual, 2),
        "desglose_mensual": {
            "salario": round(salario_mensual, 2),
            "provision_bono_14": round(provision_bono14, 2),
            "provision_aguinaldo": round(provision_aguinaldo, 2),
            "provision_vacaciones": round(provision_vacaciones, 2),
            "igss_patronal": round(igss_patronal, 2),
        },
        "costo_mensual_real": round(costo, 2),
        "costo_anual_real": round(costo * MESES_DEL_ANIO, 2),
        "sobrecosto_sobre_el_salario": round(sobrecosto, 2),
        "sobrecosto_porcentaje": round(sobrecosto / salario_mensual * 100, 2),
        "descuento_igss_al_trabajador": round(salario_mensual * TASA_IGSS_LABORAL, 2),
        "nota": (
            "El IGSS laboral no es un costo para el patrono: se descuenta del salario "
            "del trabajador y se incluye aqui solo como referencia."
        ),
    }
