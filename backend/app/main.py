from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import settings
from .database import SessionLocal, engine
from .ml.gestor import gestor
from .routers import datasets, modelos, predicciones
from .schemas import Salud


@asynccontextmanager
async def lifespan(app: FastAPI):
    with SessionLocal() as db:
        gestor.registrar_modelo_notebook(db)
        gestor.cargar_activo(db)
    yield


app = FastAPI(
    title="DataCo - Servicio de IA de riesgo de entrega tardía",
    description=(
        "API REST que expone un modelo de clasificación (HistGradientBoosting) entrenado con el dataset "
        "**DataCo Smart Supply Chain** para predecir si un pedido tendrá entrega tardía.\n\n"
        "Permite: realizar predicciones, consultar el historial, consultar métricas, "
        "enviar archivos de entrenamiento y re-entrenar el modelo."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predicciones.router)
app.include_router(modelos.router)
app.include_router(datasets.router)


@app.get("/api/salud", response_model=Salud, tags=["Sistema"], summary="Estado del servicio")
def salud():
    try:
        with engine.connect() as conexion:
            conexion.execute(text("SELECT 1"))
        base_datos = True
    except Exception:
        base_datos = False
    version = gestor.version
    return Salud(estado="ok", base_datos=base_datos, modelo_cargado=version is not None, version_modelo=version.version if version else None)
