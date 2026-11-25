import { useCallback, useEffect, useState } from 'react'
import { api, ErrorApi, formato, type MetricasModelo, type Reentrenamiento, type VersionModelo } from '../api'
import { Aviso, Cumple, Encabezado } from '../components/comunes'
import { BarrasMetricas, GraficoVersiones, MatrizConfusion } from '../components/graficos'
import ResultadoReentrenamiento from '../components/ResultadoReentrenamiento'

export default function Modelo({ alCambiarModelo }: { alCambiarModelo: () => void }) {
  const [metricas, setMetricas] = useState<MetricasModelo | null>(null)
  const [versiones, setVersiones] = useState<VersionModelo[]>([])
  const [error, setError] = useState<string | null>(null)
  const [buscar, setBuscar] = useState(false)
  const [entrenando, setEntrenando] = useState(false)
  const [resultado, setResultado] = useState<Reentrenamiento | null>(null)
  const [errorEntreno, setErrorEntreno] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)

  const cargar = useCallback(() => {
    Promise.all([api.metricas(), api.modelos()])
      .then(([m, v]) => {
        setMetricas(m)
        setVersiones(v)
        setError(null)
      })
      .catch((e: ErrorApi) => setError(e.message))
  }, [])

  useEffect(cargar, [cargar])

  const reentrenar = async () => {
    setEntrenando(true)
    setErrorEntreno(null)
    setResultado(null)
    setAviso(null)
    try {
      setResultado(await api.reentrenar(buscar))
      cargar()
      alCambiarModelo()
    } catch (e) {
      setErrorEntreno((e as ErrorApi).message)
    } finally {
      setEntrenando(false)
    }
  }

  const activar = async (version: number) => {
    try {
      await api.activar(version)
      setAviso(`Versión ${version} activada`)
      setResultado(null)
      cargar()
      alCambiarModelo()
    } catch (e) {
      setError((e as ErrorApi).message)
    }
  }

  return (
    <>
      <Encabezado titulo="Modelo y métricas">
        Qué tan bien predice el modelo activo, cómo evolucionó en cada versión y cuándo conviene entrenar una nueva.
      </Encabezado>

      {error && <Aviso titulo="No se pudieron cargar las métricas">{error}</Aviso>}

      {metricas && (
        <>
          <section className="bloque">
            <div className="bloque-titulo">
              <h2>Versión {metricas.version} activa</h2>
              <Cumple cumple={metricas.cumple_calidad} />
            </div>
            <div className="resumen-modelo">
              <span>
                Algoritmo
                <strong>{metricas.algoritmo}</strong>
              </span>
              <span>
                Entrenado
                <strong>{formato.fecha(metricas.fecha_entrenamiento)}</strong>
              </span>
              <span>
                Registros de entrenamiento / prueba
                <strong className="num">
                  {formato.entero(metricas.registros_entrenamiento)} / {formato.entero(metricas.registros_prueba)}
                </strong>
              </span>
              <span>
                Pedidos evaluados con esta versión
                <strong className="num">{formato.entero(metricas.total_predicciones)}</strong>
              </span>
              <span>
                Origen
                <strong>{metricas.origen === 'notebook' ? 'Notebook (CRISP-ML(Q))' : 'Re-entrenamiento desde la API'}</strong>
              </span>
            </div>
            <div className="rejilla-modelo">
              <BarrasMetricas
                metricas={metricas.metricas}
                umbrales={{
                  accuracy: metricas.criterio_calidad.min_accuracy,
                  f1_score: metricas.criterio_calidad.min_f1,
                  roc_auc: metricas.criterio_calidad.min_roc_auc,
                }}
              />
              <MatrizConfusion matriz={metricas.matriz_confusion} />
            </div>
          </section>

          <section className="bloque">
            <div className="bloque-titulo">
              <h2>Entrenar una nueva versión</h2>
              <p>Usa todos los datos de entrenamiento activos. La nueva versión reemplaza a la actual solo si cumple el criterio de calidad.</p>
            </div>
            <div className="pila">
              <label className="casilla">
                <input type="checkbox" checked={buscar} onChange={(e) => setBuscar(e.target.checked)} disabled={entrenando} />
                <span>
                  Buscar los mejores hiperparámetros (GridSearchCV)
                  <span className="ayuda" style={{ display: 'block', color: 'var(--tinta-3)' }}>
                    Puede tardar varios minutos. Sin esta opción se usan los mejores hiperparámetros encontrados en el notebook y tarda unos segundos.
                  </span>
                </span>
              </label>
              <div className="acciones">
                <button className="boton boton-principal" onClick={reentrenar} disabled={entrenando}>
                  {entrenando ? 'Entrenando…' : 'Entrenar nueva versión'}
                </button>
              </div>
              {errorEntreno && <Aviso titulo="No se pudo entrenar">{errorEntreno}</Aviso>}
              {aviso && <Aviso tipo="ok">{aviso}</Aviso>}
              {resultado && <ResultadoReentrenamiento r={resultado} />}
            </div>
          </section>

          <section className="bloque">
            <div className="bloque-titulo">
              <h2>Versiones del modelo</h2>
              <p>Puedes volver a activar cualquier versión anterior.</p>
            </div>
            {versiones.length > 1 && (
              <div style={{ marginBottom: '1.5rem', maxWidth: '44rem' }}>
                <GraficoVersiones versiones={versiones} />
              </div>
            )}
            <div className="tabla-marco">
              <table>
                <thead>
                  <tr>
                    <th>Versión</th>
                    <th>Fecha</th>
                    <th>Origen</th>
                    <th>Entrenada con</th>
                    <th className="der">Registros</th>
                    <th className="der">Accuracy</th>
                    <th className="der">F1</th>
                    <th className="der">ROC-AUC</th>
                    <th>Calidad</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {versiones.map((v) => (
                    <tr key={v.version}>
                      <td>
                        <strong>v{v.version}</strong>
                      </td>
                      <td>{formato.fecha(v.fecha_entrenamiento)}</td>
                      <td>{v.origen === 'notebook' ? 'Notebook' : 'API'}</td>
                      <td>
                        {v.datasets.length === 0 ? (
                          <span style={{ color: 'var(--tinta-3)' }}>Sin registro</span>
                        ) : (
                          v.datasets.map((d) => (
                            <div key={d.id} title={`${formato.entero(d.total_registros)} registros`}>
                              {d.nombre_archivo}
                            </div>
                          ))
                        )}
                      </td>
                      <td className="der num">{formato.entero(v.registros_entrenamiento + v.registros_prueba)}</td>
                      <td className="der num">{formato.metrica(v.metricas.accuracy)}</td>
                      <td className="der num">{formato.metrica(v.metricas.f1_score)}</td>
                      <td className="der num">{formato.metrica(v.metricas.roc_auc)}</td>
                      <td>
                        <Cumple cumple={v.cumple_calidad} />
                      </td>
                      <td className="der">
                        {v.activo ? (
                          <span className="estado estado-neutro">Activa</span>
                        ) : (
                          <button className="boton boton-chico" onClick={() => activar(v.version)}>
                            Activar versión
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </>
  )
}
