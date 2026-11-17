import { createApiClient, createAuthClient } from '@alovia/shared'
import { QueryClient } from '@tanstack/react-query'

import { config } from './config'

// Only created after main.tsx has checked that the settings exist.
export const authClient = createAuthClient(
  config.supabaseUrl ?? '',
  config.supabasePublishableKey ?? '',
)

export const api = createApiClient({
  baseUrl: config.apiBaseUrl ?? '',
  getToken: async () => (await authClient.auth.getSession()).data.session?.access_token ?? null,
  // ERROR_HANDLING §5: 401 → sign out and return to sign-in
  onAuthError: () => void authClient.auth.signOut(),
})

export const queryClient = new QueryClient({
  // the API client already retries GETs (ERROR_HANDLING §2); do not retry twice
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
})
