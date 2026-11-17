import type { JourneyHome, MonthDetail } from '@alovia/shared'
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

/** Month detail (GET /patient/journey/months/{month}). */
export function useMonthDetail(month: number) {
  return useQuery({
    queryKey: ['journey-month', month],
    queryFn: () => api.get<MonthDetail>(`/patient/journey/months/${month}`),
    enabled: Number.isInteger(month) && month >= 1 && month <= 9,
  })
}
