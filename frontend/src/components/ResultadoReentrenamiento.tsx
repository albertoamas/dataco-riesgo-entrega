import { formato, NOMBRES_METRICAS, type Metricas, type Reentrenamiento } from '../api'
import { Aviso } from './comunes'

/** Compara la versión recién entrenada con la que estaba activa. */
export default function ResultadoReentrenamiento({ r }: { r: Reentrenamiento }) {
  const nueva = r.nueva_version
  const anterior = r.version_anterior
  const tipo = r.activado ? 'ok' : nueva.cumple_calidad ? 'atencion' : 'error'
  return (
    <Aviso tipo={tipo} titulo={r.mensaje}>
      <span>
        Entrenada con {formato.entero(nueva.registros_entrenamiento)} registros en {r.duracion_segundos.toFixed(1).replace('.', ',')} s.
      </span>
      <table className="comparacion">
        <thead>
          <tr>
            <th>Métrica</th>
            {anterior && <th className="der">v{anterior.version} (anterior)</th>}
            <th className="der">v{nueva.version} (nueva)</th>
            {anterior && <th className="der">Diferencia</th>}
          </tr>
        </thead>
        <tbody>
          {(Object.keys(NOMBRES_METRICAS) as (keyof Metricas)[]).map((k) => {
            const delta = anterior ? nueva.metricas[k] - anterior.metricas[k] : 0
            return (
              <tr key={k}>
                <td>{NOMBRES_METRICAS[k]}</td>
                {anterior && <td className="der num">{formato.metrica(anterior.metricas[k])}</td>}
                <td className="der num">{formato.metrica(nueva.metricas[k])}</td>
                {anterior && (
                  <td className={`der num ${delta > 0.0005 ? 'delta-sube' : delta < -0.0005 ? 'delta-baja' : ''}`}>
                    {delta > 0 ? '+' : ''}
                    {formato.metrica(delta)}
                  </td>
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </Aviso>
  )
}
