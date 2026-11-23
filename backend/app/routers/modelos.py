from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..ml.entrenamiento import ErrorDatos
from ..ml.gestor import EntrenamientoEnCurso, gestor
from ..models import Prediccion, VersionModelo
from ..schemas import (
    CriterioCalidad,
    ErrorRespuesta,
    MetricasModeloSalida,
    ReentrenamientoEntrada,
    ReentrenamientoSalida,
    VersionModeloSalida,
)
from .conversion import version_a_salida

router = APIRouter(prefix="/api", tags=["Modelo"])


@router.get("/metricas", response_model=MetricasModeloSalida, summary="Métricas de rendimiento del modelo activo", responses={503: {"model": ErrorRespuesta}})
def obtener_metricas(db: Session = Depends(get_db)):
    """Accuracy, precision, recall, F1, ROC-AUC y matriz de confusión del modelo activo, calculadas sobre el conjunto de prueba (20%)."""
    version = db.scalar(select(VersionModelo).where(VersionModelo.activo))
    if version is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "No hay un modelo activo")
    total = db.scalar(select(func.count()).select_from(Prediccion).where(Prediccion.version_modelo_id == version.id))
    return MetricasModeloSalida(
        **version_a_salida(version).model_dump(),
        criterio_calidad=CriterioCalidad(min_accuracy=settings.min_accuracy, min_f1=settings.min_f1, min_roc_auc=settings.min_roc_auc),
        total_predicciones=total,
    )


@router.get("/modelos", response_model=list[VersionModeloSalida], summary="Historial de versiones del modelo")
def listar_modelos(db: Session = Depends(get_db)):
    """Todas las versiones entrenadas con sus métricas, de la más reciente a la más antigua."""
    return [version_a_salida(v) for v in db.scalars(select(VersionModelo).order_by(VersionModelo.version.desc()))]


@router.post(
    "/modelos/reentrenar",
    response_model=ReentrenamientoSalida,
    summary="Re-entrenar el modelo con los datos actualizados",
    responses={400: {"model": ErrorRespuesta}, 409: {"model": ErrorRespuesta}},
)
def reentrenar(entrada: ReentrenamientoEntrada | None = None, db: Session = Depends(get_db)):
    """Entrena una nueva versión con todos los datos de entrenamiento activos en la base de datos.

    La nueva versión solo reemplaza al modelo activo si cumple el criterio de calidad (CRISP-ML(Q)).
    """
    entrada = entrada or ReentrenamientoEntrada()
    try:
        r = gestor.reentrenar(db, entrada.buscar_hiperparametros, entrada.activar_si_cumple)
    except EntrenamientoEnCurso as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from e
    except ErrorDatos as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e

    if r["activado"]:
        mensaje = f"Versión {r['nueva'].version} entrenada y activada"
    elif not r["cumple_calidad"]:
        mensaje = f"Versión {r['nueva'].version} entrenada pero NO cumple el criterio de calidad; se mantiene el modelo anterior"
    else:
        mensaje = f"Versión {r['nueva'].version} entrenada (no activada)"
    return ReentrenamientoSalida(
        mensaje=mensaje,
        activado=r["activado"],
        nueva_version=version_a_salida(r["nueva"]),
        version_anterior=version_a_salida(r["anterior"]) if r["anterior"] else None,
        duracion_segundos=r["duracion"],
    )


@router.post("/modelos/{version}/activar", response_model=VersionModeloSalida, summary="Activar una versión anterior (rollback)", responses={404: {"model": ErrorRespuesta}})
def activar_version(version: int, db: Session = Depends(get_db)):
    try:
        return version_a_salida(gestor.activar_version(db, version))
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e
