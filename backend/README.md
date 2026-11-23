# Servicio de IA (FastAPI)

API REST que expone el modelo de riesgo de entrega tardía entrenado en `notebooks/01_entrenamiento_crisp_ml.ipynb`.

## Ejecutar

```bash
# 1. Base de datos (desde la raíz del repositorio). Crea las tablas con database/schema.sql
docker compose up -d

# 2. Dependencias
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r backend/requirements.txt

# 3. Carga inicial: inserta data/DataCoSupplyChainDataset.csv y registra el modelo del notebook como versión 1
cd backend
python -m app.seed

# 4. Servidor
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Especificación OpenAPI: http://localhost:8000/openapi.json (copia en `docs/swagger.json`)

## Endpoints

| Método | Ruta | Requisito |
|---|---|---|
| POST | `/api/predicciones` | Enviar datos al modelo y obtener la predicción |
| GET | `/api/predicciones` | Historial de predicciones (paginado, filtro por resultado) |
| GET | `/api/predicciones/{id}` | Detalle de una predicción |
| GET | `/api/metricas` | Métricas de rendimiento del modelo activo |
| GET | `/api/modelos` | Historial de versiones del modelo |
| POST | `/api/modelos/reentrenar` | Re-entrenar el modelo con los datos actualizados |
| POST | `/api/modelos/{version}/activar` | Volver a una versión anterior (rollback) |
| POST | `/api/datasets` | Enviar archivo de entrenamiento (CSV) |
| GET | `/api/datasets` | Archivos de entrenamiento cargados |
| GET | `/api/opciones` | Valores válidos de las variables categóricas |
| GET | `/api/salud` | Estado del servicio |

## Tests

```bash
cd backend
pytest
```

Los tests crean una base de datos separada `dataco_test` en el mismo contenedor, así que no modifican los datos reales.

## Configuración (variables de entorno o `backend/.env`)

| Variable | Valor por defecto |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://dataco:dataco@localhost:5433/dataco` |
| `MODEL_DIR` | `backend/model` |
| `CORS_ORIGINS` | `["http://localhost:5180"]` |
| `MIN_ACCURACY` / `MIN_F1` / `MIN_ROC_AUC` | `0.70` / `0.70` / `0.80` |
