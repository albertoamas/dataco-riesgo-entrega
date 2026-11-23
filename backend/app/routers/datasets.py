from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..ml import entrenamiento as ml
from ..ml.gestor import EntrenamientoEnCurso, gestor, guardar_datos_entrenamiento, total_registros_activos
from ..models import Dataset
from ..schemas import CargaDatasetSalida, DatasetSalida, ErrorRespuesta, ReentrenamientoSalida
from .conversion import version_a_salida

router = APIRouter(prefix="/api", tags=["Datos de entrenamiento"])


@router.post(
    "/datasets",
    response_model=CargaDatasetSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar un archivo de entrenamiento (CSV)",
    responses={400: {"model": ErrorRespuesta}, 409: {"model": ErrorRespuesta}, 413: {"model": ErrorRespuesta}},
)
def cargar_dataset(
    archivo: UploadFile = File(..., description="CSV original de DataCo o CSV con las columnas preparadas"),
    modo: Literal["agregar", "reemplazar"] = Form("agregar", description="agregar: suma los datos a los existentes; reemplazar: desactiva los datasets anteriores"),
    reentrenar: bool = Form(False, description="Re-entrenar el modelo inmediatamente después de la carga"),
    db: Session = Depends(get_db),
):
    """Acepta dos formatos:

    - **dataco**: el CSV original `DataCoSupplyChainDataset.csv` (se preparan las columnas automáticamente).
    - **preparado**: CSV con las columnas `payment_type, shipping_mode, market, order_region, order_country,
      customer_segment, category_name, quantity, product_price, discount_rate, order_month,
      order_day_of_week, order_hour, late_delivery_risk`.
    """
    if not (archivo.filename or "").lower().endswith(".csv"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El archivo debe tener extensión .csv")
    contenido = archivo.file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(contenido) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"El archivo supera {settings.max_upload_mb} MB")
    if reentrenar and gestor.entrenando:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya hay un re-entrenamiento en curso")

    try:
        crudo = ml.leer_csv(contenido)
        datos, formato = ml.preparar_datos(crudo)
    except ml.ErrorDatos as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e

    dataset = guardar_datos_entrenamiento(db, datos, archivo.filename, formato, reemplazar=(modo == "reemplazar"))
    respuesta = CargaDatasetSalida(
        mensaje=f"Se cargaron {len(datos)} registros ({formato})",
        dataset=DatasetSalida.model_validate(dataset),
        registros_descartados=len(crudo) - len(datos),
        total_registros_activos=total_registros_activos(db),
    )

    if reentrenar:
        try:
            r = gestor.reentrenar(db, buscar_hiperparametros=False, activar_si_cumple=True)
        except (EntrenamientoEnCurso, ml.ErrorDatos) as e:
            respuesta.mensaje += f". No se pudo re-entrenar: {e}"
            return respuesta
        respuesta.reentrenamiento = ReentrenamientoSalida(
            mensaje=f"Versión {r['nueva'].version} {'activada' if r['activado'] else 'no activada'}",
            activado=r["activado"],
            nueva_version=version_a_salida(r["nueva"]),
            version_anterior=version_a_salida(r["anterior"]) if r["anterior"] else None,
            duracion_segundos=r["duracion"],
        )
    return respuesta


@router.get("/datasets", response_model=list[DatasetSalida], summary="Archivos de entrenamiento cargados")
def listar_datasets(db: Session = Depends(get_db)):
    return db.scalars(select(Dataset).order_by(Dataset.id.desc())).all()
