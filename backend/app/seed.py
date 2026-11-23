"""Carga inicial: inserta el CSV de DataCo en la base de datos y registra el modelo del notebook como version 1.

Uso (desde la carpeta backend):  python -m app.seed [ruta_csv]
"""
import sys
from pathlib import Path

from sqlalchemy import func, select

from .database import SessionLocal
from .ml import entrenamiento as ml
from .ml.gestor import gestor, guardar_datos_entrenamiento
from .models import Dataset

CSV_POR_DEFECTO = Path(__file__).resolve().parents[2] / "data" / "DataCoSupplyChainDataset.csv"


def main() -> None:
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else CSV_POR_DEFECTO
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Dataset)) == 0:
            if not ruta.exists():
                sys.exit(f"No se encontró el CSV: {ruta}")
            print(f"Leyendo {ruta} ...")
            datos, formato = ml.preparar_datos(ml.leer_csv(ruta.read_bytes()))
            dataset = guardar_datos_entrenamiento(db, datos, ruta.name, formato, reemplazar=False)
            print(f"Dataset {dataset.id}: {dataset.total_registros} registros cargados ({formato})")
        else:
            print("Ya existen datasets, se omite la carga de datos")

        version = gestor.registrar_modelo_notebook(db)
        print(f"Modelo del notebook registrado como versión {version.version}" if version else "El modelo ya estaba registrado")


if __name__ == "__main__":
    main()
