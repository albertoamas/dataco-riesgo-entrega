import pandas as pd
import pytest

from app.ml import entrenamiento as ml


def fila_dataco(**cambios):
    fila = {
        "Type": "DEBIT", "Shipping Mode": "First Class", "Market": "LATAM", "Order Region": "South America",
        "Order Country": "Brasil", "Customer Segment": "Consumer", "Category Name": "Cleats",
        "Order Item Quantity": 1, "Product Price": 59.99, "Order Item Discount Rate": 0.1,
        "Late_delivery_risk": 1, "order date (DateOrders)": "1/31/2018 22:56",
        "Delivery Status": "Late delivery", "Days for shipping (real)": 5,
    }
    fila.update(cambios)
    return fila


def test_preparar_formato_dataco_deriva_fecha_y_quita_fuga():
    datos, formato = ml.preparar_datos(pd.DataFrame([fila_dataco()]))
    assert formato == "dataco"
    assert list(datos.columns) == ml.COLUMNAS + [ml.OBJETIVO]
    assert "Delivery Status" not in datos.columns
    assert datos.loc[0, "order_month"] == 1
    assert datos.loc[0, "order_day_of_week"] == 2  # 31/01/2018 fue miércoles
    assert datos.loc[0, "order_hour"] == 22


def test_preparar_descarta_registros_invalidos():
    df = pd.DataFrame([fila_dataco(), fila_dataco(**{"Order Item Quantity": 0}), fila_dataco(Late_delivery_risk=5)])
    datos, _ = ml.preparar_datos(df)
    assert len(datos) == 1


def test_preparar_formato_desconocido():
    with pytest.raises(ml.ErrorDatos):
        ml.preparar_datos(pd.DataFrame({"a": [1]}))


def test_entrenar_requiere_ambas_clases():
    datos, _ = ml.preparar_datos(pd.DataFrame([fila_dataco()] * 50))
    with pytest.raises(ml.ErrorDatos):
        ml.entrenar(datos)


@pytest.mark.parametrize(
    ("accuracy", "f1_score", "roc_auc", "esperado"),
    [
        pytest.param(0.649, 0.699, 0.799, False, id="ninguna-cumple"),
        pytest.param(0.65, 0.699, 0.799, True, id="solo-accuracy-en-el-minimo"),
        pytest.param(0.649, 0.70, 0.799, True, id="solo-f1-en-el-minimo"),
        pytest.param(0.649, 0.699, 0.80, True, id="solo-roc-auc-en-el-minimo"),
        pytest.param(0.66, 0.71, 0.799, True, id="cumplen-accuracy-y-f1"),
        pytest.param(0.66, 0.699, 0.81, True, id="cumplen-accuracy-y-roc-auc"),
        pytest.param(0.649, 0.71, 0.81, True, id="cumplen-f1-y-roc-auc"),
        pytest.param(0.66, 0.71, 0.81, True, id="todas-cumplen"),
    ],
)
def test_cumple_calidad_con_al_menos_una_metrica(accuracy, f1_score, roc_auc, esperado):
    # Usar mínimos distintos detecta si se aplica a una métrica el umbral de otra.
    metricas = {"accuracy": accuracy, "f1_score": f1_score, "roc_auc": roc_auc}
    assert ml.cumple_calidad(metricas, min_accuracy=0.65, min_f1=0.70, min_roc_auc=0.80) is esperado


def test_muestra_csv_preparada_contiene_registros_validos_de_ambas_clases(csv_preparado):
    datos, formato = ml.preparar_datos(ml.leer_csv(csv_preparado))

    assert formato == "preparado"
    assert len(datos) == 4000
    assert set(datos[ml.OBJETIVO]) == {0, 1}
