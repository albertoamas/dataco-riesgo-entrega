import type { ReactNode } from 'react'

export function Encabezado({ titulo, children }: { titulo: string; children?: ReactNode }) {
  return (
    <header className="encabezado">
      <h1>{titulo}</h1>
      {children && <p>{children}</p>}
    </header>
  )
}

export function Aviso({ tipo = 'error', titulo, children }: { tipo?: 'error' | 'ok' | 'atencion'; titulo?: string; children: ReactNode }) {
  return (
    <div className={`aviso aviso-${tipo}`} role={tipo === 'error' ? 'alert' : 'status'}>
      {titulo && <strong>{titulo}</strong>}
      {children}
    </div>
  )
}

/** Estado de la entrega: siempre con ícono y texto, nunca solo color. */
export function EstadoEntrega({ prediccion }: { prediccion: 0 | 1 }) {
  return prediccion === 1 ? (
    <span className="estado estado-tarde">
      <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
        <path d="M6 1l5 9H1z" fill="currentColor" />
      </svg>
      Entrega tardía
    </span>
  ) : (
    <span className="estado estado-tiempo">
      <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
        <path d="M2 6.5l2.5 2.5L10 3.5" stroke="currentColor" strokeWidth="2" fill="none" />
      </svg>
      A tiempo
    </span>
  )
}

export function Cumple({ cumple }: { cumple: boolean }) {
  return cumple ? (
    <span className="estado estado-tiempo">Cumple criterio</span>
  ) : (
    <span className="estado estado-tarde">No cumple criterio</span>
  )
}
