"""Administra el modelo activo en memoria, sus versiones y el re-entrenamiento."""
import json
import threading
import time
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..config import settings
from ..database import engine
from ..models import Dataset, VersionModelo
from . import entrenamiento as ml


class ModeloNoDisponible(RuntimeError):
    pass


class EntrenamientoEnCurso(RuntimeError):
    pass


def ruta_opciones(ruta_modelo: Path) -> Path:
    return ruta_modelo.with_suffix(".opciones.json")


class GestorModelo:
    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self._pipeline = None
        self._version: VersionModelo | None = None
        self._opciones: dict = {}
        self._lock_carga = threading.Lock()
        self._lock_entrenamiento = threading.Lock()

    # ---------- Modelo activo ----------
    @property
    def version(self) -> VersionModelo | None:
        return self._version

    @property
    def opciones(self) -> dict:
        return self._opciones

    @property
    def entrenando(self) -> bool:
        return self._lock_entrenamiento.locked()

    def cargar_activo(self, db: Session) -> None:
        version = db.scalar(select(VersionModelo).where(VersionModelo.activo))
        with self._lock_carga:
            if version is None:
                self._pipeline, self._version, self._opciones = None, None, {}
                return
            ruta = self.model_dir / version.ruta_archivo
            self._pipeline = joblib.load(ruta)
            self._opciones = json.loads(ruta_opciones(ruta).read_text(encoding="utf-8"))
            self._version = version

    def predecir(self, datos: dict) -> tuple[int, float, VersionModelo]:
        with self._lock_carga:
            if self._pipeline is None:
                raise ModeloNoDisponible("No hay un modelo activo. Cargue datos y re-entrene el modelo.")
            fila = pd.DataFrame([datos])[ml.COLUMNAS]
            probabilidad = float(self._pipeline.predict_proba(fila)[0, 1])
            prediccion = int(self._pipeline.predict(fila)[0])
            return prediccion, probabilidad, self._version

    # ---------- Registro inicial del modelo del notebook ----------
    def registrar_modelo_notebook(self, db: Session) -> VersionModelo | None:
        """Registra modelo.joblib + metricas.json (generados por el notebook) como version 1."""
        if db.scalar(select(func.count()).select_from(VersionModelo)) > 0:
            return None
        ruta_modelo = self.model_dir / "modelo.joblib"
        ruta_metricas = self.model_dir / "metricas.json"
        if not ruta_modelo.exists() or not ruta_metricas.exists():
            return None
        info = json.loads(ruta_metricas.read_text(encoding="utf-8"))
        ruta_opciones(ruta_modelo).write_text(json.dumps(info["opciones"], ensure_ascii=False), encoding="utf-8")
        m = info["metricas"]
        version = VersionModelo(
            version=1,
            algoritmo=info["algoritmo"],
            hiperparametros=info["mejores_parametros"],
            accuracy=m["accuracy"],
            precision_score=m["precision"],
            recall=m["recall"],
            f1_score=m["f1_score"],
            roc_auc=m["roc_auc"],
            matriz_confusion=info["matriz_confusion"],
            registros_entrenamiento=info["registros_entrenamiento"],
            registros_prueba=info["registros_prueba"],
            ruta_archivo=ruta_modelo.name,
            cumple_calidad=ml.cumple_calidad(m, settings.min_accuracy, settings.min_f1, settings.min_roc_auc),
            activo=True,
            origen="notebook",
        )
        db.add(version)
        db.commit()
        return version

    # ---------- Re-entrenamiento ----------
    def reentrenar(self, db: Session, buscar_hiperparametros: bool, activar_si_cumple: bool) -> dict:
        if not self._lock_entrenamiento.acquire(blocking=False):
            raise EntrenamientoEnCurso("Ya hay un re-entrenamiento en curso")
        try:
            inicio = time.perf_counter()
            datos = cargar_datos_entrenamiento()
            if datos.empty:
                raise ml.ErrorDatos("No hay datos de entrenamiento activos. Envie un archivo de entrenamiento primero.")

            resultado = ml.entrenar(datos, buscar_hiperparametros=buscar_hiperparametros)
            anterior = db.scalar(select(VersionModelo).where(VersionModelo.activo))
            numero = (db.scalar(select(func.max(VersionModelo.version))) or 0) + 1

            ruta = self.model_dir / f"modelo_v{numero}.joblib"
            joblib.dump(resultado.pipeline, ruta)
            ruta_opciones(ruta).write_text(json.dumps(resultado.opciones, ensure_ascii=False), encoding="utf-8")

            m = resultado.metricas
            cumple = ml.cumple_calidad(m, settings.min_accuracy, settings.min_f1, settings.min_roc_auc)
            activar = cumple and activar_si_cumple
            nueva = VersionModelo(
                version=numero,
                algoritmo=ml.ALGORITMO,
                hiperparametros=resultado.hiperparametros,
                accuracy=m["accuracy"],
                precision_score=m["precision"],
                recall=m["recall"],
                f1_score=m["f1_score"],
                roc_auc=m["roc_auc"],
                matriz_confusion=resultado.matriz_confusion,
                registros_entrenamiento=resultado.registros_entrenamiento,
                registros_prueba=resultado.registros_prueba,
                ruta_archivo=ruta.name,
                cumple_calidad=cumple,
                activo=False,
                origen="api",
            )
            db.add(nueva)
            if activar:
                db.execute(update(VersionModelo).where(VersionModelo.activo).values(activo=False))
                db.flush()
                nueva.activo = True
            db.commit()
            if activar:
                self.cargar_activo(db)
            return {
                "activado": activar,
                "cumple_calidad": cumple,
                "nueva": nueva,
                "anterior": anterior,
                "duracion": round(time.perf_counter() - inicio, 2),
            }
        finally:
            self._lock_entrenamiento.release()

    def activar_version(self, db: Session, numero: int) -> VersionModelo:
        version = db.scalar(select(VersionModelo).where(VersionModelo.version == numero))
        if version is None:
            raise LookupError(f"No existe la version {numero}")
        db.execute(update(VersionModelo).where(VersionModelo.activo).values(activo=False))
        db.flush()
        version.activo = True
        db.commit()
        self.cargar_activo(db)
        return version


def cargar_datos_entrenamiento() -> pd.DataFrame:
    columnas = ", ".join(f"d.{c}" for c in ml.COLUMNAS + [ml.OBJETIVO])
    consulta = (
        f"SELECT {columnas} FROM datos_entrenamiento d "
        "JOIN datasets s ON s.id = d.dataset_id WHERE s.activo ORDER BY d.id"
    )
    with engine.connect() as conexion:
        datos = pd.read_sql(consulta, conexion)
    for c in ["product_price", "discount_rate"]:
        datos[c] = datos[c].astype(float)
    return datos


def guardar_datos_entrenamiento(db: Session, datos: pd.DataFrame, nombre_archivo: str, formato: str, reemplazar: bool) -> Dataset:
    """Registra el dataset e inserta sus filas con COPY (rapido para cientos de miles de registros)."""
    if reemplazar:
        db.execute(update(Dataset).where(Dataset.activo).values(activo=False))
    dataset = Dataset(nombre_archivo=nombre_archivo, formato=formato, total_registros=len(datos), activo=True)
    db.add(dataset)
    db.flush()

    columnas = ["dataset_id"] + ml.COLUMNAS + [ml.OBJETIVO]
    filas = datos[ml.COLUMNAS + [ml.OBJETIVO]].copy()
    filas.insert(0, "dataset_id", dataset.id)
    cursor = db.connection().connection.driver_connection.cursor()
    with cursor.copy(f"COPY datos_entrenamiento ({', '.join(columnas)}) FROM STDIN") as copia:
        for fila in filas.itertuples(index=False, name=None):
            copia.write_row(fila)
    db.commit()
    return dataset


def total_registros_activos(db: Session) -> int:
    return db.scalar(select(func.coalesce(func.sum(Dataset.total_registros), 0)).where(Dataset.activo))


gestor = GestorModelo(settings.model_dir)
