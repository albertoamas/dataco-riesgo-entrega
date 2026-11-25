from ..models import Prediccion, VersionModelo
from ..schemas import DatasetResumen, Metricas, PrediccionSalida, VersionModeloSalida

ETIQUETAS = {0: "A tiempo", 1: "Entrega tardía"}


def version_a_salida(v: VersionModelo) -> VersionModeloSalida:
    return VersionModeloSalida(
        version=v.version,
        algoritmo=v.algoritmo,
        hiperparametros=v.hiperparametros,
        metricas=Metricas(
            accuracy=float(v.accuracy),
            precision=float(v.precision_score),
            recall=float(v.recall),
            f1_score=float(v.f1_score),
            roc_auc=float(v.roc_auc),
        ),
        matriz_confusion=v.matriz_confusion,
        registros_entrenamiento=v.registros_entrenamiento,
        registros_prueba=v.registros_prueba,
        cumple_calidad=v.cumple_calidad,
        activo=v.activo,
        origen=v.origen,
        fecha_entrenamiento=v.fecha_entrenamiento,
        datasets=[DatasetResumen(id=d.id, nombre_archivo=d.nombre_archivo, total_registros=d.total_registros) for d in v.datasets],
    )


def prediccion_a_salida(p: Prediccion) -> PrediccionSalida:
    return PrediccionSalida(
        id=p.id,
        prediccion=p.prediccion,
        etiqueta=ETIQUETAS[p.prediccion],
        probabilidad_tardia=float(p.probabilidad),
        version_modelo=p.version_modelo.version,
        fecha=p.fecha,
        datos_entrada=p.datos_entrada,
    )
