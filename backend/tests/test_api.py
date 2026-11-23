def test_salud(client):
    r = client.get("/api/salud")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok", "base_datos": True, "modelo_cargado": True, "version_modelo": 1}


def test_opciones(client):
    r = client.get("/api/opciones")
    assert r.status_code == 200
    opciones = r.json()["opciones"]
    assert "First Class" in opciones["shipping_mode"]
    assert len(opciones["order_country"]) > 100


def test_destinos_sin_datos(client):
    assert client.get("/api/destinos").json() == []


def test_prediccion_y_historial(client, pedido):
    r = client.post("/api/predicciones", json=pedido)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["prediccion"] in (0, 1)
    assert 0 <= cuerpo["probabilidad_tardia"] <= 1
    assert cuerpo["prediccion"] == int(cuerpo["probabilidad_tardia"] >= 0.5)
    assert cuerpo["datos_entrada"]["shipping_mode"] == "First Class"

    historial = client.get("/api/predicciones", params={"tamano": 5}).json()
    assert historial["total"] >= 1
    assert historial["elementos"][0]["id"] == cuerpo["id"]

    detalle = client.get(f"/api/predicciones/{cuerpo['id']}")
    assert detalle.status_code == 200


def test_first_class_tiene_alto_riesgo(client, pedido):
    """En los datos, First Class llega tarde en el 95% de los casos."""
    r = client.post("/api/predicciones", json=pedido)
    assert r.json()["prediccion"] == 1


def test_prediccion_con_categoria_invalida(client, pedido):
    pedido["payment_type"] = "BITCOIN"
    r = client.post("/api/predicciones", json=pedido)
    assert r.status_code == 422
    assert "payment_type" in r.json()["detail"]


def test_prediccion_con_valores_fuera_de_rango(client, pedido):
    pedido["quantity"] = 0
    pedido["discount_rate"] = 1.5
    assert client.post("/api/predicciones", json=pedido).status_code == 422


def test_prediccion_inexistente(client):
    assert client.get("/api/predicciones/999999").status_code == 404


def test_metricas(client):
    r = client.get("/api/metricas")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["activo"] is True
    assert cuerpo["metricas"]["accuracy"] > 0.70
    assert len(cuerpo["matriz_confusion"]) == 2
    assert "criterio_calidad" in cuerpo


def test_carga_rechaza_archivo_invalido(client):
    r = client.post("/api/datasets", files={"archivo": ("datos.csv", b"a,b\n1,2\n", "text/csv")})
    assert r.status_code == 400
    r = client.post("/api/datasets", files={"archivo": ("datos.txt", b"a,b\n1,2\n", "text/plain")})
    assert r.status_code == 400


def test_reentrenar_sin_datos(client):
    r = client.post("/api/modelos/reentrenar", json={})
    assert r.status_code == 400


def test_carga_y_reentrenamiento(client, csv_preparado):
    r = client.post(
        "/api/datasets",
        files={"archivo": ("preparado.csv", csv_preparado, "text/csv")},
        data={"modo": "reemplazar"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["dataset"]["formato"] == "preparado"
    destinos = client.get("/api/destinos").json()
    assert {"market": "LATAM", "order_region": "South America", "order_country": "Brasil"} in destinos

    r = client.post("/api/modelos/reentrenar", json={"activar_si_cumple": False})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["activado"] is False
    assert cuerpo["nueva_version"]["version"] == 2
    assert cuerpo["version_anterior"]["version"] == 1

    modelos = client.get("/api/modelos").json()
    assert [m["version"] for m in modelos] == [2, 1]
    assert client.get("/api/salud").json()["version_modelo"] == 1


def test_activar_version(client):
    r = client.post("/api/modelos/2/activar")
    assert r.status_code == 200
    assert client.get("/api/salud").json()["version_modelo"] == 2
    client.post("/api/modelos/1/activar")
    assert client.post("/api/modelos/99/activar").status_code == 404
