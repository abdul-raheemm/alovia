import { describe, expect, it, vi } from 'vitest'

import { ApiError, createApiClient, NETWORK_ERROR } from './api'
import { userMessage } from './messages'

function jsonResponse(status: number, body: unknown, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  })
}

function client(fetchFn: typeof fetch, extra: Partial<Parameters<typeof createApiClient>[0]> = {}) {
  return createApiClient({
    baseUrl: 'http://api.test/api/v1',
    getToken: async () => 'tok',
    retryDelaysMs: [0, 0],
    fetchFn,
    ...extra,
  })
}

describe('api client', () => {
  it('returns data from the envelope and sends the bearer token', async () => {
    const fetchFn = vi.fn(async () => jsonResponse(200, { data: { ok: 1 }, error: null }))
    await expect(client(fetchFn).get('/me')).resolves.toEqual({ ok: 1 })
    const [url, init] = fetchFn.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('http://api.test/api/v1/me')
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok')
  })

  it('turns an error envelope into ApiError with code, fields and request id', async () => {
    const fetchFn = vi.fn(async () =>
      jsonResponse(
        400,
        { data: null, error: { code: 'VALIDATION_ERROR', message: 'Bad.', fields: { a: 'x' } } },
        { 'X-Request-ID': 'rid1' },
      ),
    )
    const err = await client(fetchFn)
      .post('/x', {})
      .catch((e: unknown) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({
      status: 400,
      code: 'VALIDATION_ERROR',
      fields: { a: 'x' },
      requestId: 'rid1',
    })
  })

  it('retries GET twice on server errors, then succeeds', async () => {
    const fetchFn = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(503, { data: null, error: { code: 'SERVICE_UNAVAILABLE', message: '' } }),
      )
      .mockRejectedValueOnce(new TypeError('offline'))
      .mockResolvedValueOnce(jsonResponse(200, { data: 'ok', error: null }))
    await expect(client(fetchFn as typeof fetch).get('/x')).resolves.toBe('ok')
    expect(fetchFn).toHaveBeenCalledTimes(3)
  })

  it('never retries POST (no duplicate records)', async () => {
    const fetchFn = vi.fn(async () =>
      jsonResponse(503, { data: null, error: { code: 'SERVICE_UNAVAILABLE', message: '' } }),
    )
    await expect(client(fetchFn).post('/x', {})).rejects.toMatchObject({
      code: 'SERVICE_UNAVAILABLE',
    })
    expect(fetchFn).toHaveBeenCalledTimes(1)
  })

  it('gives up after the timeout with a network error', async () => {
    const fetchFn = vi.fn(
      (_url: string | URL | Request, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () =>
            reject(new DOMException('aborted', 'AbortError')),
          )
        }),
    )
    const c = client(fetchFn as typeof fetch, { timeoutMs: 10, retryDelaysMs: [] })
    await expect(c.get('/slow')).rejects.toMatchObject({ code: NETWORK_ERROR, status: 0 })
  })

  it('calls onAuthError on 401', async () => {
    const onAuthError = vi.fn()
    const fetchFn = vi.fn(async () =>
      jsonResponse(401, { data: null, error: { code: 'AUTH_REQUIRED', message: 'x' } }),
    )
    await expect(client(fetchFn, { onAuthError }).get('/me')).rejects.toBeInstanceOf(ApiError)
    expect(onAuthError).toHaveBeenCalledOnce()
  })
})

describe('userMessage (ERROR_HANDLING.md §1)', () => {
  it('maps codes to the documented wording', () => {
    const e = (code: string, message = '') => new ApiError(400, code, message, null, 'rid9')
    expect(userMessage(e('AUTH_REQUIRED'), 'patient')).toBe('Please sign in again.')
    expect(userMessage(e('FORBIDDEN'), 'patient')).toBe("You don't have access to this.")
    expect(userMessage(e('NOT_FOUND'), 'patient')).toBe("We couldn't find this.")
    expect(userMessage(e('CONFLICT', 'This code has already been used.'), 'patient')).toBe(
      'This code has already been used.',
    )
    expect(userMessage(e(NETWORK_ERROR), 'patient')).toBe(
      "We can't connect right now. Please try again.",
    )
    expect(userMessage(e('INTERNAL_ERROR'), 'patient')).toBe(
      'Something went wrong. Please try again.',
    )
    expect(userMessage(e('INTERNAL_ERROR'), 'doctor')).toBe(
      'Something went wrong. Please try again. (Request ID: rid9)',
    )
  })
})
