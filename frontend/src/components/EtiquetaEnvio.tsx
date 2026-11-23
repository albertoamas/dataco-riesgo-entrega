import { formato, type PedidoEntrada, type Prediccion } from '../api'

interface Props {
  resultado: Prediccion | null
  pedido: PedidoEntrada
  cargando: boolean
}

/** El resultado de la predicción, presentado como etiqueta de envío con su sello. */
export default function EtiquetaEnvio({ resultado, pedido, cargando }: Props) {
  if (!resultado) {
    return (
      <div className="etiqueta etiqueta-vacia" aria-live="polite">
        <span className="etiqueta-ojal" aria-hidden="true" />
        <div className="etiqueta-cabecera">
          <span>Etiqueta sin evaluar</span>
        </div>
        <div className="etiqueta-ruta">
          {pedido.order_country || 'Destino'}
          <span>{[pedido.order_region, pedido.shipping_mode].filter(Boolean).join(', ') || 'Completa los datos del pedido'}</span>
        </div>
        <p className="etiqueta-explicacion">
          {cargando
            ? 'Consultando al modelo…'
            : 'Completa el pedido y presiona «Evaluar pedido». El modelo estimará la probabilidad de que la entrega llegue tarde.'}
        </p>
      </div>
    )
  }

  const p = resultado.probabilidad_tardia
  const tarde = resultado.prediccion === 1
  const d = resultado.datos_entrada
  return (
    <div className="etiqueta" aria-live="polite">
      <span className="etiqueta-ojal" aria-hidden="true" />
      <div className="etiqueta-cabecera">
        <span>Predicción n.º {resultado.id}</span>
        <span>Modelo v{resultado.version_modelo}</span>
      </div>

      <div className="etiqueta-ruta">
        {d.order_country}
        <span>
          {d.order_region}, {d.market}
        </span>
      </div>
      <div className="etiqueta-ruta" style={{ marginTop: '0.75rem', fontSize: 'var(--t-lg)' }}>
        {d.shipping_mode}
        <span>
          {d.quantity} × {d.category_name}
        </span>
      </div>

      <div className="etiqueta-cifra">
        <div className="cifra-fila">
          <div className="valor">{formato.probabilidad(p)}</div>
          {/* key fuerza a repetir la animación del sello en cada predicción */}
          <div key={resultado.id} className={`sello ${tarde ? 'sello-tarde' : 'sello-tiempo'}`}>
            {tarde ? 'Llega tarde' : 'A tiempo'}
          </div>
        </div>
        <div className="rotulo">probabilidad de entrega tardía</div>
        <div
          className="medidor"
          role="meter"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(p * 100)}
          aria-label="Probabilidad de entrega tardía"
        >
          <div className="medidor-relleno" style={{ width: `${p * 100}%`, background: tarde ? 'var(--tarde)' : 'var(--tiempo)' }} />
          <div className="medidor-umbral" title="Umbral de decisión: 50 %" />
        </div>
        <div className="medidor-escala">
          <span>0 %</span>
          <span>umbral 50 %</span>
          <span>100 %</span>
        </div>
      </div>

      <div className="etiqueta-pie">
        <span>{formato.fecha(resultado.fecha)}</span>
        <span>{tarde ? 'Priorizar despacho' : 'Despacho normal'}</span>
      </div>
    </div>
  )
}
