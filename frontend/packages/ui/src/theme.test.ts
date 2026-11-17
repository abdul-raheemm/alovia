import { afterEach, describe, expect, it, vi } from 'vitest'

import { getThemeChoice, resolveTheme, setThemeChoice } from './theme'

describe('theme', () => {
  afterEach(() => localStorage.clear())

  it('follows the system unless the user picked light or dark', () => {
    expect(resolveTheme('system', true)).toBe('dark')
    expect(resolveTheme('system', false)).toBe('light')
    expect(resolveTheme('light', true)).toBe('light')
    expect(resolveTheme('dark', false)).toBe('dark')
  })

  it('remembers the choice and applies it to <html>', () => {
    vi.stubGlobal('matchMedia', () => ({ matches: false }))
    setThemeChoice('dark')
    expect(getThemeChoice()).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
    setThemeChoice('system')
    expect(getThemeChoice()).toBe('system')
    expect(document.documentElement.dataset.theme).toBe('light')
    vi.unstubAllGlobals()
  })
})
