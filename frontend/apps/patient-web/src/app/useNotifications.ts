import type { DoctorNote, Notification } from '@alovia/shared'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from './services'

const NOTIFICATIONS_KEY = ['notifications']

/** GET /patient/notifications: the backend creates any that are due, then returns the
 * unread ones (§10.2: generated when she opens the app). */
export function useNotifications() {
  return useQuery({
    queryKey: NOTIFICATIONS_KEY,
    queryFn: () => api.get<Notification[]>('/patient/notifications'),
  })
}

/** POST /patient/notifications/{id}/read or /dismiss; either removes it from the bar. */
export function useMarkNotification() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'read' | 'dismiss' }) =>
      api.post<null>(`/patient/notifications/${id}/${action}`, {}),
    onSettled: () => queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_KEY }),
  })
}

/** GET /patient/doctor-notes: notes her doctors shared, newest first (§10.3). */
export function useDoctorNotes() {
  return useQuery({
    queryKey: ['doctor-notes'],
    queryFn: () => api.get<DoctorNote[]>('/patient/doctor-notes'),
  })
}
