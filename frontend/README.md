# Cliente web (React + Vite)

Interfaz gráfica que consume todos los endpoints del Servicio de IA.

| Sección | Endpoints que usa |
|---|---|
| Evaluar pedido | `GET /api/opciones`, `GET /api/destinos`, `POST /api/predicciones` |
| Historial | `GET /api/predicciones` (paginado y filtrado) |
| Modelo y métricas | `GET /api/metricas`, `GET /api/modelos`, `POST /api/modelos/reentrenar`, `POST /api/modelos/{version}/activar` |
| Datos de entrenamiento | `POST /api/datasets`, `GET /api/datasets` |
| Barra lateral | `GET /api/salud` (cada 15 s) |

## Ejecutar

Con el backend corriendo en el puerto 8000:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5180
```

En desarrollo, Vite redirige `/api` a `http://localhost:8000` (ver `vite.config.ts`).
Para apuntar a otro servidor, define `VITE_API_URL` (por ejemplo en `frontend/.env`).

```bash
npm run build      # compila a dist/
npm run lint
```

## Diseño

Se diseñó con la skill oficial `frontend-design` de Anthropic (instalada como plugin del proyecto en `.claude/settings.json`).

- **Concepto:** mesa de despacho logístico. El resultado de la predicción se presenta como una etiqueta de envío con un sello.
- **Tipografía:** Barlow y Barlow Condensed (inspiradas en la señalética vial), servidas localmente con Fontsource.
- **Color:** fondo azul niebla, tinta pizarra, ámbar de alta visibilidad como acento; rojo y verde reservados para el estado de la entrega, siempre acompañados de ícono y texto.
- **Gráficos:** barras de métricas contra el umbral de calidad, matriz de confusión en escala secuencial de un tono y evolución por versión con leyenda y tooltip.
- Responsive hasta 320 px, foco visible con teclado y `prefers-reduced-motion` respetado.
