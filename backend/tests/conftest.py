"""Los tests usan una base de datos separada (dataco_test) en el mismo contenedor de PostgreSQL
y una copia temporal de la carpeta del modelo, para no modificar los datos reales."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
CARPETA_MODELO = Path(tempfile.mkdtemp(prefix="dataco_modelo_"))
for nombre in ("modelo.joblib", "metricas.json"):
    shutil.copy(RAIZ / "backend" / "model" / nombre, CARPETA_MODELO / nombre)

os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://dataco:dataco@localhost:5433/dataco_test")
os.environ["MODEL_DIR"] = str(CARPETA_MODELO)


def _crear_base_de_prueba():
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    url = make_url(os.environ["DATABASE_URL"])
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS {url.database} WITH (FORCE)"))
        c.execute(text(f"CREATE DATABASE {url.database}"))
    admin.dispose()
    esquema = (RAIZ / "database" / "schema.sql").read_text(encoding="utf-8")
    motor = create_engine(url)
    with motor.begin() as c:
        c.exec_driver_sql(esquema)
    motor.dispose()


_crear_base_de_prueba()


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
    shutil.rmtree(CARPETA_MODELO, ignore_errors=True)


@pytest.fixture
def pedido():
    return {
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
    }


@pytest.fixture(scope="session")
def csv_preparado():
    """CSV preparado pequeño construido a partir del dataset real."""
    import pandas as pd

    from app.ml import entrenamiento as ml

    df = pd.read_csv(RAIZ / "data" / "DataCoSupplyChainDataset.csv", encoding="latin-1", nrows=4000)
    datos, _ = ml.preparar_datos(df)
    return datos.to_csv(index=False).encode("utf-8")
