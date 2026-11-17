import { Monitor, Moon, Sun } from 'lucide-react'
import { useState } from 'react'

import { cn } from '../cn'
import { getThemeChoice, setThemeChoice, type ThemeChoice } from '../theme'

const OPTIONS: { value: ThemeChoice; label: string; Icon: typeof Sun }[] = [
  { value: 'light', label: 'Light', Icon: Sun },
  { value: 'dark', label: 'Dark', Icon: Moon },
  { value: 'system', label: 'System', Icon: Monitor },
]

/** Theme switch: a labelled group of three radio buttons (keyboard and screen-reader friendly). */
export function ThemeSwitch({ compact = false }: { compact?: boolean }) {
  const [choice, setChoice] = useState<ThemeChoice>(getThemeChoice)
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className={cn('font-semibold', compact && 'sr-only')}>Theme</legend>
      <div className="inline-flex rounded-md border border-border bg-surface p-1">
        {OPTIONS.map(({ value, label, Icon }) => (
          <label
            key={value}
            className={cn(
              'flex min-h-10 cursor-pointer items-center gap-1 rounded-sm px-3 text-sm has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-primary',
              choice === value && 'bg-primary text-on-primary',
            )}
          >
            <input
              type="radio"
              name="theme"
              value={value}
              checked={choice === value}
              onChange={() => {
                setThemeChoice(value)
                setChoice(value)
              }}
              className="sr-only"
            />
            <Icon aria-hidden="true" className="size-4" />
            {label}
          </label>
        ))}
      </div>
    </fieldset>
  )
}
