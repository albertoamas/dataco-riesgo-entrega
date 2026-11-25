from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PrediccionEntrada(BaseModel):
    """Datos de un pedido al momento de registrarlo."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "payment_type": "DEBIT",
        "shipping_mode": "First Class",
        "market": "LATAM",
        "order_region": "South America",
        "order_country": "Brasil",
        "customer_segment": "Consumer",
        "category_name": "Cleats",
        "quantity": 2,
        "product_price": 59.99,
        "discount_rate": 0.05,
        "order_date": "2026-11-23T14:30:00",
    }})

    payment_type: str = Field(..., description="Tipo de pago: DEBIT, TRANSFER, PAYMENT, CASH")
    shipping_mode: str = Field(..., description="Modo de envio: Standard Class, Second Class, First Class, Same Day")
    market: str = Field(..., description="Mercado de destino")
    order_region: str = Field(..., description="Region de destino del pedido")
    order_country: str = Field(..., description="Pais de destino del pedido")
    customer_segment: str = Field(..., description="Segmento del cliente: Consumer, Corporate, Home Office")
    category_name: str = Field(..., description="Categoria del producto")
    quantity: int = Field(..., ge=1, le=1000, description="Cantidad de unidades")
    product_price: float = Field(..., ge=0, le=100000, description="Precio unitario del producto")
    discount_rate: float = Field(..., ge=0, le=1, description="Tasa de descuento (0 a 1)")
    order_date: datetime = Field(..., description="Fecha y hora del pedido; se usan mes, dia de la semana y hora")


class PrediccionSalida(BaseModel):
    id: int
    prediccion: int = Field(..., description="1 = entrega tardia, 0 = a tiempo")
    etiqueta: str
    probabilidad_tardia: float
    version_modelo: int
    fecha: datetime
    datos_entrada: dict


class HistorialPredicciones(BaseModel):
    total: int
    pagina: int
    tamano: int
    elementos: list[PrediccionSalida]


class Metricas(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float


class CriterioCalidad(BaseModel):
    min_accuracy: float
    min_f1: float
    min_roc_auc: float


class DatasetResumen(BaseModel):
    id: int
    nombre_archivo: str
    total_registros: int


class VersionModeloSalida(BaseModel):
    version: int
    algoritmo: str
    hiperparametros: dict
    metricas: Metricas
    matriz_confusion: list[list[int]]
    registros_entrenamiento: int
    registros_prueba: int
    cumple_calidad: bool
    activo: bool
    origen: str
    fecha_entrenamiento: datetime
    datasets: list[DatasetResumen] = Field(default_factory=list, description="Archivos de entrenamiento con los que se entrenó esta versión")


class MetricasModeloSalida(VersionModeloSalida):
    criterio_calidad: CriterioCalidad
    total_predicciones: int


class ReentrenamientoEntrada(BaseModel):
    buscar_hiperparametros: bool = Field(False, description="Ejecuta GridSearchCV (tarda varios minutos). Si es false usa los mejores hiperparametros del notebook")
    activar_si_cumple: bool = Field(True, description="Activa la nueva version solo si cumple el criterio de calidad")


class ReentrenamientoSalida(BaseModel):
    mensaje: str
    activado: bool
    nueva_version: VersionModeloSalida
    version_anterior: VersionModeloSalida | None
    duracion_segundos: float


class DatasetSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_archivo: str
    formato: str
    total_registros: int
    activo: bool
    fecha_carga: datetime


class CargaDatasetSalida(BaseModel):
    mensaje: str
    dataset: DatasetSalida
    registros_descartados: int
    total_registros_activos: int
    reentrenamiento: ReentrenamientoSalida | None = None


class Opciones(BaseModel):
    version_modelo: int
    opciones: dict[str, list[str]]


class Destino(BaseModel):
    market: str
    order_region: str
    order_country: str


class Salud(BaseModel):
    estado: Literal["ok"]
    base_datos: bool
    modelo_cargado: bool
    version_modelo: int | None


class ErrorRespuesta(BaseModel):
    detail: str
