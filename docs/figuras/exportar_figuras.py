"""Exporta a PNG cada artboard (.dc.html) del lienzo de figuras: toma el <helmet> y el contenido de <x-dc>.

El PNG se recorta debajo del titulo: en formato APA el numero y el titulo de la figura van en el documento.
"""
RECORTE_SUPERIOR = 136
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

origen, destino = Path(sys.argv[1]), Path(sys.argv[2])
figuras = {
    "Main.dc.html": "figura_1_arquitectura.png",
    "Figura2-Cronograma.dc.html": "figura_2_cronograma.png",
    "Figura3-Importancia.dc.html": "figura_3_importancia_variables.png",
    "Figura4-BaseDeDatos.dc.html": "figura_4_diagrama_bd.png",
    "Figura5-Reentrenamiento.dc.html": "figura_9_flujo_reentrenamiento.png",
}

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(device_scale_factor=2, viewport={"width": 1500, "height": 1000})
    for archivo, png in figuras.items():
        texto = (origen / archivo).read_text(encoding="utf-8")
        helmet = re.search(r"<helmet>(.*?)</helmet>", texto, re.S).group(1)
        cuerpo = re.search(r"</helmet>(.*?)</x-dc>", texto, re.S).group(1)
        html = f"<!doctype html><html lang='es'><head><meta charset='utf-8'>{helmet}</head><body>{cuerpo}</body></html>"
        pg.set_content(html, wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        caja = pg.locator("body > div").first.bounding_box()
        pg.screenshot(path=str(destino / png), clip={"x": 0, "y": RECORTE_SUPERIOR, "width": caja["width"], "height": caja["height"] - RECORTE_SUPERIOR})
        print("ok", png)
    b.close()
