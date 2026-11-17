/** Light / dark / follow-the-system theme (DESIGN_SYSTEM §3). The choice is kept in this
 * browser only (essential storage, DEC-027). index.html runs applyStoredTheme() before React
 * starts, so the page never flashes the wrong theme. */
export type ThemeChoice = 'light' | 'dark' | 'system'

const KEY = 'alovia-theme'

export function getThemeChoice(): ThemeChoice {
  try {
    const v = localStorage.getItem(KEY)
    return v === 'light' || v === 'dark' ? v : 'system'
  } catch {
    return 'system'
  }
}

export function resolveTheme(choice: ThemeChoice, prefersDark: boolean): 'light' | 'dark' {
  if (choice === 'system') return prefersDark ? 'dark' : 'light'
  return choice
}

export function applyTheme(choice: ThemeChoice): void {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  document.documentElement.dataset.theme = resolveTheme(choice, prefersDark)
}

export function setThemeChoice(choice: ThemeChoice): void {
  try {
    if (choice === 'system') localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, choice)
  } catch {
    // storage blocked (private mode): the choice still applies until the page reloads
  }
  applyTheme(choice)
}

/** Keep "system" in step when the OS setting changes while the app is open. */
export function watchSystemTheme(): () => void {
  const media = window.matchMedia('(prefers-color-scheme: dark)')
  const onChange = () => {
    if (getThemeChoice() === 'system') applyTheme('system')
  }
  media.addEventListener('change', onChange)
  return () => media.removeEventListener('change', onChange)
}
