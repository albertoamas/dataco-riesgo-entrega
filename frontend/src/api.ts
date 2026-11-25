// Cliente del Servicio de IA (FastAPI). Todas las rutas están documentadas en /docs del backend.
const BASE = import.meta.env.VITE_API_URL ?? ''

export type Categoria =
  | 'payment_type'
  | 'shipping_mode'
  | 'market'
  | 'order_region'
  | 'order_country'
  | 'customer_segment'
  | 'category_name'

export interface PedidoEntrada {
  payment_type: string
  shipping_mode: string
  market: string
  order_region: string
  order_country: string
  customer_segment: string
  category_name: string
  quantity: number
  product_price: number
  discount_rate: number
  order_date: string
}

export interface Prediccion {
  id: number
  prediccion: 0 | 1
  etiqueta: string
  probabilidad_tardia: number
  version_modelo: number
  fecha: string
  datos_entrada: PedidoEntrada
}

export interface Historial {
  total: number
  pagina: number
  tamano: number
  elementos: Prediccion[]
}

export interface Metricas {
  accuracy: number
  precision: number
  recall: number
  f1_score: number
  roc_auc: number
}

export interface VersionModelo {
  version: number
  algoritmo: string
  hiperparametros: Record<string, number | null>
  metricas: Metricas
  matriz_confusion: number[][]
  registros_entrenamiento: number
  registros_prueba: number
  cumple_calidad: boolean
  activo: boolean
  origen: 'notebook' | 'api'
  fecha_entrenamiento: string
  datasets: { id: number; nombre_archivo: string; total_registros: number }[]
}

export interface MetricasModelo extends VersionModelo {
  criterio_calidad: { min_accuracy: number; min_f1: number; min_roc_auc: number }
  total_predicciones: number
}

export interface Reentrenamiento {
  mensaje: string
  activado: boolean
  nueva_version: VersionModelo
  version_anterior: VersionModelo | null
  duracion_segundos: number
}

export interface Dataset {
  id: number
  nombre_archivo: string
  formato: 'dataco' | 'preparado'
  total_registros: number
  activo: boolean
  fecha_carga: string
}

export interface CargaDataset {
  mensaje: string
  dataset: Dataset
  registros_descartados: number
  total_registros_activos: number
  reentrenamiento: Reentrenamiento | null
}

export interface Salud {
  estado: 'ok'
  base_datos: boolean
  modelo_cargado: boolean
  version_modelo: number | null
}

export interface Destino {
  market: string
  order_region: string
  order_country: string
}

export class ErrorApi extends Error {
  status: number
  constructor(status: number, mensaje: string) {
    super(mensaje)
    this.status = status
  }
}

async function pedir<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  let respuesta: Response
  try {
    respuesta = await fetch(`${BASE}${ruta}`, opciones)
  } catch {
    throw new ErrorApi(0, 'No hay conexión con el servicio de IA. Verifica que el backend esté corriendo en el puerto 8000.')
  }
  const cuerpo = await respuesta.json().catch(() => null)
  if (!respuesta.ok) {
    throw new ErrorApi(respuesta.status, describirError(cuerpo?.detail) ?? `Error ${respuesta.status}`)
  }
  return cuerpo as T
}

// FastAPI devuelve detail como texto o como lista de errores de validación
function describirError(detalle: unknown): string | null {
  if (typeof detalle === 'string') return detalle
  if (Array.isArray(detalle)) {
    return detalle
      .map((e: { loc?: (string | number)[]; msg?: string }) => `${e.loc?.slice(1).join('.') ?? ''}: ${e.msg ?? ''}`)
      .join('; ')
  }
  return null
}

const json = (cuerpo: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(cuerpo),
})

export const api = {
  salud: () => pedir<Salud>('/api/salud'),
  opciones: () => pedir<{ version_modelo: number; opciones: Record<Categoria, string[]> }>('/api/opciones'),
  destinos: () => pedir<Destino[]>('/api/destinos'),
  predecir: (pedido: PedidoEntrada) => pedir<Prediccion>('/api/predicciones', json(pedido)),
  historial: (pagina: number, tamano: number, prediccion?: 0 | 1) => {
    const q = new URLSearchParams({ pagina: String(pagina), tamano: String(tamano) })
    if (prediccion !== undefined) q.set('prediccion', String(prediccion))
    return pedir<Historial>(`/api/predicciones?${q}`)
  },
  metricas: () => pedir<MetricasModelo>('/api/metricas'),
  modelos: () => pedir<VersionModelo[]>('/api/modelos'),
  reentrenar: (buscar_hiperparametros: boolean) =>
    pedir<Reentrenamiento>('/api/modelos/reentrenar', json({ buscar_hiperparametros, activar_si_cumple: true })),
  activar: (version: number) => pedir<VersionModelo>(`/api/modelos/${version}/activar`, { method: 'POST' }),
  datasets: () => pedir<Dataset[]>('/api/datasets'),
  subirDataset: (archivo: File, modo: 'agregar' | 'reemplazar', reentrenar: boolean) => {
    const datos = new FormData()
    datos.append('archivo', archivo)
    datos.append('modo', modo)
    datos.append('reentrenar', String(reentrenar))
    return pedir<CargaDataset>('/api/datasets', { method: 'POST', body: datos })
  },
}

// ---------- Formato ----------
const fechaHora = new Intl.DateTimeFormat('es', { dateStyle: 'medium', timeStyle: 'short' })
const entero = new Intl.NumberFormat('es', { useGrouping: 'always' })

export const formato = {
  fecha: (iso: string) => fechaHora.format(new Date(iso)),
  entero: (n: number) => entero.format(n),
  porcentaje: (n: number, decimales = 1) => `${(n * 100).toFixed(decimales).replace('.', ',')} %`,
  // Evita mostrar 100 % o 0 % cuando el modelo no está totalmente seguro
  probabilidad: (n: number) => (n >= 0.995 ? '> 99 %' : n <= 0.005 ? '< 1 %' : `${Math.round(n * 100)} %`),
  metrica: (n: number) => n.toFixed(3).replace('.', ','),
  dinero: (n: number) => `$${n.toFixed(2)}`,
}

export const NOMBRES_METRICAS: Record<keyof Metricas, string> = {
  accuracy: 'Accuracy',
  precision: 'Precision',
  recall: 'Recall',
  f1_score: 'F1-score',
  roc_auc: 'ROC-AUC',
}

export const NOMBRES_CAMPOS: Record<keyof PedidoEntrada, string> = {
  payment_type: 'Tipo de pago',
  shipping_mode: 'Modo de envío',
  market: 'Mercado',
  order_region: 'Región de destino',
  order_country: 'País de destino',
  customer_segment: 'Segmento del cliente',
  category_name: 'Categoría del producto',
  quantity: 'Cantidad',
  product_price: 'Precio unitario',
  discount_rate: 'Descuento',
  order_date: 'Fecha del pedido',
}
