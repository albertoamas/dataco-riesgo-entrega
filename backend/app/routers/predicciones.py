from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..ml import entrenamiento as ml
from ..ml.gestor import ModeloNoDisponible, gestor
from ..models import Dataset, DatoEntrenamiento, Prediccion
from ..schemas import Destino, ErrorRespuesta, HistorialPredicciones, Opciones, PrediccionEntrada, PrediccionSalida
from .conversion import prediccion_a_salida

router = APIRouter(prefix="/api", tags=["Predicciones"])


@router.post(
    "/predicciones",
    response_model=PrediccionSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar datos al modelo y obtener la predicción",
    responses={422: {"model": ErrorRespuesta}, 503: {"model": ErrorRespuesta}},
)
def crear_prediccion(entrada: PrediccionEntrada, db: Session = Depends(get_db)):
    """Predice si un pedido tendrá **entrega tardía** (1) o llegará **a tiempo** (0) y guarda la predicción en el historial."""
    opciones = gestor.opciones
    errores = [
        f"{campo}: valor '{getattr(entrada, campo)}' no válido"
        for campo in ml.COLUMNAS_CATEGORICAS
        if opciones and getattr(entrada, campo) not in opciones.get(campo, [])
    ]
    if errores:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "; ".join(errores) + ". Consulte GET /api/opciones")

    datos = entrada.model_dump(exclude={"order_date"})
    datos.update(
        order_month=entrada.order_date.month,
        order_day_of_week=entrada.order_date.weekday(),
        order_hour=entrada.order_date.hour,
    )
    try:
        prediccion, probabilidad, version = gestor.predecir(datos)
    except ModeloNoDisponible as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e)) from e

    registro = Prediccion(
        version_modelo_id=version.id,
        datos_entrada=entrada.model_dump(mode="json"),
        prediccion=prediccion,
        probabilidad=round(probabilidad, 4),
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return prediccion_a_salida(registro)


@router.get("/predicciones", response_model=HistorialPredicciones, summary="Historial de predicciones previas")
def listar_predicciones(
    pagina: int = Query(1, ge=1),
    tamano: int = Query(20, ge=1, le=200),
    prediccion: int | None = Query(None, ge=0, le=1, description="Filtrar por resultado (0 o 1)"),
    db: Session = Depends(get_db),
):
    """Devuelve los datos enviados y el resultado de cada predicción, de la más reciente a la más antigua."""
    consulta = select(Prediccion)
    conteo = select(func.count()).select_from(Prediccion)
    if prediccion is not None:
        consulta = consulta.where(Prediccion.prediccion == prediccion)
        conteo = conteo.where(Prediccion.prediccion == prediccion)
    total = db.scalar(conteo)
    filas = db.scalars(consulta.order_by(Prediccion.id.desc()).offset((pagina - 1) * tamano).limit(tamano)).all()
    return HistorialPredicciones(total=total, pagina=pagina, tamano=tamano, elementos=[prediccion_a_salida(p) for p in filas])


@router.get("/predicciones/{prediccion_id}", response_model=PrediccionSalida, summary="Detalle de una predicción", responses={404: {"model": ErrorRespuesta}})
def obtener_prediccion(prediccion_id: int, db: Session = Depends(get_db)):
    registro = db.get(Prediccion, prediccion_id)
    if registro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Predicción no encontrada")
    return prediccion_a_salida(registro)


@router.get("/opciones", response_model=Opciones, summary="Valores válidos de las variables categóricas", responses={503: {"model": ErrorRespuesta}})
def obtener_opciones():
    """Valores aceptados por el modelo activo para cada variable categórica (para construir el formulario)."""
    if gestor.version is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "No hay un modelo activo")
    return Opciones(version_modelo=gestor.version.version, opciones=gestor.opciones)


@router.get("/destinos", response_model=list[Destino], summary="Combinaciones válidas de mercado, región y país")
def listar_destinos(db: Session = Depends(get_db)):
    """Combinaciones mercado / región / país presentes en los datos de entrenamiento activos (para filtrar el formulario en cascada)."""
    filas = db.execute(
        select(DatoEntrenamiento.market, DatoEntrenamiento.order_region, DatoEntrenamiento.order_country)
        .join(Dataset, Dataset.id == DatoEntrenamiento.dataset_id)
        .where(Dataset.activo)
        .distinct()
        .order_by(DatoEntrenamiento.market, DatoEntrenamiento.order_region, DatoEntrenamiento.order_country)
    ).all()
    return [Destino(market=m, order_region=r, order_country=c) for m, r, c in filas]
