/** Typed client for the Alovia backend (API.md). Every response is the {data, error} envelope.
 *
 * ERROR_HANDLING.md §2: 20 s timeout; GETs retry twice with back-off; POST/PUT/DELETE never
 * retry automatically. A 401 calls onAuthError (the app signs out).
 */

export const NETWORK_ERROR = 'NETWORK_ERROR' // client-side code: offline, timeout, no response

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly fields: Record<string, string> | null
  readonly requestId: string | null

  constructor(
    status: number,
    code: string,
    message: string,
    fields: Record<string, string> | null = null,
    requestId: string | null = null,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fields = fields
    this.requestId = requestId
  }
}

export interface ApiClientOptions {
  baseUrl: string
  getToken: () => Promise<string | null>
  onAuthError?: () => void
  timeoutMs?: number
  retryDelaysMs?: number[]
  fetchFn?: typeof fetch
}

export interface ApiClient {
  get<T>(path: string): Promise<T>
  post<T>(path: string, body: unknown): Promise<T>
  put<T>(path: string, body: unknown): Promise<T>
}

interface Envelope {
  data?: unknown
  error?: { code?: string; message?: string; fields?: Record<string, string> | null } | null
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export function createApiClient({
  baseUrl,
  getToken,
  onAuthError,
  timeoutMs = 20_000,
  retryDelaysMs = [1_000, 3_000],
  fetchFn = (...args) => fetch(...args),
}: ApiClientOptions): ApiClient {
  async function once(method: string, path: string, body?: unknown): Promise<unknown> {
    const token = await getToken()
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs)
    let res: Response
    try {
      res = await fetchFn(`${baseUrl}${path}`, {
        method,
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      })
    } catch {
      throw new ApiError(0, NETWORK_ERROR, 'No response from the server.')
    } finally {
      clearTimeout(timer)
    }
    const requestId = res.headers.get('X-Request-ID')
    let json: Envelope | null = null
    try {
      json = (await res.json()) as Envelope
    } catch {
      json = null
    }
    if (res.ok && json && 'data' in json && !json.error) return json.data
    const err = json?.error
    throw new ApiError(
      res.status,
      err?.code ?? (res.status >= 500 ? 'INTERNAL_ERROR' : 'UNKNOWN'),
      err?.message ?? 'Request failed.',
      err?.fields ?? null,
      requestId,
    )
  }

  async function request<T>(
    method: 'GET' | 'POST' | 'PUT',
    path: string,
    body?: unknown,
  ): Promise<T> {
    const delays = method === 'GET' ? retryDelaysMs : []
    for (let attempt = 0; ; attempt++) {
      try {
        return (await once(method, path, body)) as T
      } catch (e) {
        const retriable = e instanceof ApiError && (e.status === 0 || e.status >= 500)
        if (retriable && attempt < delays.length) {
          await sleep(delays[attempt] ?? 0)
          continue
        }
        if (e instanceof ApiError && e.status === 401) onAuthError?.()
        throw e
      }
    }
  }

  return {
    get: <T>(path: string) => request<T>('GET', path),
    post: <T>(path: string, body: unknown) => request<T>('POST', path, body),
    put: <T>(path: string, body: unknown) => request<T>('PUT', path, body),
  }
}
