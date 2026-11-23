import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { api, ErrorApi, type Categoria, type Destino, type PedidoEntrada, type Prediccion } from '../api'
import { Aviso, Encabezado } from '../components/comunes'
import EtiquetaEnvio from '../components/EtiquetaEnvio'

function ahoraLocal() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

const PEDIDO_INICIAL: PedidoEntrada = {
  payment_type: 'DEBIT',
  shipping_mode: 'Standard Class',
  market: 'LATAM',
  order_region: 'South America',
  order_country: 'Brasil',
  customer_segment: 'Consumer',
  category_name: 'Cleats',
  quantity: 1,
  product_price: 59.99,
  discount_rate: 0.05,
  order_date: ahoraLocal(),
}

const azar = <T,>(lista: T[]) => lista[Math.floor(Math.random() * lista.length)]

export default function Evaluar() {
  const [opciones, setOpciones] = useState<Record<Categoria, string[]> | null>(null)
  const [destinos, setDestinos] = useState<Destino[]>([])
  const [pedido, setPedido] = useState<PedidoEntrada>(PEDIDO_INICIAL)
  const [resultado, setResultado] = useState<Prediccion | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorCarga, setErrorCarga] = useState<string | null>(null)
  const refEtiqueta = useRef<HTMLDivElement>(null)

  useEffect(() => {
    Promise.all([api.opciones(), api.destinos()])
      .then(([o, d]) => {
        setOpciones(o.opciones)
        setDestinos(d)
      })
      .catch((e: ErrorApi) => setErrorCarga(e.message))
  }, [])

  // Cascada mercado -> región -> país usando las combinaciones reales de los datos
  const mercados = useMemo(() => {
    const desdeDatos = [...new Set(destinos.map((d) => d.market))]
    return desdeDatos.length ? desdeDatos : (opciones?.market ?? [])
  }, [destinos, opciones])
  const regiones = useMemo(() => {
    const r = [...new Set(destinos.filter((d) => d.market === pedido.market).map((d) => d.order_region))]
    return destinos.length ? r : (opciones?.order_region ?? [])
  }, [destinos, opciones, pedido.market])
  const paises = useMemo(() => {
    const p = destinos.filter((d) => d.market === pedido.market && d.order_region === pedido.order_region).map((d) => d.order_country)
    return (destinos.length ? p : (opciones?.order_country ?? [])).filter((x) => !opciones || opciones.order_country.includes(x))
  }, [destinos, opciones, pedido.market, pedido.order_region])

  const cambiar = <K extends keyof PedidoEntrada>(campo: K, valor: PedidoEntrada[K]) => {
    setPedido((anterior) => {
      const nuevo = { ...anterior, [campo]: valor }
      if (campo === 'market') {
        const r = destinos.find((d) => d.market === valor)
        nuevo.order_region = r?.order_region ?? ''
        nuevo.order_country = r?.order_country ?? ''
      }
      if (campo === 'order_region') {
        nuevo.order_country = destinos.find((d) => d.market === nuevo.market && d.order_region === valor)?.order_country ?? ''
      }
      return nuevo
    })
  }

  const cargarEjemplo = () => {
    if (!opciones || !destinos.length) return
    const destino = azar(destinos.filter((d) => opciones.order_country.includes(d.order_country)))
    setPedido({
      payment_type: azar(opciones.payment_type),
      shipping_mode: azar(opciones.shipping_mode),
      market: destino.market,
      order_region: destino.order_region,
      order_country: destino.order_country,
      customer_segment: azar(opciones.customer_segment),
      category_name: azar(opciones.category_name),
      quantity: 1 + Math.floor(Math.random() * 5),
      product_price: azar([24.99, 49.98, 59.99, 129.99, 199.99, 299.98, 399.98]),
      discount_rate: azar([0, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25]),
      order_date: ahoraLocal(),
    })
    setResultado(null)
  }

  const enviar = async (e: FormEvent) => {
    e.preventDefault()
    setCargando(true)
    setError(null)
    try {
      setResultado(await api.predecir(pedido))
      if (window.matchMedia('(max-width: 1100px)').matches) {
        refEtiqueta.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    } catch (err) {
      setError((err as ErrorApi).message)
    } finally {
      setCargando(false)
    }
  }

  const selector = (campo: Categoria, etiqueta: string, lista: string[], ayuda?: string) => (
    <div className="campo">
      <label htmlFor={campo}>{etiqueta}</label>
      <select id={campo} value={pedido[campo]} onChange={(e) => cambiar(campo, e.target.value)} required>
        {!lista.includes(pedido[campo]) && <option value="">Selecciona…</option>}
        {lista.map((v) => (
          <option key={v} value={v}>
            {v}
          </option>
        ))}
      </select>
      {ayuda && <span className="ayuda">{ayuda}</span>}
    </div>
  )

  return (
    <>
      <Encabezado titulo="Evaluar pedido">
        Antes de despachar, revisa si el pedido corre riesgo de llegar tarde. El modelo usa solo datos conocidos al registrar el pedido.
      </Encabezado>

      {errorCarga && (
        <Aviso titulo="No se pudo cargar el formulario">
          {errorCarga}
        </Aviso>
      )}

      {opciones && (
        <div className="evaluar">
          <form className="bloque formulario" onSubmit={enviar}>
            <fieldset className="grupo">
              <legend>Envío</legend>
              <div className="grupo-campos">
              {selector('shipping_mode', 'Modo de envío', opciones.shipping_mode, 'La variable que más influye en el riesgo')}
              {selector('payment_type', 'Tipo de pago', opciones.payment_type)}
              </div>
            </fieldset>

            <fieldset className="grupo">
              <legend>Destino</legend>
              <div className="grupo-campos">
              {selector('market', 'Mercado', mercados)}
              {selector('order_region', 'Región', regiones)}
              {selector('order_country', 'País', paises)}
              </div>
            </fieldset>

            <fieldset className="grupo">
              <legend>Cliente y producto</legend>
              <div className="grupo-campos">
              {selector('customer_segment', 'Segmento del cliente', opciones.customer_segment)}
              {selector('category_name', 'Categoría del producto', opciones.category_name)}
              <div className="campo">
                <label htmlFor="quantity">Cantidad</label>
                <input
                  id="quantity"
                  type="number"
                  min={1}
                  max={1000}
                  step={1}
                  required
                  value={pedido.quantity}
                  onChange={(e) => cambiar('quantity', Number(e.target.value))}
                />
              </div>
              <div className="campo">
                <label htmlFor="product_price">Precio unitario (USD)</label>
                <input
                  id="product_price"
                  type="number"
                  min={0}
                  step={0.01}
                  required
                  value={pedido.product_price}
                  onChange={(e) => cambiar('product_price', Number(e.target.value))}
                />
              </div>
              <div className="campo">
                <label htmlFor="discount_rate">Descuento (%)</label>
                <input
                  id="discount_rate"
                  type="number"
                  min={0}
                  max={100}
                  step={1}
                  required
                  value={Math.round(pedido.discount_rate * 100)}
                  onChange={(e) => cambiar('discount_rate', Number(e.target.value) / 100)}
                />
              </div>
              </div>
            </fieldset>

            <fieldset className="grupo">
              <legend>Fecha</legend>
              <div className="grupo-campos">
              <div className="campo">
                <label htmlFor="order_date">Fecha y hora del pedido</label>
                <input
                  id="order_date"
                  type="datetime-local"
                  required
                  value={pedido.order_date}
                  onChange={(e) => cambiar('order_date', e.target.value)}
                />
                <span className="ayuda">Se usan el mes, el día de la semana y la hora</span>
              </div>
              </div>
            </fieldset>

            {error && <Aviso titulo="El modelo no pudo evaluar el pedido">{error}</Aviso>}

            <div className="acciones">
              <button className="boton boton-principal" type="submit" disabled={cargando}>
                {cargando ? 'Evaluando…' : 'Evaluar pedido'}
              </button>
              <button className="boton" type="button" onClick={cargarEjemplo} disabled={cargando}>
                Llenar con un pedido de ejemplo
              </button>
            </div>
          </form>

          <div className="columna-etiqueta" ref={refEtiqueta}>
            <EtiquetaEnvio resultado={resultado} pedido={pedido} cargando={cargando} />
          </div>
        </div>
      )}
    </>
  )
}
