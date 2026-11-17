import { ApiError, NETWORK_ERROR } from './api'

/** What the user sees for an API error (ERROR_HANDLING.md §1). Never technical detail;
 * the doctor app adds the request ID to unexpected errors so it can be found in the logs. */
export function userMessage(error: unknown, app: 'patient' | 'doctor'): string {
  if (!(error instanceof ApiError)) return 'Something went wrong. Please try again.'
  switch (error.code) {
    case 'VALIDATION_ERROR':
    case 'CONFLICT':
      return error.message
    case 'AUTH_REQUIRED':
      return 'Please sign in again.'
    case 'FORBIDDEN':
      return "You don't have access to this."
    case 'NOT_FOUND':
      return "We couldn't find this."
    case 'FILE_TOO_LARGE':
      return 'File too large (max 10 MB)'
    case 'UNSUPPORTED_FILE_TYPE':
      return 'Only PDF, JPG, PNG'
    case 'RATE_LIMITED':
      return 'Too many attempts. Please wait a few minutes.'
    case 'SERVICE_UNAVAILABLE':
    case NETWORK_ERROR:
      return "We can't connect right now. Please try again."
    default: {
      const base = 'Something went wrong. Please try again.'
      return app === 'doctor' && error.requestId ? `${base} (Request ID: ${error.requestId})` : base
    }
  }
}
