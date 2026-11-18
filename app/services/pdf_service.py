from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

#formatos
def _importe(valor) -> str:
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        numero = 0
    return f"$ {numero:,.0f}".replace(",", ".")

#formatos
def _texto(valor) -> str:
    if valor is None:
        return "-"
    return str(valor)

#genera la tabla con el estilo del cine
def _tabla(datos, anchos):
    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8f3a43")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bcb4a9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f7f4ef")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tabla


def generar_reporte_ventas_pdf(reporte: dict, complejo: str | None = None,
                               periodo: str | None = None) -> bytes:
    buffer = BytesIO()

    #configuracion formato hoja
    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title="Reporte de ventas",
        author="Cine Paradiso",
    )
    #estilos de texto
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "TituloReporte",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6f2630"),
        spaceAfter=8,
    )
    subtitulo = ParagraphStyle(
        "SubtituloReporte",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#686057"),
        spaceAfter=12,
    )

    contenido = [
        Paragraph("CINE PARADISO", titulo),
        Paragraph("Reporte de ventas por función y película", subtitulo),
    ]

    filtro_complejo = complejo or "Todos los complejos"
    filtro_periodo = periodo or "Todos los períodos"
    fecha_emision = datetime.now().strftime("%d/%m/%Y %H:%M")
    contenido.append(Paragraph(
        f"<b>Complejo:</b> {_texto(filtro_complejo)} &nbsp;&nbsp;"
        f"<b>Período:</b> {_texto(filtro_periodo)} &nbsp;&nbsp;"
        f"<b>Emitido:</b> {fecha_emision}",
        estilos["Normal"],
    ))
    contenido.append(Spacer(1, 10))

    resumen = reporte.get("resumen_general", {})
    ventas_netas = int(resumen.get("total_vendidas", 0))
    canceladas = int(resumen.get("total_canceladas", 0))
    emitidas = int(resumen.get("total_generadas", 0))
    ingresos_entradas = float(resumen.get("total_ingresos", 0))
    ingresos_servicios = float(resumen.get("ingresos_servicios", 0))

    resumen_datos = [
        ["Entradas emitidas", "Entradas vendidas", "Canceladas", "Ingresos entradas", "Ingresos servicios"],
        [
            str(emitidas),
            str(ventas_netas),
            str(canceladas),
            _importe(ingresos_entradas),
            _importe(ingresos_servicios),
        ],
    ]
    contenido.append(_tabla(resumen_datos, [5.2 * cm] * 5))
    contenido.append(Spacer(1, 14))

    peliculas = reporte.get("por_pelicula", [])
    pelicula_mas_vista = max(
        peliculas,
        key=lambda pelicula: int(pelicula.get("total_entradas_vendidas", 0)),
        default=None,
    )
    if pelicula_mas_vista:
        contenido.append(Paragraph(
            "<b>Película más vista:</b> "
            f"{_texto(pelicula_mas_vista.get('pelicula_titulo'))} "
            f"({int(pelicula_mas_vista.get('total_entradas_vendidas', 0))} entradas)"
        ))
        contenido.append(Spacer(1, 10))



    #parte de ventas por función
    contenido.append(Paragraph("Ventas por función", estilos["Heading2"]))
    funciones = reporte.get("por_funcion", [])
    funciones_datos = [[
        "Película", "Fecha y hora", "Complejo", "Sala",
        "Vendidas", "Canceladas", "Capacidad", "Ingresos",
    ]]
    for funcion in funciones:
        funciones_datos.append([
            _texto(funcion.get("pelicula_titulo")),
            _texto(funcion.get("fecha_hora_proyeccion")),
            _texto(funcion.get("cine_local")),
            _texto(funcion.get("sala_nombre")),
            str(int(funcion.get("butacas_ocupadas", 0))),
            str(int(funcion.get("butacas_canceladas", 0))),
            str(int(funcion.get("sala_capacidad", 0))),
            _importe(funcion.get("total_ingresos", 0)),
        ])
    if len(funciones_datos) == 1:
        funciones_datos.append(["Sin funciones", "-", "-", "-", "0", "0", "0", _importe(0)])
    contenido.append(_tabla(funciones_datos, [
        5.1 * cm, 3.4 * cm, 3.2 * cm, 2.8 * cm,
        1.7 * cm, 1.8 * cm, 1.7 * cm, 2.4 * cm,
    ]))



    #parte de ventas por pelicula
    contenido.append(PageBreak())
    contenido.append(Paragraph("Ventas por película", estilos["Heading2"]))
    peliculas_datos = [[
        "Película", "Funciones", "Entradas", "Capacidad",
        "Ocupación", "Ingresos entradas", "Ingresos servicios", "Total",
    ]]
    for pelicula in peliculas:
        entradas = int(pelicula.get("total_entradas_vendidas", 0))
        capacidad = int(pelicula.get("capacidad_total_ofertada", 0))
        ocupacion = round(entradas / capacidad * 100, 1) if capacidad else 0
        ingresos_entradas_pelicula = float(pelicula.get("total_ingresos", 0))
        ingresos_servicios_pelicula = float(pelicula.get("ingresos_servicios", 0))
        peliculas_datos.append([
            _texto(pelicula.get("pelicula_titulo")),
            str(int(pelicula.get("total_funciones", 0))),
            str(entradas),
            str(capacidad),
            f"{ocupacion}%".replace(".", ","),
            _importe(ingresos_entradas_pelicula),
            _importe(ingresos_servicios_pelicula),
            _importe(ingresos_entradas_pelicula + ingresos_servicios_pelicula),
        ])
    if len(peliculas_datos) == 1:
        peliculas_datos.append(["Sin películas", "0", "0", "0", "0%", _importe(0), _importe(0), _importe(0)])
    contenido.append(_tabla(peliculas_datos, [
        5.4 * cm, 2 * cm, 2 * cm, 2 * cm,
        2 * cm, 3 * cm, 3 * cm, 3 * cm,
    ]))


    #construye el pdf
    documento.build(contenido)
    buffer.seek(0)
    return buffer.getvalue()