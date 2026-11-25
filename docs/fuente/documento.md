# Predicción del riesgo de entrega tardía en una cadena de suministro mediante CRISP-ML(Q), un servicio de inteligencia artificial y un cliente web

Alberto Amas Villarroel

[Nombre de la universidad]

Taller de Sistemas Inteligentes

[Nombre del docente]

23 de noviembre de 2026

## Resumen

Este trabajo desarrolla una solución completa de aprendizaje supervisado que predice, en el momento de registrar un pedido, si su entrega llegará tarde. Se utilizó el conjunto de datos DataCo Smart Supply Chain (Constante et al., 2019), con 180.519 registros, y se siguió la metodología CRISP-ML(Q) (Studer et al., 2021). El análisis exploratorio reveló tres columnas con fuga de información, que se descartaron para que el modelo use solo datos disponibles al registrar el pedido. Se compararon tres algoritmos mediante validación cruzada y se eligió HistGradientBoostingClassifier, que en el conjunto de prueba alcanzó una exactitud de 0,739, un F1 de 0,734 y un ROC-AUC de 0,828, por encima del criterio de éxito definido antes del entrenamiento. El modelo se expone mediante una API REST construida con FastAPI y PostgreSQL, que permite realizar predicciones, consultar el historial y las métricas, cargar datos nuevos y volver a entrenar el modelo con control de calidad. Un cliente web en React consume todos los servicios.

*Palabras clave:* aprendizaje supervisado, clasificación, CRISP-ML(Q), cadena de suministro, API REST

## Introducción

Una empresa de distribución necesita saber, en el momento en que registra un pedido, si este corre el riesgo de llegar tarde. Con esa información puede priorizar el despacho, cambiar el modo de envío o avisar al cliente antes de que el retraso ocurra.

El objetivo del proyecto es entrenar un modelo de clasificación capaz de anticipar ese riesgo y ponerlo a disposición de los usuarios mediante un servicio web. La solución tiene cuatro componentes: un cuaderno de Jupyter donde se entrena el modelo, un servicio de inteligencia artificial que lo expone mediante una API REST, una base de datos que guarda los datos de entrenamiento, las versiones del modelo y las predicciones, y una aplicación web que interactúa con el servicio.

**Figura 1**

*Arquitectura de la solución*

**[INSERTAR AQUÍ LA FIGURA 1. Archivo: docs/img/figura_1_arquitectura.png]**

El cuaderno entrena la primera versión del modelo y la exporta al servicio. A partir de ese momento, el servicio recibe nuevos archivos de datos, vuelve a entrenar el modelo, guarda la información en PostgreSQL y responde al cliente web en formato JSON.

## Metodología

Se utilizó CRISP-ML(Q), un modelo de proceso que adapta CRISP-DM al ciclo de vida de las aplicaciones de aprendizaje automático. Su aporte principal es que cada fase define requisitos, riesgos y medidas de aseguramiento de la calidad antes de avanzar a la siguiente, y que el ciclo continúa después del despliegue con el monitoreo y el mantenimiento del modelo (Studer et al., 2021). La Tabla 1 resume las fases y el resultado de cada una en este proyecto.

**Tabla 1**

*Fases de CRISP-ML(Q) y resultado obtenido en el proyecto*

| Fase | Pregunta que responde | Resultado en el proyecto |
| --- | --- | --- |
| 1. Entendimiento del negocio y de los datos | Qué problema se resuelve y cómo se mide el éxito | Clasificación binaria, criterio de éxito numérico, análisis exploratorio y detección de fuga de información |
| 2. Ingeniería de datos | Qué datos entran al modelo y cómo se transforman | Trece variables disponibles al registrar el pedido, procesadas en un pipeline reproducible |
| 3. Ingeniería del modelo | Qué algoritmo e hiperparámetros se usan | Tres algoritmos comparados con validación cruzada y ajuste del mejor con GridSearchCV |
| 4. Evaluación | Si el modelo cumple el criterio de éxito | Métricas sobre datos no vistos y verificación automática del criterio |
| 5. Despliegue | Cómo se usa el modelo en la práctica | API REST, base de datos PostgreSQL y cliente web |
| 6. Monitoreo y mantenimiento | Cómo se mantiene vigente el modelo | Historial, versionado, reentrenamiento con control de calidad y reversión a versiones anteriores |

Las fases 1 a 4 se desarrollaron en el cuaderno de entrenamiento del repositorio. Las fases 5 y 6 se implementaron en el servicio de inteligencia artificial y en el cliente web.

### Cronograma

El proyecto se desarrolló en dos semanas, entre el 10 y el 23 de noviembre de 2026. Las fases 5 y 6 se superponen porque el versionado y el reentrenamiento se construyeron junto con el servicio. La Figura 2 muestra el cronograma y la Tabla 2 detalla las actividades.

**Figura 2**

*Cronograma del proyecto según CRISP-ML(Q)*

**[INSERTAR AQUÍ LA FIGURA 2. Archivo: docs/img/figura_2_cronograma.png]**

**Tabla 2**

*Actividades y entregables por fase*

| Fase | Fechas | Actividades | Entregable |
| --- | --- | --- | --- |
| 0. Preparación | 10 y 11 de noviembre | Búsqueda del conjunto de datos y definición del tipo de problema | Conjunto de datos elegido |
| 1. Negocio y datos | 12 y 13 de noviembre | Criterio de éxito, análisis exploratorio y fuga de información | Sección 1 del cuaderno |
| 2. Ingeniería de datos | 14 y 15 de noviembre | Selección de variables, limpieza y pipeline | Sección 2 del cuaderno |
| 3. Ingeniería del modelo | 16 y 17 de noviembre | Comparación de algoritmos y ajuste de hiperparámetros | Sección 3 del cuaderno |
| 4. Evaluación | 18 de noviembre | Métricas, matriz de confusión y verificación del criterio | Modelo aprobado (versión 1) |
| 5. Despliegue | 19 al 22 de noviembre | Script de base de datos, API REST con Swagger y cliente web | Servicio, base de datos y cliente |
| 6. Monitoreo y mantenimiento | 20 al 22 de noviembre | Historial, versionado, reentrenamiento y pruebas | Servicios de mantenimiento y 18 pruebas |
| Entrega | 22 y 23 de noviembre | Documentación, revisión del código con IA y video | Documento, repositorio y video |

## Fase 1: entendimiento del negocio y de los datos

### Objetivo y criterio de éxito

El objetivo es estimar, al registrar un pedido, la probabilidad de que llegue más tarde de lo programado. Se trata de un problema de clasificación binaria cuya variable objetivo, Late_delivery_risk, vale 1 cuando la entrega es tardía y 0 cuando llega a tiempo.

Como exige CRISP-ML(Q), el criterio de éxito se fijó antes del entrenamiento (Tabla 3). Este criterio se verifica en tres lugares: en el cuaderno, mediante una aserción; en el servicio, que solo activa una versión nueva si lo cumple; y en el cliente web, que lo muestra junto a las métricas.

**Tabla 3**

*Criterio de éxito del modelo*

| Métrica | Valor mínimo | Justificación |
| --- | --- | --- |
| Exactitud (accuracy) | 0,70 | Superar con claridad al modelo base, que obtiene 0,548 |
| F1 | 0,70 | Equilibrar la detección de retrasos con la cantidad de falsas alarmas |
| ROC-AUC | 0,80 | Ordenar bien los pedidos según su riesgo, sin depender del umbral |

### Descripción de los datos

El conjunto de datos DataCo Smart Supply Chain for Big Data Analysis contiene 180.519 registros correspondientes a 65.752 pedidos, con 53 columnas, entre enero de 2015 y enero de 2018 (Constante et al., 2019). Las clases están balanceadas: el 54,8 % de los registros corresponde a entregas tardías y el 45,2 % a entregas a tiempo. No hay filas duplicadas y los valores faltantes se concentran en columnas que no se utilizan, como Order Zipcode (86 %) y Product Description (100 %). También se detectaron columnas constantes y cuatro pares de columnas idénticas, por ejemplo Benefit per order y Order Profit Per Order.

### Análisis exploratorio

El modo de envío es la variable más relacionada con el retraso, y de forma contraria a lo esperado: los envíos más rápidos son los que más se atrasan, porque el plazo prometido es demasiado corto (Tabla 4). El mercado, el segmento del cliente y el tipo de pago presentan tasas parecidas entre sí, entre 0,48 y 0,58.

**Tabla 4**

*Tasa de entregas tardías según el modo de envío*

| Modo de envío | Días programados | Entregas tardías |
| --- | --- | --- |
| First Class | 1 | 95,3 % |
| Second Class | 2 | 76,6 % |
| Same Day | 0 | 45,7 % |
| Standard Class | 4 | 38,1 % |

### Fuga de información

El hallazgo más importante de esta fase fue que tres columnas solo se conocen después de que el pedido se envía o se entrega (Tabla 5). Con ellas, el modelo alcanza una exactitud cercana a 0,97, pero sería inútil en la práctica, porque necesitaría como entrada justamente lo que se quiere predecir. Por esa razón se descartaron las tres.

**Tabla 5**

*Columnas descartadas por fuga de información*

| Columna | Motivo | Evidencia |
| --- | --- | --- |
| Delivery Status | Define directamente la variable objetivo | El valor Late delivery coincide en un 100 % con Late_delivery_risk igual a 1 |
| Days for shipping (real) | Se conoce al entregar el pedido | Que los días reales superen a los programados coincide en un 97,5 % con el objetivo |
| shipping date (DateOrders) | Se conoce al despachar el pedido | Es posterior a la fecha del pedido |

## Fase 2: ingeniería de datos

El modelo utiliza trece variables que existen en el momento de registrar el pedido (Tabla 6). Tres de ellas se obtienen de la fecha del pedido.

**Tabla 6**

*Variables de entrada del modelo*

| Variable | Tipo | Columna de origen |
| --- | --- | --- |
| shipping_mode | Categórica (4 valores) | Shipping Mode |
| payment_type | Categórica (4 valores) | Type |
| market | Categórica (5 valores) | Market |
| order_region | Categórica (23 valores) | Order Region |
| order_country | Categórica (164 valores) | Order Country |
| customer_segment | Categórica (3 valores) | Customer Segment |
| category_name | Categórica (50 valores) | Category Name |
| quantity | Numérica | Order Item Quantity |
| product_price | Numérica | Product Price |
| discount_rate | Numérica, entre 0 y 1 | Order Item Discount Rate |
| order_month | Numérica, entre 1 y 12 | Fecha del pedido |
| order_day_of_week | Numérica, entre 0 y 6 | Fecha del pedido |
| order_hour | Numérica, entre 0 y 23 | Fecha del pedido |

Se descartaron cuatro grupos de columnas: las que tienen fuga de información; las redundantes, como los días programados, que dependen solo del modo de envío; los identificadores y datos personales, como nombres, calles y códigos postales; y las columnas constantes o vacías.

Todo el preprocesamiento se integró en un Pipeline de scikit-learn (Pedregosa et al., 2011), de modo que el objeto que se entrena es el mismo que usa el servicio y ambos no pueden desincronizarse. El pipeline aplica una codificación one-hot a las siete variables categóricas, que agrupa las categorías con menos de 50 registros y tolera categorías nuevas; luego estandariza las seis variables numéricas y, por último, aplica el clasificador. Los datos se dividieron en un 80 % para entrenamiento (144.415 registros) y un 20 % para prueba (36.104 registros), de forma estratificada y con una semilla fija.

## Fase 3: ingeniería del modelo

Un modelo base que siempre predice la clase mayoritaria obtiene una exactitud de 0,548. Para superarlo, se compararon tres algoritmos mediante validación cruzada estratificada de cinco particiones sobre el conjunto de entrenamiento (Tabla 7).

**Tabla 7**

*Comparación de algoritmos mediante validación cruzada*

| Algoritmo | F1 promedio | Desviación estándar |
| --- | --- | --- |
| HistGradientBoostingClassifier | 0,6986 | 0,0024 |
| Random Forest (100 árboles, profundidad 15) | 0,6957 | 0,0019 |
| Regresión logística | 0,6794 | 0,0026 |

Se eligió HistGradientBoostingClassifier porque obtuvo el mejor F1 y porque se entrena en pocos segundos, lo que permite reentrenarlo desde la API. Sus hiperparámetros se ajustaron con GridSearchCV, usando tres particiones y 24 combinaciones (Tabla 8). El F1 en validación cruzada subió de 0,699 a 0,712.

**Tabla 8**

*Ajuste de hiperparámetros*

| Hiperparámetro | Valores probados | Mejor valor |
| --- | --- | --- |
| learning_rate | 0,05; 0,1; 0,2 | 0,2 |
| max_iter | 200; 400 | 400 |
| max_depth | Sin límite; 10 | Sin límite |
| l2_regularization | 0; 1 | 1,0 |

## Fase 4: evaluación del modelo

El modelo cumple el criterio de éxito en el conjunto de prueba, formado por 36.104 pedidos que no vio durante el entrenamiento, y supera al modelo base en 19 puntos de exactitud (Tabla 9).

**Tabla 9**

*Métricas en el conjunto de prueba*

| Métrica | Valor | Valor mínimo | Cumple |
| --- | --- | --- | --- |
| Exactitud (accuracy) | 0,7394 | 0,70 | Sí |
| F1 | 0,7340 | 0,70 | Sí |
| ROC-AUC | 0,8284 | 0,80 | Sí |
| Precisión | 0,8335 | No aplica | No aplica |
| Sensibilidad (recall) | 0,6557 | No aplica | No aplica |

**Tabla 10**

*Matriz de confusión en el conjunto de prueba*

| Valor real | Predicción: a tiempo | Predicción: tardía |
| --- | --- | --- |
| A tiempo | 13.716 | 2.592 |
| Tardía | 6.816 | 12.980 |

Cuando el modelo predice una entrega tardía, acierta en el 83 % de los casos, por lo que sus alertas son confiables. En cambio, detecta el 66 % de los pedidos que realmente llegan tarde, es decir, uno de cada tres retrasos no se anticipa. Este límite es la consecuencia esperable de no usar variables con fuga de información: parte de los retrasos depende de factores que el conjunto de datos no registra, como el transportista, el inventario o el clima.

La importancia de las variables se calculó por permutación sobre 5.000 pedidos de prueba (Figura 3). El modo de envío pesa más que las otras doce variables juntas, lo que confirma lo observado en el análisis exploratorio. La categoría, el precio y la cantidad casi no aportan.

**Figura 3**

*Importancia de las variables por permutación*

**[INSERTAR AQUÍ LA FIGURA 3. Archivo: docs/img/figura_3_importancia_variables.png]**

El pipeline completo se guardó con joblib junto con un archivo de métricas que incluye los hiperparámetros y los valores válidos de cada variable categórica. Al iniciar, el servicio registra este modelo como versión 1.

## Fase 5: despliegue

### Servicio de inteligencia artificial

El servicio se construyó con FastAPI (Ramírez, 2018), que genera automáticamente la especificación OpenAPI y la documentación interactiva Swagger a partir del código, y valida las entradas con Pydantic. El acceso a PostgreSQL se realiza con SQLAlchemy. El servicio reutiliza el mismo procedimiento de entrenamiento del cuaderno, de modo que, con los mismos datos, el reentrenamiento desde la API reproduce exactamente las métricas originales. La Tabla 11 relaciona los servicios con los requisitos del enunciado.

**Tabla 11**

*Servicios de la API REST*

| Requisito | Método y ruta | Función |
| --- | --- | --- |
| a. Enviar datos y obtener la predicción | POST /api/predicciones | Devuelve la predicción, la probabilidad y la versión del modelo, y guarda el resultado |
| b. Historial de predicciones | GET /api/predicciones | Lista paginada y filtrable con los datos enviados y el resultado |
| c. Métricas del modelo | GET /api/metricas | Métricas, matriz de confusión, hiperparámetros y criterio de calidad |
| d. Reentrenamiento | POST /api/modelos/reentrenar | Entrena una versión nueva con los datos activos |
| e. Envío del archivo de entrenamiento | POST /api/datasets | Carga un archivo CSV en modo agregar o reemplazar |
| Versiones | GET /api/modelos y POST /api/modelos/{version}/activar | Lista las versiones y permite volver a una anterior |
| Apoyo al formulario | GET /api/opciones y GET /api/destinos | Valores válidos y combinaciones de mercado, región y país |
| Operación | GET /api/predicciones/{id}, GET /api/datasets y GET /api/salud | Detalle de una predicción, archivos cargados y estado del servicio |

Para realizar una predicción, el cliente envía los datos del pedido: tipo de pago, modo de envío, mercado, región, país, segmento del cliente, categoría del producto, cantidad, precio unitario, descuento y fecha del pedido. El servicio obtiene de la fecha el mes, el día de la semana y la hora, y responde con la predicción (1 para entrega tardía y 0 para entrega a tiempo), la probabilidad de entrega tardía, la versión del modelo y la fecha del registro.

El servicio valida todas las entradas (Tabla 12). La documentación interactiva se encuentra en la ruta /docs del servicio y una copia de la especificación se incluye en el repositorio.

**Tabla 12**

*Validaciones y códigos de respuesta*

| Situación | Código de respuesta |
| --- | --- |
| Categoría desconocida o número fuera de rango | 422 |
| Archivo CSV con columnas incorrectas o con otra extensión | 400 |
| Archivo mayor a 200 MB | 413 |
| Reentrenamiento mientras otro está en curso | 409 |
| Predicción o versión inexistente | 404 |
| Ausencia de un modelo activo | 503 |

### Base de datos

La base de datos PostgreSQL 16 se crea únicamente con el script schema.sql del repositorio, que Docker Compose ejecuta al crear el contenedor (Figura 4). Está formada por cinco tablas (Tabla 13): las dos primeras guardan los datos, las dos siguientes guardan los modelos y sus predicciones, y una tabla intermedia une ambos grupos.

**Figura 4**

*Diagrama entidad-relación de la base de datos*

**[INSERTAR AQUÍ LA FIGURA 4. Archivo: docs/img/figura_4_diagrama_bd.png]**

**Tabla 13**

*Tablas de la base de datos*

| Tabla | Contenido |
| --- | --- |
| datasets | Cada archivo de entrenamiento enviado: nombre, formato, cantidad de registros y si está activo |
| datos_entrenamiento | Los registros preparados, con las trece variables y el objetivo, ligados a su archivo |
| versiones_modelo | Cada entrenamiento: hiperparámetros, métricas, matriz de confusión, archivo del modelo y si cumple la calidad |
| versiones_datasets | Tabla intermedia de la relación de muchos a muchos: qué archivos de entrenamiento se usaron en cada versión del modelo |
| predicciones | Cada predicción: datos enviados, resultado, probabilidad, versión del modelo y fecha |

El script define restricciones de verificación sobre los rangos válidos, claves foráneas entre las tablas y un índice único parcial que garantiza que exista un solo modelo activo a la vez. La tabla versiones_datasets resuelve la relación de muchos a muchos entre versiones del modelo y archivos de entrenamiento: una versión se entrena con uno o más archivos, y un archivo puede usarse en varias versiones. Así queda registrado con qué datos exactos se entrenó cada modelo, aunque después esos archivos se reemplacen. Para generar la base se ejecuta el comando docker compose up desde la raíz del repositorio y, después, el script de carga inicial del servicio, que inserta los 180.519 registros en unos seis segundos y registra el modelo del cuaderno como versión 1.

### Cliente web

El cliente web se desarrolló con React 19, TypeScript y Vite, y consume todos los servicios de la API en cuatro secciones (Tabla 14).

**Tabla 14**

*Secciones del cliente web*

| Sección | Funcionalidad | Servicios que utiliza |
| --- | --- | --- |
| Evaluar pedido | Formulario con listas dependientes de mercado, región y país; el resultado se muestra como una etiqueta de envío con la probabilidad y un sello | GET /api/opciones, GET /api/destinos y POST /api/predicciones |
| Historial | Tabla paginada con filtro por resultado y detalle de los datos enviados | GET /api/predicciones |
| Modelo y métricas | Métricas frente al criterio de calidad, matriz de confusión, reentrenamiento, comparación entre versiones y reversión | GET /api/metricas, GET /api/modelos, POST /api/modelos/reentrenar y POST /api/modelos/{version}/activar |
| Datos de entrenamiento | Carga de archivos CSV, modo agregar o reemplazar y lista de archivos | POST /api/datasets y GET /api/datasets |

El diseño se elaboró con la skill oficial frontend-design de Anthropic. Se tomó como concepto una mesa de despacho logístico, con tipografía Barlow, una paleta sobria con un acento ámbar y colores rojo y verde reservados para el estado de la entrega, siempre acompañados de un ícono y un texto. La interfaz se adapta a pantallas desde 320 píxeles de ancho y puede usarse con el teclado. Las Figuras 5 a 8 muestran las cuatro secciones.

**Figura 5**

*Sección Evaluar pedido*

**[INSERTAR AQUÍ LA FIGURA 5. Archivo: docs/img/figura_5_evaluar_pedido.png]**

**Figura 6**

*Sección Historial de predicciones*

**[INSERTAR AQUÍ LA FIGURA 6. Archivo: docs/img/figura_6_historial.png]**

**Figura 7**

*Sección Modelo y métricas*

**[INSERTAR AQUÍ LA FIGURA 7. Archivo: docs/img/figura_7_modelo_metricas.png]**

**Figura 8**

*Sección Datos de entrenamiento*

**[INSERTAR AQUÍ LA FIGURA 8. Archivo: docs/img/figura_8_datos_entrenamiento.png]**

## Fase 6: monitoreo y mantenimiento

Una versión nueva del modelo solo reemplaza a la activa si cumple el criterio de calidad definido en la fase 1. En caso contrario, se guarda como versión inactiva y el servicio sigue funcionando con la anterior (Figura 9). En ambos casos, la API responde con la comparación de métricas entre las dos versiones.

**Figura 9**

*Flujo de reentrenamiento con control de calidad*

**[INSERTAR AQUÍ LA FIGURA 9. Archivo: docs/img/figura_9_flujo_reentrenamiento.png]**

Cada predicción guarda los datos enviados, el resultado, la probabilidad y la versión del modelo que la generó, y cada versión guarda los archivos con que se entrenó. Así es posible auditar cualquier decisión desde la predicción hasta los datos de origen. Cada entrenamiento produce un archivo de modelo y un registro con sus métricas, y cualquier versión anterior puede volver a activarse desde la API o desde el cliente. Un mecanismo de bloqueo impide dos reentrenamientos simultáneos. El reentrenamiento puede ejecutarse en modo rápido, con los mejores hiperparámetros encontrados en el cuaderno (unos diez segundos), o en modo completo, con GridSearchCV (varios minutos).

## Aseguramiento de la calidad

CRISP-ML(Q) exige identificar los riesgos de cada fase y definir controles para mitigarlos (Studer et al., 2021). La Tabla 15 resume los aplicados en el proyecto.

**Tabla 15**

*Riesgos y controles por fase*

| Fase | Riesgo | Control |
| --- | --- | --- |
| 1. Negocio y datos | Métricas engañosas por fuga de información | Análisis de las columnas posteriores al envío y aserción en el cuaderno |
| 1. Negocio y datos | Criterio de éxito ambiguo | Umbrales numéricos definidos antes de entrenar |
| 2. Ingeniería de datos | Preprocesamiento distinto en producción | Preprocesamiento dentro del pipeline que usa el servicio |
| 2. Ingeniería de datos | Categorías nuevas en producción | Tolerancia a categorías desconocidas y validación en la API |
| 3. Ingeniería del modelo | Sobreajuste o elección del modelo por azar | Validación cruzada estratificada con baja variación entre particiones |
| 3. Ingeniería del modelo | Resultados no reproducibles | Semilla fija y orden estable de los datos |
| 4. Evaluación | Aprobar un modelo deficiente | Evaluación en datos no vistos y aserción del criterio |
| 5. Despliegue | Entradas inválidas | Validación de tipos, rangos y categorías, y restricciones en la base de datos |
| 5. Despliegue | Errores en el código | 18 pruebas automatizadas con una base de datos de prueba separada |
| 6. Monitoreo | Un reentrenamiento empeora el modelo | Control de calidad, versionado y reversión |
| 6. Monitoreo | Falta de trazabilidad | Registro de los datos, el resultado y la versión de cada predicción, y de los archivos con que se entrenó cada versión |

Las 18 pruebas automatizadas, desarrolladas con pytest, cubren la preparación de los datos, el entrenamiento y todos los servicios de la API. Utilizan una base de datos independiente, por lo que no modifican los datos reales.

## Herramientas utilizadas

El proyecto se desarrolló con Python 3.14, TypeScript y SQL. Para el análisis y el modelado se usaron pandas, NumPy, scikit-learn, matplotlib, seaborn y Jupyter. El servicio se construyó con FastAPI, Pydantic, SQLAlchemy y Uvicorn, sobre PostgreSQL 16 ejecutado con Docker Compose. El cliente se desarrolló con React 19, Vite y React Router. La calidad se controló con pytest, oxlint y el compilador de TypeScript. Como apoyo se utilizó la inteligencia artificial generativa Claude Code para el análisis, el código y la documentación, y el control de versiones se realizó con Git y GitHub, con revisión de solicitudes de cambio asistida por inteligencia artificial.

## Conclusiones

El modelo cumple el criterio de éxito, con una exactitud de 0,739, un F1 de 0,734 y un ROC-AUC de 0,828, frente a 0,548 del modelo base, y es realista, porque solo usa información disponible al registrar el pedido.

La detección de la fuga de información fue la decisión más importante del proyecto. Un modelo que usara el estado de la entrega o los días reales de envío habría mostrado cerca de un 97 % de exactitud, pero no serviría en la práctica.

El modo de envío explica la mayor parte del riesgo. Los envíos First Class llegan tarde en el 95 % de los casos, lo que sugiere revisar el plazo que se promete para ese modo.

La sensibilidad de 66 % refleja el límite de los datos disponibles. Incorporar información del transportista, del inventario o del clima sería la mejora natural para una siguiente iteración del ciclo.

Por último, el ciclo de vida queda cerrado: el servicio incorpora datos nuevos, vuelve a entrenar el modelo con control de calidad, conserva sus versiones y permite volver a una anterior, tal como propone la fase 6 de CRISP-ML(Q).

## Referencias

Constante, F., Silva, F., & Pereira, A. (2019). *DataCo smart supply chain for big data analysis* (Versión 5) [Conjunto de datos]. Mendeley Data. https://doi.org/10.17632/8gx2fvg2k6.5

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, E. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825-2830.

Ramírez, S. (2018). *FastAPI* [Software]. https://fastapi.tiangolo.com

Studer, S., Bui, T. B., Drescher, C., Hanuschkin, A., Winkler, L., Peters, S., & Müller, K.-R. (2021). Towards CRISP-ML(Q): A machine learning process model with quality assurance methodology. *Machine Learning and Knowledge Extraction, 3*(2), 392-413. https://doi.org/10.3390/make3020020
