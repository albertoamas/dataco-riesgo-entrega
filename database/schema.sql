-- =============================================================
-- Base de datos del Servicio de IA - DataCo Late Delivery Risk
-- PostgreSQL 16
-- Se ejecuta automaticamente al crear el contenedor de Docker
-- (docker-entrypoint-initdb.d) o manualmente con:
--   psql -U dataco -d dataco -f database/schema.sql
-- =============================================================

DROP TABLE IF EXISTS predicciones;
DROP TABLE IF EXISTS versiones_datasets;
DROP TABLE IF EXISTS versiones_modelo;
DROP TABLE IF EXISTS datos_entrenamiento;
DROP TABLE IF EXISTS datasets;

-- Archivos de entrenamiento enviados al servicio
CREATE TABLE datasets (
    id              SERIAL PRIMARY KEY,
    nombre_archivo  VARCHAR(255) NOT NULL,
    formato         VARCHAR(20)  NOT NULL CHECK (formato IN ('dataco', 'preparado')),
    total_registros INTEGER      NOT NULL CHECK (total_registros >= 0),
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    fecha_carga     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Registros de entrenamiento ya preparados (solo variables sin fuga de informacion)
CREATE TABLE datos_entrenamiento (
    id                 BIGSERIAL PRIMARY KEY,
    dataset_id         INTEGER       NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    payment_type       VARCHAR(20)   NOT NULL,
    shipping_mode      VARCHAR(30)   NOT NULL,
    market             VARCHAR(30)   NOT NULL,
    order_region       VARCHAR(50)   NOT NULL,
    order_country      VARCHAR(100)  NOT NULL,
    customer_segment   VARCHAR(30)   NOT NULL,
    category_name      VARCHAR(100)  NOT NULL,
    quantity           INTEGER       NOT NULL CHECK (quantity > 0),
    product_price      NUMERIC(10,2) NOT NULL CHECK (product_price >= 0),
    discount_rate      NUMERIC(5,4)  NOT NULL CHECK (discount_rate BETWEEN 0 AND 1),
    order_month        SMALLINT      NOT NULL CHECK (order_month BETWEEN 1 AND 12),
    order_day_of_week  SMALLINT      NOT NULL CHECK (order_day_of_week BETWEEN 0 AND 6),
    order_hour         SMALLINT      NOT NULL CHECK (order_hour BETWEEN 0 AND 23),
    late_delivery_risk SMALLINT      NOT NULL CHECK (late_delivery_risk IN (0, 1))
);
CREATE INDEX idx_datos_entrenamiento_dataset ON datos_entrenamiento(dataset_id);

-- Cada entrenamiento del modelo genera una version con sus metricas
CREATE TABLE versiones_modelo (
    id                      SERIAL PRIMARY KEY,
    version                 INTEGER       NOT NULL UNIQUE,
    algoritmo               VARCHAR(100)  NOT NULL,
    hiperparametros         JSONB         NOT NULL DEFAULT '{}',
    accuracy                NUMERIC(6,4)  NOT NULL,
    precision_score         NUMERIC(6,4)  NOT NULL,
    recall                  NUMERIC(6,4)  NOT NULL,
    f1_score                NUMERIC(6,4)  NOT NULL,
    roc_auc                 NUMERIC(6,4)  NOT NULL,
    matriz_confusion        JSONB         NOT NULL,
    registros_entrenamiento INTEGER       NOT NULL,
    registros_prueba        INTEGER       NOT NULL,
    ruta_archivo            VARCHAR(255)  NOT NULL,
    cumple_calidad          BOOLEAN       NOT NULL,
    activo                  BOOLEAN       NOT NULL DEFAULT FALSE,
    origen                  VARCHAR(20)   NOT NULL DEFAULT 'api' CHECK (origen IN ('notebook', 'api')),
    fecha_entrenamiento     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
-- Solo puede existir un modelo activo a la vez
CREATE UNIQUE INDEX idx_un_modelo_activo ON versiones_modelo(activo) WHERE activo;

-- Trazabilidad: archivos de entrenamiento con los que se entreno cada version (relacion N a N)
CREATE TABLE versiones_datasets (
    version_modelo_id  INTEGER NOT NULL REFERENCES versiones_modelo(id) ON DELETE CASCADE,
    dataset_id         INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    PRIMARY KEY (version_modelo_id, dataset_id)
);
CREATE INDEX idx_versiones_datasets_dataset ON versiones_datasets(dataset_id);

-- Historial de predicciones: datos enviados y resultado
CREATE TABLE predicciones (
    id                 BIGSERIAL PRIMARY KEY,
    version_modelo_id  INTEGER      NOT NULL REFERENCES versiones_modelo(id),
    datos_entrada      JSONB        NOT NULL,
    prediccion         SMALLINT     NOT NULL CHECK (prediccion IN (0, 1)),
    probabilidad       NUMERIC(6,4) NOT NULL CHECK (probabilidad BETWEEN 0 AND 1),
    fecha              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_predicciones_fecha ON predicciones(fecha DESC);
