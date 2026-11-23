import { useCallback, useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { api, type Salud } from './api'
import Evaluar from './pages/Evaluar'
import Historial from './pages/Historial'
import Modelo from './pages/Modelo'
import Datos from './pages/Datos'

const SECCIONES = [
  { ruta: '/evaluar', nombre: 'Evaluar pedido' },
  { ruta: '/historial', nombre: 'Historial' },
  { ruta: '/modelo', nombre: 'Modelo y métricas' },
  { ruta: '/datos', nombre: 'Datos de entrenamiento' },
]

export default function App() {
  const [salud, setSalud] = useState<Salud | null>(null)
  const [sinConexion, setSinConexion] = useState(false)

  const revisarSalud = useCallback(() => {
    api
      .salud()
      .then((s) => {
        setSalud(s)
        setSinConexion(false)
      })
      .catch(() => setSinConexion(true))
  }, [])

  useEffect(() => {
    revisarSalud()
    const intervalo = setInterval(revisarSalud, 15000)
    return () => clearInterval(intervalo)
  }, [revisarSalud])

  return (
    <div className="app">
      <aside className="riel">
        <div className="marca">
          <svg width="34" height="34" viewBox="0 0 32 32" aria-hidden="true">
            <path d="M4 9l7-6h17v26H11l-7-6z" fill="#e9eef1" />
            <circle cx="10" cy="16" r="2.5" fill="#22313c" />
            <rect x="15" y="10" width="9" height="12" rx="1" fill="#f5b300" />
          </svg>
          <div>
            <div className="marca-nombre">DataCo</div>
            <div className="marca-sub">Riesgo de entrega tardía</div>
          </div>
        </div>
        <nav className="nav" aria-label="Secciones">
          {SECCIONES.map((s) => (
            <NavLink key={s.ruta} to={s.ruta} className="nav-enlace">
              {s.nombre}
            </NavLink>
          ))}
        </nav>
        <div className="riel-estado" aria-live="polite">
          {sinConexion ? (
            <span>
              <span className="luz mal" />
              Servicio de IA sin conexión
            </span>
          ) : salud ? (
            <>
              <span>
                <span className={`luz ${salud.base_datos ? 'ok' : 'mal'}`} />
                Base de datos {salud.base_datos ? 'conectada' : 'sin conexión'}
              </span>
              <span>
                <span className={`luz ${salud.modelo_cargado ? 'ok' : 'mal'}`} />
                {salud.modelo_cargado ? `Modelo activo: versión ${salud.version_modelo}` : 'Sin modelo activo'}
              </span>
            </>
          ) : (
            <span>Conectando…</span>
          )}
        </div>
      </aside>

      <main className="trabajo">
        <Routes>
          <Route path="/" element={<Navigate to="/evaluar" replace />} />
          <Route path="/evaluar" element={<Evaluar />} />
          <Route path="/historial" element={<Historial />} />
          <Route path="/modelo" element={<Modelo alCambiarModelo={revisarSalud} />} />
          <Route path="/datos" element={<Datos alCambiarModelo={revisarSalud} />} />
          <Route path="*" element={<Navigate to="/evaluar" replace />} />
        </Routes>
      </main>
    </div>
  )
}
