import type { AppointmentList, JourneyCalendar } from '@alovia/shared'
import { keepPreviousData, useQuery, type QueryClient } from '@tanstack/react-query'

import { api } from './services'
import { HOME_KEY } from './useJourneyHome'

const APPOINTMENTS_KEY = ['appointments']
const CALENDAR_KEY = 'journey-calendar'

/** GET /patient/appointments: upcoming and past (Journey §9.3, UX_FLOWS P8). */
export function useAppointments() {
  return useQuery({
    queryKey: APPOINTMENTS_KEY,
    queryFn: () => api.get<AppointmentList>('/patient/appointments'),
  })
}

/** GET /patient/journey/calendar for the days from..to, inclusive (Journey §9.1-9.2). */
export function useCalendar(from: string, to: string) {
  return useQuery({
    queryKey: [CALENDAR_KEY, from, to],
    queryFn: () => api.get<JourneyCalendar>(`/patient/journey/calendar?from=${from}&to=${to}`),
    // keep the calendar on screen while the next month loads (no flash, focus kept)
    placeholderData: keepPreviousData,
  })
}

/** After an appointment changes: the list, every calendar range and the home's next one. */
export function refreshAppointments(queryClient: QueryClient) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: APPOINTMENTS_KEY }),
    queryClient.invalidateQueries({ queryKey: [CALENDAR_KEY] }),
    queryClient.invalidateQueries({ queryKey: HOME_KEY }),
  ])
}
