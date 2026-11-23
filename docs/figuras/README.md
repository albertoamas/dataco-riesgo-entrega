# Figuras del documento

Fuentes de las figuras 1, 2, 3, 4 y 9 del documento del proyecto, hechas en un lienzo de diseño (formato `.dc.html`). Cada archivo es una mesa de trabajo con HTML y estilos en línea.

| Archivo | Figura | PNG exportado |
|---|---|---|
| `Main.dc.html` | 1. Arquitectura de la solución | `docs/img/figura_1_arquitectura.png` |
| `Figura2-Cronograma.dc.html` | 2. Cronograma según CRISP-ML(Q) | `docs/img/figura_2_cronograma.png` |
| `Figura3-Importancia.dc.html` | 3. Importancia de las variables | `docs/img/figura_3_importancia_variables.png` |
| `Figura4-BaseDeDatos.dc.html` | 4. Diagrama entidad-relación | `docs/img/figura_4_diagrama_bd.png` |
| `Figura5-Reentrenamiento.dc.html` | 9. Flujo de reentrenamiento | `docs/img/figura_9_flujo_reentrenamiento.png` |

Las figuras 5 a 8 son capturas de la aplicación: `docs/img/figura_5_evaluar_pedido.png`, `figura_6_historial.png`, `figura_7_modelo_metricas.png` y `figura_8_datos_entrenamiento.png`.

Los PNG se exportan sin el título de la mesa de trabajo, porque en formato APA el número y el título de cada figura van en el documento.

## Volver a exportar los PNG

```bash
pip install playwright && python -m playwright install chromium
python docs/figuras/exportar_figuras.py docs/figuras docs/img
```
