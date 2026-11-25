"""Mapeo ORM de las tablas definidas en database/schema.sql (el esquema se crea con ese script)."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, BigInteger, Column, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Table, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")

# Trazabilidad: con qué archivos de entrenamiento se entrenó cada versión (N a N)
versiones_datasets = Table(
    "versiones_datasets",
    Base.metadata,
    Column("version_modelo_id", Integer, ForeignKey("versiones_modelo.id", ondelete="CASCADE"), primary_key=True),
    Column("dataset_id", Integer, ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True),
)


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_archivo: Mapped[str] = mapped_column(String(255))
    formato: Mapped[str] = mapped_column(String(20))
    total_registros: Mapped[int]
    activo: Mapped[bool] = mapped_column(default=True)
    fecha_carga: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DatoEntrenamiento(Base):
    __tablename__ = "datos_entrenamiento"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))
    payment_type: Mapped[str] = mapped_column(String(20))
    shipping_mode: Mapped[str] = mapped_column(String(30))
    market: Mapped[str] = mapped_column(String(30))
    order_region: Mapped[str] = mapped_column(String(50))
    order_country: Mapped[str] = mapped_column(String(100))
    customer_segment: Mapped[str] = mapped_column(String(30))
    category_name: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int]
    product_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    order_month: Mapped[int] = mapped_column(SmallInteger)
    order_day_of_week: Mapped[int] = mapped_column(SmallInteger)
    order_hour: Mapped[int] = mapped_column(SmallInteger)
    late_delivery_risk: Mapped[int] = mapped_column(SmallInteger)


class VersionModelo(Base):
    __tablename__ = "versiones_modelo"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[int] = mapped_column(unique=True)
    algoritmo: Mapped[str] = mapped_column(String(100))
    hiperparametros: Mapped[dict] = mapped_column(JsonType, default=dict)
    accuracy: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    precision_score: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    recall: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    f1_score: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    roc_auc: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    matriz_confusion: Mapped[list] = mapped_column(JsonType)
    registros_entrenamiento: Mapped[int]
    registros_prueba: Mapped[int]
    ruta_archivo: Mapped[str] = mapped_column(String(255))
    cumple_calidad: Mapped[bool]
    activo: Mapped[bool] = mapped_column(default=False)
    origen: Mapped[str] = mapped_column(String(20), default="api")
    fecha_entrenamiento: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    datasets: Mapped[list[Dataset]] = relationship(secondary=versiones_datasets, lazy="selectin", order_by=Dataset.id)


class Prediccion(Base):
    __tablename__ = "predicciones"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    version_modelo_id: Mapped[int] = mapped_column(ForeignKey("versiones_modelo.id"))
    datos_entrada: Mapped[dict] = mapped_column(JsonType)
    prediccion: Mapped[int] = mapped_column(SmallInteger)
    probabilidad: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    version_modelo: Mapped[VersionModelo] = relationship(lazy="joined")
