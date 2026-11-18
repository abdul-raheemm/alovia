import type {
  CheckinHistory,
  CheckinInput,
  CheckinResult,
  SymptomCharts,
  SymptomVocabulary,
} from '@alovia/shared'
import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'

import { api } from './services'
import { cannotReach } from './symptoms'
import { HOME_KEY } from './useJourneyHome'

const CHECKIN_PATH = '/patient/symptoms/checkins'

/** GET /patient/symptoms/vocabulary: the log form for her pregnancy week (§5). */
export function useVocabulary() {
  return useQuery({
    queryKey: ['symptom-vocabulary'],
    queryFn: () => api.get<SymptomVocabulary>('/patient/symptoms/vocabulary'),
  })
}

/** GET own check-ins and chart data (§4.3). */
export function useCheckins() {
  return useQuery({
    queryKey: ['symptom-checkins'],
    queryFn: () => api.get<CheckinHistory[]>(CHECKIN_PATH),
  })
}

export function useSymptomCharts() {
  return useQuery({
    queryKey: ['symptom-charts'],
    queryFn: () => api.get<SymptomCharts>('/patient/symptoms/charts'),
  })
}

/** After a check-in: home (logged today, weekly summary), calendar dots, history, charts. */
function refreshAfterCheckin(queryClient: QueryClient) {
  for (const key of [HOME_KEY, ['journey-calendar'], ['symptom-checkins'], ['symptom-charts']]) {
    void queryClient.invalidateQueries({ queryKey: key })
  }
}

/** POST a check-in. Never retried automatically (no duplicate records). */
export function useSubmitCheckin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: CheckinInput) => api.post<CheckinResult>(CHECKIN_PATH, body),
    onSuccess: () => refreshAfterCheckin(queryClient),
  })
}

// DEC-060 / ERROR_HANDLING.md: an urgent check-in that could not reach the backend is kept in
// memory and sent when possible. shortcut: lost if the page is reloaded before it is sent;
// a durable queue (IndexedDB) would be the upgrade if that ever matters.
const pending: CheckinInput[] = []
let timer: ReturnType<typeof setInterval> | undefined

async function flush(): Promise<void> {
  while (pending.length > 0) {
    try {
      await api.post<CheckinResult>(CHECKIN_PATH, pending[0])
      pending.shift()
    } catch (e) {
      if (cannotReach(e)) return // still unreachable: try again later
      pending.shift() // refused by the backend (e.g. not offered any more): drop it
    }
  }
  if (timer !== undefined) clearInterval(timer)
  timer = undefined
}

export function queueCheckin(body: CheckinInput): void {
  pending.push(body)
  if (timer === undefined) {
    timer = setInterval(() => void flush(), 30_000)
    window.addEventListener('online', () => void flush(), { once: true })
  }
}

/** For tests: how many check-ins are waiting to be sent. */
export function pendingCount(): number {
  return pending.length
}
