/** Public settings from apps/doctor-web/.env (ENVIRONMENT.md §2). Never put a private value
 * in a VITE_ variable: everything here ends up in the browser. */
const env = import.meta.env

export const config = {
  apiBaseUrl: env.VITE_API_BASE_URL as string | undefined,
  supabaseUrl: env.VITE_SUPABASE_URL as string | undefined,
  supabasePublishableKey: env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined,
}

/** Names of required settings that are missing (shown on screen; values are never shown). */
export const missingConfig: string[] = Object.entries({
  VITE_API_BASE_URL: config.apiBaseUrl,
  VITE_SUPABASE_URL: config.supabaseUrl,
  VITE_SUPABASE_PUBLISHABLE_KEY: config.supabasePublishableKey,
})
  .filter(([, value]) => !value)
  .map(([name]) => name)
