import { useCallback, useEffect, useRef, useState, type DragEvent } from 'react'
import { api, ErrorApi, formato, type CargaDataset, type Dataset } from '../api'
import { Aviso, Encabezado } from '../components/comunes'
import ResultadoReentrenamiento from '../components/ResultadoReentrenamiento'

const COLUMNAS_PREPARADAS =
  'payment_type, shipping_mode, market, order_region, order_country, customer_segment, category_name, quantity, product_price, discount_rate, order_month, order_day_of_week, order_hour, late_delivery_risk'

export default function Datos({ alCambiarModelo }: { alCambiarModelo: () => void }) {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [error, setError] = useState<string | null>(null)
  const [archivo, setArchivo] = useState<File | null>(null)
  const [modo, setModo] = useState<'agregar' | 'reemplazar'>('agregar')
  const [reentrenar, setReentrenar] = useState(true)
  const [subiendo, setSubiendo] = useState(false)
  const [arrastrando, setArrastrando] = useState(false)
  const [resultado, setResultado] = useState<CargaDataset | null>(null)
  const [errorCarga, setErrorCarga] = useState<string | null>(null)
  const entrada = useRef<HTMLInputElement>(null)

  const cargar = useCallback(() => {
    api
      .datasets()
      .then((d) => {
        setDatasets(d)
        setError(null)
      })
      .catch((e: ErrorApi) => setError(e.message))
  }, [])

  useEffect(cargar, [cargar])

  const elegir = (f: File | undefined) => {
    if (!f) return
    setArchivo(f)
    setResultado(null)
    setErrorCarga(f.name.toLowerCase().endsWith('.csv') ? null : 'El archivo debe ser un CSV (.csv).')
  }

  const soltar = (e: DragEvent) => {
    e.preventDefault()
    setArrastrando(false)
    elegir(e.dataTransfer.files[0])
  }

  const subir = async () => {
    if (!archivo) return
    setSubiendo(true)
    setErrorCarga(null)
    setResultado(null)
    try {
      const r = await api.subirDataset(archivo, modo, reentrenar)
      setResultado(r)
      setArchivo(null)
      if (entrada.current) entrada.current.value = ''
      cargar()
      if (r.reentrenamiento) alCambiarModelo()
    } catch (e) {
      setErrorCarga((e as ErrorApi).message)
    } finally {
      setSubiendo(false)
    }
  }

  const activos = datasets.filter((d) => d.activo).reduce((a, d) => a + d.total_registros, 0)

  return (
    <>
      <Encabezado titulo="Datos de entrenamiento">
        Envía nuevos pedidos con su resultado real de entrega para que el modelo aprenda de información actualizada.
      </Encabezado>

      <div className="rejilla-datos">
        <section className="bloque">
          <div className="bloque-titulo">
            <h2>Enviar archivo</h2>
          </div>
          <div className="pila">
            <label
              className={`zona-carga ${arrastrando ? 'arrastrando' : ''}`}
              onDragOver={(e) => {
                e.preventDefault()
                setArrastrando(true)
              }}
              onDragLeave={() => setArrastrando(false)}
              onDrop={soltar}
            >
              <input ref={entrada} type="file" accept=".csv,text/csv" onChange={(e) => elegir(e.target.files?.[0])} />
              <svg width="36" height="36" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M6 2h8l5 5v15H6z" fill="none" stroke="#4f5e69" strokeWidth="1.5" />
                <path d="M14 2v5h5M12.5 18v-7M9.5 13.5l3-3 3 3" fill="none" stroke="#4f5e69" strokeWidth="1.5" />
              </svg>
              {archivo ? (
                <>
                  <strong>{archivo.name}</strong>
                  <span className="ayuda">{(archivo.size / 1024 / 1024).toFixed(1).replace('.', ',')} MB. Selecciona otro archivo para cambiarlo.</span>
                </>
              ) : (
                <>
                  <strong>Arrastra un CSV o selecciónalo</strong>
                  <span className="ayuda">CSV original de DataCo o con las columnas ya preparadas</span>
                </>
              )}
            </label>

            <div className="campo">
              <span className="rotulo" id="modo-carga">
                Qué hacer con los datos actuales
              </span>
              <div className="segmentado" role="group" aria-labelledby="modo-carga">
                <button type="button" aria-pressed={modo === 'agregar'} onClick={() => setModo('agregar')}>
                  Agregar a los existentes
                </button>
                <button type="button" aria-pressed={modo === 'reemplazar'} onClick={() => setModo('reemplazar')}>
                  Reemplazarlos
                </button>
              </div>
              <span className="ayuda">
                {modo === 'agregar'
                  ? 'El modelo se entrenará con los datos actuales más los del archivo.'
                  : 'Los archivos anteriores quedan inactivos y el modelo se entrenará solo con este archivo.'}
              </span>
            </div>

            <label className="casilla">
              <input type="checkbox" checked={reentrenar} onChange={(e) => setReentrenar(e.target.checked)} />
              <span>Entrenar una nueva versión del modelo después de cargar</span>
            </label>

            <div className="acciones">
              <button className="boton boton-principal" onClick={subir} disabled={!archivo || subiendo || !!errorCarga}>
                {subiendo ? (reentrenar ? 'Cargando y entrenando…' : 'Cargando…') : 'Cargar archivo'}
              </button>
            </div>

            {errorCarga && <Aviso titulo="No se pudo cargar el archivo">{errorCarga}</Aviso>}
            {resultado && (
              <Aviso tipo="ok" titulo={resultado.mensaje}>
                {resultado.registros_descartados > 0 && `Se descartaron ${formato.entero(resultado.registros_descartados)} filas con datos incompletos o inválidos. `}
                Ahora hay {formato.entero(resultado.total_registros_activos)} registros activos para entrenar.
              </Aviso>
            )}
            {resultado?.reentrenamiento && <ResultadoReentrenamiento r={resultado.reentrenamiento} />}

            <details>
              <summary style={{ cursor: 'pointer', fontSize: 'var(--t-sm)', color: 'var(--tinta-2)' }}>Formatos de archivo aceptados</summary>
              <div style={{ fontSize: 'var(--t-sm)', color: 'var(--tinta-2)', marginTop: '0.5rem', display: 'grid', gap: '0.5rem' }}>
                <p>
                  <strong>CSV original de DataCo</strong> (DataCoSupplyChainDataset.csv). El servicio selecciona las columnas útiles, calcula mes, día y hora del pedido, y descarta las
                  columnas con fuga de información.
                </p>
                <p>
                  <strong>CSV preparado</strong> con las columnas: <code style={{ wordBreak: 'break-word' }}>{COLUMNAS_PREPARADAS}</code>
                </p>
              </div>
            </details>
          </div>
        </section>

        <section className="bloque">
          <div className="bloque-titulo">
            <h2>Archivos cargados</h2>
            <p className="num">{formato.entero(activos)} registros activos</p>
          </div>
          {error && <Aviso titulo="No se pudieron cargar los archivos">{error}</Aviso>}
          {datasets.length === 0 && !error ? (
            <div className="vacio">
              <p>Todavía no hay datos de entrenamiento. Carga el CSV de DataCo para empezar.</p>
            </div>
          ) : (
            <div className="tabla-marco">
              <table>
                <thead>
                  <tr>
                    <th>Archivo</th>
                    <th>Cargado</th>
                    <th className="der">Registros</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {datasets.map((d) => (
                    <tr key={d.id}>
                      <td>
                        {d.nombre_archivo}
                        <div style={{ color: 'var(--tinta-3)', fontSize: 'var(--t-xs)' }}>{d.formato === 'dataco' ? 'Formato DataCo' : 'Formato preparado'}</div>
                      </td>
                      <td>{formato.fecha(d.fecha_carga)}</td>
                      <td className="der num">{formato.entero(d.total_registros)}</td>
                      <td>
                        <span className={`estado ${d.activo ? 'estado-tiempo' : 'estado-neutro'}`}>{d.activo ? 'En uso' : 'Inactivo'}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </>
  )
}
