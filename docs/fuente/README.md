# Fuente del documento del proyecto

`documento.md` contiene el texto del documento (formato APA 7). `generar_apa.py` lo convierte en `docs/Documento_Proyecto.docx` con Times New Roman 12, doble espacio, márgenes de una pulgada y número de página; el PDF se exporta desde Word.

```bash
pip install python-docx
python docs/fuente/generar_apa.py docs/fuente/documento.md docs/Documento_Proyecto.docx
```

Después de generarlo, insertar cada figura donde dice "INSERTAR AQUÍ LA FIGURA N" con la imagen indicada de `docs/img/`.
