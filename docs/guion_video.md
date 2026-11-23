# Guion del video demostrativo (5 minutos)

## Antes de grabar

- [ ] `docker compose down -v && docker compose up -d`, y luego `python -m app.seed`, para que la base quede limpia, con el modelo v1 y sin predicciones.
- [ ] Backend corriendo (`uvicorn app.main:app --port 8000`).
- [ ] Frontend corriendo (`npm run dev`, http://localhost:5180).
- [ ] Pestañas abiertas: notebook en VS Code, cliente web, Swagger (`/docs`) y el repositorio en GitHub.
- [ ] Un CSV pequeño para la demo de carga. Por ejemplo, las primeras 5.000 filas del dataset (ver nota al final).
- [ ] Zoom del navegador al 110 % para que se lea en el video.

## Guion

| Tiempo | Pantalla | Qué mostrar | Qué decir (idea principal) |
|---|---|---|---|
| **0:00 a 0:30** | Diagrama de arquitectura (README) | El esquema: notebook, servicio de IA, base de datos y cliente web | "El problema es predecir, al registrar un pedido, si va a llegar tarde. Usé el dataset DataCo, con 180 mil registros, y seguí CRISP-ML(Q)." |
| **0:30 a 1:30** | Notebook | Recorrer los encabezados de las fases. Detenerse en: tasa de retraso por modo de envío, **tabla de fuga de información** (`Delivery Status`), comparación de modelos y métricas finales con el `assert` del criterio | "El hallazgo clave fue la fuga de información: `Delivery Status` revela el resultado. Con esas columnas se llega a 97 %, pero ese modelo no sirve. Sin ellas obtuve accuracy 0,74, F1 0,73 y AUC 0,83, que cumple el criterio que definí antes de entrenar." |
| **1:30 a 2:30** | Cliente: Evaluar pedido | 1) Pedido con **First Class**: aparece el sello "Llega tarde" con más de 99 %. 2) Cambiar a **Standard Class** y evaluar: baja la probabilidad. 3) Mostrar la cascada mercado → región → país. 4) "Llenar con un pedido de ejemplo". | "El formulario solo pide datos conocidos al momento del pedido. El modo de envío es lo que más influye." |
| **2:30 a 3:00** | Cliente: Historial | Filtro "Entrega tardía", abrir una fila con todos los datos enviados | "Cada predicción queda en PostgreSQL con los datos, el resultado y la versión del modelo que la hizo." |
| **3:00 a 4:00** | Cliente: Datos, luego Modelo | 1) Arrastrar el CSV, dejar marcado "Entrenar nueva versión" y cargar. 2) Mostrar la comparación v1 contra v2. 3) Ir a Modelo: barras contra el umbral, matriz de confusión, gráfico de versiones. 4) "Activar versión" sobre la v1 (rollback). | "La nueva versión solo se activa si cumple el criterio de calidad. Si no, el servicio sigue con la anterior. Y puedo volver a cualquier versión." |
| **4:00 a 4:30** | Swagger (`/docs`) | Expandir `POST /api/predicciones`, "Try it out" con el ejemplo y ejecutar. Mostrar la lista de endpoints. | "La API está documentada con OpenAPI. Estos son los endpoints que pide el enunciado: predicción, historial, métricas, re-entrenamiento y carga de archivos." |
| **4:30 a 5:00** | GitHub | El repositorio, el PR con la revisión de IA y la carpeta `docs/` | "El código está en GitHub, con 18 pruebas automatizadas y el PR revisado por IA. Toda la documentación está en la carpeta docs." |

## Nota: preparar el CSV de la demo

Desde la raíz del proyecto, con el entorno virtual activo:

```bash
python -c "import pandas as pd; pd.read_csv('data/DataCoSupplyChainDataset.csv', encoding='latin-1', nrows=5000).to_csv('data/demo_5000.csv', index=False, encoding='latin-1')"
```

Con 5.000 registros en modo *agregar*, la carga y el re-entrenamiento tardan unos 10 segundos.
