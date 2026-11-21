/** Unsaved Log choices kept on this device only (FRONTEND_REDESIGN §7.5, DEC-109): keyed to the
 * patient, with a time stamp, dropped after `draft_ttl_minutes` and on sign-out. Storage can be
 * missing or blocked (private window); then nothing is kept and the Log still works. */
import type { CommonDraft } from './symptoms'

const PREFIX = 'alovia-log-draft:'

export interface LogDraft {
  warning: Record<string, boolean>
  labourDuration?: string
  drafts: Record<string, CommonDraft>
  savedAt: number // ms since epoch
}

export function saveDraft(userId: string, draft: Omit<LogDraft, 'savedAt'>, now = Date.now()) {
  try {
    localStorage.setItem(PREFIX + userId, JSON.stringify({ ...draft, savedAt: now }))
  } catch {
    // storage unavailable: the draft is simply not kept
  }
}

/** The patient's draft if it is younger than the time to live; an expired one is removed. */
export function loadDraft(userId: string, ttlMinutes: number, now = Date.now()): LogDraft | null {
  try {
    const raw = localStorage.getItem(PREFIX + userId)
    if (!raw) return null
    const draft = JSON.parse(raw) as LogDraft
    if (typeof draft.savedAt !== 'number' || now - draft.savedAt > ttlMinutes * 60_000) {
      localStorage.removeItem(PREFIX + userId)
      return null
    }
    return draft
  } catch {
    return null
  }
}

export function clearDraft(userId: string) {
  try {
    localStorage.removeItem(PREFIX + userId)
  } catch {
    // nothing to clear
  }
}

/** On sign-out: every patient's draft on this device. */
export function clearAllDrafts() {
  try {
    for (const key of Object.keys(localStorage)) {
      if (key.startsWith(PREFIX)) localStorage.removeItem(key)
    }
  } catch {
    // nothing to clear
  }
}
