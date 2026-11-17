import type { JourneyHome } from '@alovia/shared'
import { useQuery } from '@tanstack/react-query'

import { api } from './services'

export const HOME_KEY = ['journey-home']

/** Everything the Journey screens need (GET /patient/journey/home). */
export function useJourneyHome() {
  return useQuery({
    queryKey: HOME_KEY,
    queryFn: () => api.get<JourneyHome>('/patient/journey/home'),
  })
}
