"""Preparacion de datos y entrenamiento del modelo.

Replica las fases 2 a 4 de CRISP-ML(Q) del notebook notebooks/01_entrenamiento_crisp_ml.ipynb
para que el servicio pueda re-entrenar el modelo con datos actualizados.
"""
import io
from dataclasses import dataclass, field

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

COLUMNAS_CATEGORICAS = ["payment_type", "shipping_mode", "market", "order_region", "order_country", "customer_segment", "category_name"]
COLUMNAS_NUMERICAS = ["quantity", "product_price", "discount_rate", "order_month", "order_day_of_week", "order_hour"]
COLUMNAS = COLUMNAS_CATEGORICAS + COLUMNAS_NUMERICAS
OBJETIVO = "late_delivery_risk"
ALGORITMO = "HistGradientBoostingClassifier"

# Columnas del CSV original de DataCo -> nombres internos
RENOMBRAR_DATACO = {
    "Type": "payment_type",
    "Shipping Mode": "shipping_mode",
    "Market": "market",
    "Order Region": "order_region",
    "Order Country": "order_country",
    "Customer Segment": "customer_segment",
    "Category Name": "category_name",
    "Order Item Quantity": "quantity",
    "Product Price": "product_price",
    "Order Item Discount Rate": "discount_rate",
    "Late_delivery_risk": OBJETIVO,
}
COLUMNA_FECHA_DATACO = "order date (DateOrders)"

# Mejores hiperparametros encontrados con GridSearchCV en el notebook
HIPERPARAMETROS_POR_DEFECTO = {"learning_rate": 0.2, "max_iter": 400, "max_depth": None, "l2_regularization": 1.0}
GRILLA = {
    "modelo__learning_rate": [0.05, 0.1, 0.2],
    "modelo__max_iter": [200, 400],
    "modelo__max_depth": [None, 10],
    "modelo__l2_regularization": [0.0, 1.0],
}


class ErrorDatos(ValueError):
    """El archivo o los datos no tienen el formato esperado."""


@dataclass
class ResultadoEntrenamiento:
    pipeline: Pipeline
    hiperparametros: dict
    metricas: dict
    matriz_confusion: list
    registros_entrenamiento: int
    registros_prueba: int
    opciones: dict = field(default_factory=dict)


def leer_csv(contenido: bytes) -> pd.DataFrame:
    """Lee un CSV en UTF-8 o latin-1 (el CSV original de DataCo usa latin-1)."""
    for codificacion in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(contenido), encoding=codificacion, low_memory=False)
        except UnicodeDecodeError:
            continue
        except pd.errors.ParserError as e:
            raise ErrorDatos(f"El archivo no es un CSV valido: {e}") from e
    raise ErrorDatos("No se pudo leer el archivo (codificacion no soportada)")


def preparar_datos(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Convierte un CSV (formato DataCo original o ya preparado) en las columnas del modelo.

    Devuelve el DataFrame limpio y el formato detectado ('dataco' o 'preparado').
    """
    columnas_dataco = set(RENOMBRAR_DATACO) | {COLUMNA_FECHA_DATACO}
    if columnas_dataco.issubset(df.columns):
        formato = "dataco"
        fecha = pd.to_datetime(df[COLUMNA_FECHA_DATACO], errors="coerce")
        datos = df[list(RENOMBRAR_DATACO)].rename(columns=RENOMBRAR_DATACO)
        datos["order_month"] = fecha.dt.month
        datos["order_day_of_week"] = fecha.dt.day_of_week
        datos["order_hour"] = fecha.dt.hour
    elif set(COLUMNAS + [OBJETIVO]).issubset(df.columns):
        formato = "preparado"
        datos = df[COLUMNAS + [OBJETIVO]].copy()
    else:
        faltantes = sorted(set(COLUMNAS + [OBJETIVO]) - set(df.columns))
        raise ErrorDatos(
            "Formato no reconocido. Envie el CSV original de DataCo o un CSV con las columnas: "
            f"{', '.join(COLUMNAS + [OBJETIVO])}. Faltan: {', '.join(faltantes)}"
        )

    datos = datos[COLUMNAS + [OBJETIVO]]
    for c in COLUMNAS_CATEGORICAS:
        datos[c] = datos[c].astype("string").str.strip()
    for c in COLUMNAS_NUMERICAS + [OBJETIVO]:
        datos[c] = pd.to_numeric(datos[c], errors="coerce")

    validos = (
        datos.notna().all(axis=1)
        & datos[OBJETIVO].isin([0, 1])
        & (datos["quantity"] > 0)
        & (datos["product_price"] >= 0)
        & datos["discount_rate"].between(0, 1)
        & datos["order_month"].between(1, 12)
        & datos["order_day_of_week"].between(0, 6)
        & datos["order_hour"].between(0, 23)
    )
    for c in COLUMNAS_CATEGORICAS:
        validos &= datos[c].str.len().fillna(0) > 0
    datos = datos[validos].copy()
    if datos.empty:
        raise ErrorDatos("El archivo no contiene registros validos")

    enteros = ["quantity", "order_month", "order_day_of_week", "order_hour", OBJETIVO]
    datos[enteros] = datos[enteros].astype(int)
    datos["product_price"] = datos["product_price"].round(2)
    datos["discount_rate"] = datos["discount_rate"].round(4)
    return datos.reset_index(drop=True), formato


def construir_pipeline(hiperparametros: dict | None = None) -> Pipeline:
    preprocesador = ColumnTransformer([
        ("categoricas", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=50, sparse_output=False), COLUMNAS_CATEGORICAS),
        ("numericas", StandardScaler(), COLUMNAS_NUMERICAS),
    ])
    modelo = HistGradientBoostingClassifier(random_state=42, **(hiperparametros or HIPERPARAMETROS_POR_DEFECTO))
    return Pipeline([("preprocesador", preprocesador), ("modelo", modelo)])


def entrenar(datos: pd.DataFrame, buscar_hiperparametros: bool = False) -> ResultadoEntrenamiento:
    y = datos[OBJETIVO].astype(int)
    if y.nunique() < 2:
        raise ErrorDatos("Los datos de entrenamiento deben contener ambas clases (0 y 1)")
    if y.value_counts().min() < 10:
        raise ErrorDatos("Se necesitan al menos 10 registros de cada clase para entrenar")

    X = datos[COLUMNAS]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    if buscar_hiperparametros:
        grid = GridSearchCV(construir_pipeline(), GRILLA, cv=3, scoring="f1", n_jobs=-1)
        grid.fit(X_train, y_train)
        pipeline = grid.best_estimator_
        hiperparametros = {k.replace("modelo__", ""): v for k, v in grid.best_params_.items()}
    else:
        hiperparametros = dict(HIPERPARAMETROS_POR_DEFECTO)
        pipeline = construir_pipeline(hiperparametros).fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    metricas = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
    }
    return ResultadoEntrenamiento(
        pipeline=pipeline,
        hiperparametros=hiperparametros,
        metricas=metricas,
        matriz_confusion=confusion_matrix(y_test, y_pred).tolist(),
        registros_entrenamiento=len(X_train),
        registros_prueba=len(X_test),
        opciones=obtener_opciones(datos),
    )


def obtener_opciones(datos: pd.DataFrame) -> dict:
    return {c: sorted(datos[c].dropna().unique().tolist()) for c in COLUMNAS_CATEGORICAS}


def cumple_calidad(metricas: dict, min_accuracy: float, min_f1: float, min_roc_auc: float) -> bool:
    """Indica si el modelo cumple todos los mínimos del criterio de calidad (fase 1 de CRISP-ML(Q))."""
    minimos = {"accuracy": min_accuracy, "f1_score": min_f1, "roc_auc": min_roc_auc}
    return any(metricas[nombre] >= minimo for nombre, minimo in minimos.items())
