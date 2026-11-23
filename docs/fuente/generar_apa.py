"""Genera el .docx del documento del proyecto a partir de su Markdown.

Formato: Times New Roman 12, interlineado 1,5, todo alineado a la izquierda, tablas con bordes completos,
figuras insertadas desde docs/img y en amarillo los datos que faltan ([Nombre ...]).

Uso: python generar_apa.py <documento.md> <salida.docx> <raiz_del_repositorio>
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

NEGRO = RGBColor(0, 0, 0)
FUENTE = "Times New Roman"
ANCHO_UTIL = 6.5  # pulgadas (carta con márgenes de 1 pulgada)
ALTO_MAX_FIGURA = 7.5

origen, destino, raiz = sys.argv[1], sys.argv[2], Path(sys.argv[3])
bloques = [b.strip("\n") for b in re.split(r"\n\s*\n", open(origen, encoding="utf-8").read()) if b.strip()]

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
for lado in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, lado, Inches(1))

normal = doc.styles["Normal"]
normal.font.name = FUENTE
normal.font.size = Pt(12)
normal.font.color.rgb = NEGRO
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.space_after = Pt(8)
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT


def numero_de_pagina():
    p = sec.header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run()
    for tipo, texto in (("begin", None), (None, "PAGE"), ("end", None)):
        if tipo:
            f = OxmlElement("w:fldChar")
            f.set(qn("w:fldCharType"), tipo)
            r._r.append(f)
        else:
            t = OxmlElement("w:instrText")
            t.set(qn("xml:space"), "preserve")
            t.text = texto
            r._r.append(t)
    r.font.name, r.font.size, r.font.color.rgb = FUENTE, Pt(11), NEGRO


def agregar_texto(p, texto, tamano=None, negrita_forzada=False):
    """**negrita**, *cursiva* y [dato faltante] resaltado en amarillo."""
    for parte in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|\[Nombre[^\]]*\])", texto):
        if not parte:
            continue
        negrita = parte.startswith("**")
        cursiva = not negrita and parte.startswith("*")
        faltante = parte.startswith("[Nombre")
        contenido = parte.strip("*") if (negrita or cursiva) else parte
        r = p.add_run(contenido)
        r.bold = negrita or negrita_forzada
        r.italic = cursiva
        r.font.name, r.font.color.rgb = FUENTE, NEGRO
        if tamano:
            r.font.size = Pt(tamano)
        if faltante:
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW


def parrafo(texto, francesa=False, junto=False, salto=False, tamano=None, despues=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.page_break_before = salto
    pf.keep_with_next = junto
    if francesa:
        pf.left_indent = Inches(0.5)
        pf.first_line_indent = Inches(-0.5)
    if despues is not None:
        pf.space_after = Pt(despues)
    agregar_texto(p, texto, tamano=tamano)
    return p


def bordes_tabla(tabla):
    tblPr = tabla._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{lado}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "6")
        b.set(qn("w:color"), "000000")
        borders.append(b)
    tblPr.append(borders)
    ancho = OxmlElement("w:tblW")
    ancho.set(qn("w:w"), "5000")
    ancho.set(qn("w:type"), "pct")
    tblPr.append(ancho)


def tabla(lineas):
    filas = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lineas if not re.match(r"^\|\s*-", l)]
    t = doc.add_table(rows=len(filas), cols=len(filas[0]))
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    bordes_tabla(t)
    for i, fila in enumerate(filas):
        trPr = t.rows[i]._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        if i == 0:
            trPr.append(OxmlElement("w:tblHeader"))  # repite el encabezado si la tabla cruza de página
        for j, valor in enumerate(fila):
            p = t.cell(i, j).paragraphs[0]
            pf = p.paragraph_format
            pf.line_spacing = 1.0
            pf.space_before = Pt(2)
            pf.space_after = Pt(2)
            pf.keep_with_next = len(filas) <= 15 and i < len(filas) - 1
            agregar_texto(p, valor, tamano=10.5, negrita_forzada=(i == 0))
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def figura(ruta_relativa, texto_original):
    ruta = raiz / ruta_relativa
    if not ruta.exists():
        p = parrafo(texto_original.strip("*"))
        for r in p.runs:
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW
        return
    from PIL import Image

    with Image.open(ruta) as im:
        w, h = im.size
    ancho = ANCHO_UTIL
    if ancho * h / w > ALTO_MAX_FIGURA:
        ancho = ALTO_MAX_FIGURA * w / h
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.0
    p.add_run().add_picture(str(ruta), width=Inches(ancho))


numero_de_pagina()
titulo = None
en_portada = en_referencias = False
previo = ""

for bloque in bloques:
    if bloque.startswith("# "):
        titulo = bloque[2:].strip()
        parrafo(f"**{titulo}**", tamano=16, despues=24)
        en_portada = True
        continue
    if bloque.startswith("## "):
        nombre = bloque[3:].strip()
        en_portada = False
        en_referencias = nombre == "Referencias"
        salto = nombre in ("Resumen", "Introducción", "Referencias")
        p = parrafo(f"**{nombre}**", junto=True, salto=salto, tamano=14)
        p.paragraph_format.space_before = Pt(12)
        continue
    if bloque.startswith("### "):
        p = parrafo(f"**{bloque[4:].strip()}**", junto=True)
        p.paragraph_format.space_before = Pt(6)
        continue
    if bloque.startswith("|"):
        tabla(bloque.splitlines())
        continue
    if en_portada:
        parrafo(bloque, despues=4)
        continue
    if en_referencias:
        parrafo(bloque, francesa=True)
        continue
    if re.fullmatch(r"\*\*(Tabla|Figura) \d+\*\*", bloque):
        parrafo(bloque, junto=True, despues=0)
        previo = "numero"
        continue
    if previo == "numero" and re.fullmatch(r"\*[^*]+\*", bloque):
        parrafo(bloque, junto=True)
        previo = ""
        continue
    m = re.match(r"\*\*\[INSERTAR AQUÍ LA FIGURA \d+\. Archivo: ([^\]]+)\]\*\*", bloque)
    if m:
        figura(m.group(1).strip(), bloque)
        continue
    parrafo(bloque)

doc.core_properties.title = titulo
doc.core_properties.author = ""
doc.save(destino)
print("ok", destino)
