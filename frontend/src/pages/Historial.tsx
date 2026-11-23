import { Fragment, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ErrorApi, formato, NOMBRES_CAMPOS, type Historial as THistorial, type PedidoEntrada } from '../api'
import { Aviso, Encabezado, EstadoEntrega } from '../components/comunes'

const TAMANO = 15
type Filtro = 'todas' | 1 | 0

function Detalle({ datos }: { datos: PedidoEntrada }) {
  const valor = (campo: keyof PedidoEntrada) => {
    const v = datos[campo]
    if (campo === 'product_price') return formato.dinero(Number(v))
    if (campo === 'discount_rate') return formato.porcentaje(Number(v), 0)
    if (campo === 'order_date') return formato.fecha(String(v))
    return String(v)
  }
  return (
    <dl className="lista-datos">
      {(Object.keys(NOMBRES_CAMPOS) as (keyof PedidoEntrada)[]).map((campo) => (
        <div key={campo}>
          <dt>{NOMBRES_CAMPOS[campo]}</dt>
          <dd>{valor(campo)}</dd>
        </div>
      ))}
    </dl>
  )
}

export default function Historial() {
  const [filtro, setFiltro] = useState<Filtro>('todas')
  const [pagina, setPagina] = useState(1)
  const [datos, setDatos] = useState<THistorial | null>(null)
  const [conteo, setConteo] = useState<{ tarde: number; tiempo: number } | null>(null)
  const [abierta, setAbierta] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .historial(pagina, TAMANO, filtro === 'todas' ? undefined : filtro)
      .then((h) => {
        setDatos(h)
        setError(null)
      })
      .catch((e: ErrorApi) => setError(e.message))
  }, [pagina, filtro])

  useEffect(() => {
    Promise.all([api.historial(1, 1, 1), api.historial(1, 1, 0)])
      .then(([t, a]) => setConteo({ tarde: t.total, tiempo: a.total }))
      .catch(() => setConteo(null))
  }, [])

  const paginas = datos ? Math.max(1, Math.ceil(datos.total / TAMANO)) : 1
  const totalConteo = conteo ? conteo.tarde + conteo.tiempo : 0

  const elegirFiltro = (f: Filtro) => {
    setFiltro(f)
    setPagina(1)
    setAbierta(null)
  }

  return (
    <>
      <Encabezado titulo="Historial de predicciones">
        Cada pedido evaluado queda registrado con los datos enviados, el resultado y la versión del modelo que lo evaluó.
      </Encabezado>

      {error && <Aviso titulo="No se pudo cargar el historial">{error}</Aviso>}

      <section className="bloque">
        <div className="bloque-titulo">
          {conteo && totalConteo > 0 ? (
            <div style={{ flex: '1 1 18rem', maxWidth: '28rem' }}>
              <p>
                {formato.entero(totalConteo)} pedidos evaluados: {formato.entero(conteo.tarde)} con entrega tardía y {formato.entero(conteo.tiempo)} a tiempo
              </p>
              <div
                style={{ display: 'flex', gap: 2, height: 8, marginTop: 8 }}
                role="img"
                aria-label={`${conteo.tarde} con entrega tardía, ${conteo.tiempo} a tiempo`}
              >
                {conteo.tarde > 0 && <div style={{ flex: conteo.tarde, background: 'var(--tarde)', borderRadius: 999 }} title={`Entrega tardía: ${conteo.tarde}`} />}
                {conteo.tiempo > 0 && <div style={{ flex: conteo.tiempo, background: 'var(--tiempo)', borderRadius: 999 }} title={`A tiempo: ${conteo.tiempo}`} />}
              </div>
            </div>
          ) : (
            <span />
          )}
          <div className="segmentado" role="group" aria-label="Filtrar por resultado">
            <button aria-pressed={filtro === 'todas'} onClick={() => elegirFiltro('todas')}>
              Todas
            </button>
            <button aria-pressed={filtro === 1} onClick={() => elegirFiltro(1)}>
              Entrega tardía
            </button>
            <button aria-pressed={filtro === 0} onClick={() => elegirFiltro(0)}>
              A tiempo
            </button>
          </div>
        </div>

        {!datos ? (
          !error && <p className="cargando">Cargando historial…</p>
        ) : datos.total === 0 ? (
          <div className="vacio">
            <p>{filtro === 'todas' ? 'Todavía no se evaluó ningún pedido.' : 'No hay predicciones con este resultado.'}</p>
            {filtro === 'todas' && (
              <Link to="/evaluar" className="boton boton-principal">
                Evaluar un pedido
              </Link>
            )}
          </div>
        ) : (
          <>
            <div className="tabla-marco">
              <table>
                <thead>
                  <tr>
                    <th className="der">N.º</th>
                    <th>Fecha</th>
                    <th>Destino</th>
                    <th>Modo de envío</th>
                    <th>Producto</th>
                    <th>Resultado</th>
                    <th className="der">Prob. tardía</th>
                    <th className="der">Modelo</th>
                  </tr>
                </thead>
                <tbody>
                  {datos.elementos.map((p) => (
                    <Fragment key={p.id}>
                      <tr
                        className="fila-abrible"
                        tabIndex={0}
                        aria-expanded={abierta === p.id}
                        onClick={() => setAbierta(abierta === p.id ? null : p.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault()
                            setAbierta(abierta === p.id ? null : p.id)
                          }
                        }}
                      >
                        <td className="der num">{p.id}</td>
                        <td>{formato.fecha(p.fecha)}</td>
                        <td>
                          {p.datos_entrada.order_country}
                          <div style={{ color: 'var(--tinta-3)', fontSize: 'var(--t-xs)' }}>{p.datos_entrada.order_region}</div>
                        </td>
                        <td>{p.datos_entrada.shipping_mode}</td>
                        <td>
                          {p.datos_entrada.quantity} × {p.datos_entrada.category_name}
                        </td>
                        <td>
                          <EstadoEntrega prediccion={p.prediccion} />
                        </td>
                        <td className="der num">{formato.probabilidad(p.probabilidad_tardia)}</td>
                        <td className="der num">v{p.version_modelo}</td>
                      </tr>
                      {abierta === p.id && (
                        <tr className="fila-detalle">
                          <td colSpan={8}>
                            <Detalle datos={p.datos_entrada} />
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="paginacion">
              <span>
                Página {pagina} de {paginas}. Selecciona una fila para ver todos los datos enviados.
              </span>
              <div>
                <button className="boton boton-chico" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>
                  Anterior
                </button>
                <button className="boton boton-chico" disabled={pagina >= paginas} onClick={() => setPagina(pagina + 1)}>
                  Siguiente
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </>
  )
}
