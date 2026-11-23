import { useState } from 'react'
import { formato, NOMBRES_METRICAS, type Metricas, type VersionModelo } from '../api'

/* ---------- Métricas como barras contra el umbral de calidad ---------- */
interface BarrasProps {
  metricas: Metricas
  umbrales: Partial<Record<keyof Metricas, number>>
}

export function BarrasMetricas({ metricas, umbrales }: BarrasProps) {
  const [hover, setHover] = useState<keyof Metricas | null>(null)
  const claves = Object.keys(NOMBRES_METRICAS) as (keyof Metricas)[]
  return (
    <figure style={{ margin: 0 }}>
      <figcaption className="grafico-titulo">Rendimiento en el conjunto de prueba (escala 0 a 1)</figcaption>
      <div className="barras">
        {claves.map((k) => {
          const umbral = umbrales[k]
          return (
            <div
              key={k}
              className="barra-fila"
              onMouseEnter={() => setHover(k)}
              onMouseLeave={() => setHover(null)}
              tabIndex={0}
              onFocus={() => setHover(k)}
              onBlur={() => setHover(null)}
              aria-label={`${NOMBRES_METRICAS[k]}: ${formato.metrica(metricas[k])}${umbral ? `, mínimo exigido ${formato.metrica(umbral)}` : ''}`}
            >
              <span>{NOMBRES_METRICAS[k]}</span>
              <div className="barra-pista">
                <div className="barra-relleno" style={{ width: `${metricas[k] * 100}%`, maxHeight: 24 }} />
                {umbral !== undefined && <div className="barra-umbral" style={{ left: `${umbral * 100}%` }} />}
                {hover === k && (
                  <div className="tooltip" style={{ left: `${metricas[k] * 100}%`, top: 0 }}>
                    {NOMBRES_METRICAS[k]} {formato.metrica(metricas[k])}
                    {umbral !== undefined && ` · mínimo ${formato.metrica(umbral)}`}
                  </div>
                )}
              </div>
              <span className="num" style={{ textAlign: 'right', fontWeight: 600 }}>
                {formato.metrica(metricas[k])}
              </span>
            </div>
          )
        })}
      </div>
      <div className="leyenda">
        <span>
          <span className="muestra" style={{ background: 'var(--pizarra-2)' }} />
          Valor del modelo
        </span>
        <span>
          <span className="muestra muestra-umbral" />
          Mínimo exigido por el criterio de calidad
        </span>
      </div>
    </figure>
  )
}

/* ---------- Matriz de confusión (secuencial, un solo tono) ---------- */
const CLASES = ['A tiempo', 'Entrega tardía']

export function MatrizConfusion({ matriz }: { matriz: number[][] }) {
  const [hover, setHover] = useState<string | null>(null)
  const total = matriz.flat().reduce((a, b) => a + b, 0)
  const maximo = Math.max(...matriz.flat())
  return (
    <figure style={{ margin: 0 }}>
      <figcaption className="grafico-titulo">Matriz de confusión: filas = valor real, columnas = predicción del modelo</figcaption>
      <div className="matriz" role="table" aria-label="Matriz de confusión">
        <span />
        {CLASES.map((c) => (
          <span key={c} className="matriz-eje" role="columnheader">
            Predicho: {c.toLowerCase()}
          </span>
        ))}
        {matriz.map((fila, i) => (
          <div key={i} style={{ display: 'contents' }} role="row">
            <span className="matriz-eje matriz-eje-fila" role="rowheader">
              Real: {CLASES[i].toLowerCase()}
            </span>
            {fila.map((valor, j) => {
              const intensidad = 0.15 + 0.85 * (valor / maximo)
              const oscuro = intensidad > 0.55
              const id = `${i}-${j}`
              const acierto = i === j
              return (
                <div
                  key={j}
                  role="cell"
                  tabIndex={0}
                  className="matriz-celda"
                  style={{
                    background: `color-mix(in srgb, #1d5fae ${Math.round(intensidad * 100)}%, #eef4fb)`,
                    color: oscuro ? '#ffffff' : 'var(--pizarra)',
                  }}
                  onMouseEnter={() => setHover(id)}
                  onMouseLeave={() => setHover(null)}
                  onFocus={() => setHover(id)}
                  onBlur={() => setHover(null)}
                  aria-label={`Real ${CLASES[i]}, predicho ${CLASES[j]}: ${valor} pedidos`}
                >
                  <strong className="num">{formato.entero(valor)}</strong>
                  <small>{acierto ? 'aciertos' : 'errores'}</small>
                  {hover === id && (
                    <div className="tooltip" style={{ left: '50%', top: 0 }}>
                      {formato.porcentaje(valor / total)} del conjunto de prueba
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </figure>
  )
}

/* ---------- Evolución de métricas por versión (3 series, slots categóricos 1-3) ---------- */
const SERIES: { clave: keyof Metricas; color: string }[] = [
  { clave: 'accuracy', color: 'var(--serie-1)' },
  { clave: 'f1_score', color: 'var(--serie-2)' },
  { clave: 'roc_auc', color: 'var(--serie-3)' },
]

export function GraficoVersiones({ versiones }: { versiones: VersionModelo[] }) {
  const [hover, setHover] = useState<number | null>(null)
  const datos = [...versiones].sort((a, b) => a.version - b.version)
  const ancho = 640
  const alto = 220
  const m = { arriba: 12, derecha: 84, abajo: 28, izquierda: 40 }
  const valores = datos.flatMap((v) => SERIES.map((s) => v.metricas[s.clave]))
  const minimo = Math.max(0, Math.floor((Math.min(...valores) - 0.05) * 10) / 10)
  const maximo = Math.min(1, Math.ceil((Math.max(...valores) + 0.02) * 10) / 10)
  const x = (i: number) => m.izquierda + (datos.length === 1 ? (ancho - m.izquierda - m.derecha) / 2 : (i * (ancho - m.izquierda - m.derecha)) / (datos.length - 1))
  const y = (v: number) => m.arriba + ((maximo - v) * (alto - m.arriba - m.abajo)) / (maximo - minimo)
  const ticks = Array.from({ length: Math.round((maximo - minimo) / 0.05) + 1 }, (_, i) => minimo + i * 0.05)
  const ultimo = datos[datos.length - 1]
  // Si las etiquetas finales quedan a menos de 14px entre sí, se omiten (la leyenda y el tooltip identifican las series)
  const posFinales = SERIES.map((s) => y(ultimo.metricas[s.clave])).sort((a, b) => a - b)
  const etiquetasChocan = posFinales.some((v, i) => i > 0 && v - posFinales[i - 1] < 14)

  return (
    <figure style={{ margin: 0 }}>
      <figcaption className="grafico-titulo">Métricas de cada versión entrenada</figcaption>
      <div className="grafico-marco" onMouseLeave={() => setHover(null)}>
        <svg className="grafico-svg" viewBox={`0 0 ${ancho} ${alto}`} role="img" aria-label="Evolución de accuracy, F1 y ROC-AUC por versión del modelo">
          {ticks.map((t) => (
            <g key={t}>
              <line x1={m.izquierda} x2={ancho - m.derecha} y1={y(t)} y2={y(t)} stroke="#dce3e8" strokeWidth={1} />
              <text x={m.izquierda - 8} y={y(t) + 4} textAnchor="end" className="num">
                {t.toFixed(2).replace('.', ',')}
              </text>
            </g>
          ))}
          {datos.map((v, i) => (
            <text key={v.version} x={x(i)} y={alto - 8} textAnchor="middle">
              v{v.version}
            </text>
          ))}
          {hover !== null && <line x1={x(hover)} x2={x(hover)} y1={m.arriba} y2={alto - m.abajo} stroke="#6b7984" strokeWidth={1} />}
          {SERIES.map((s) => (
            <g key={s.clave}>
              {datos.length > 1 && (
                <polyline
                  fill="none"
                  stroke={s.color}
                  strokeWidth={2}
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  points={datos.map((v, i) => `${x(i)},${y(v.metricas[s.clave])}`).join(' ')}
                />
              )}
              {datos.map((v, i) => (
                <circle key={v.version} cx={x(i)} cy={y(v.metricas[s.clave])} r={hover === i ? 5.5 : 4} fill={s.color} stroke="#ffffff" strokeWidth={2} />
              ))}
              {/* etiqueta directa al final de cada serie */}
              {!etiquetasChocan && (
                <text x={x(datos.length - 1) + 10} y={y(ultimo.metricas[s.clave]) + 4}>
                  {NOMBRES_METRICAS[s.clave]}
                </text>
              )}
            </g>
          ))}
          {/* zonas de captura más grandes que las marcas */}
          {datos.map((v, i) => (
            <rect
              key={v.version}
              x={x(i) - (ancho - m.izquierda - m.derecha) / Math.max(datos.length - 1, 1) / 2}
              y={0}
              width={(ancho - m.izquierda - m.derecha) / Math.max(datos.length - 1, 1)}
              height={alto}
              fill="transparent"
              onMouseEnter={() => setHover(i)}
            />
          ))}
        </svg>
        {hover !== null && (
          <div className="tooltip" style={{ left: `${(x(hover) / ancho) * 100}%`, top: `${(m.arriba / alto) * 100}%` }}>
            <strong>Versión {datos[hover].version}</strong>
            {SERIES.map((s) => (
              <div key={s.clave} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span className="muestra" style={{ background: s.color, width: 8, height: 8 }} />
                {NOMBRES_METRICAS[s.clave]} {formato.metrica(datos[hover].metricas[s.clave])}
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="leyenda">
        {SERIES.map((s) => (
          <span key={s.clave}>
            <span className="muestra muestra-linea" style={{ background: s.color }} />
            {NOMBRES_METRICAS[s.clave]}
          </span>
        ))}
      </div>
    </figure>
  )
}
