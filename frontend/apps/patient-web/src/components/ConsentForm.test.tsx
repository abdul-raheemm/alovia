import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import { ConsentForm } from './ConsentForm'

describe('ConsentForm (CONSENT_TEXT.md)', () => {
  it('starts unticked and enables Continue only when both boxes are ticked', async () => {
    const onAccept = vi.fn()
    render(
      <MemoryRouter>
        <ConsentForm busy={false} onAccept={onAccept} />
      </MemoryRouter>,
    )
    const age = screen.getByRole('checkbox', { name: 'I am 18 years or older.' })
    const agree = screen.getByRole('checkbox', { name: /I have read the Privacy Policy/ })
    const button = screen.getByRole('button', { name: 'Continue' })
    expect(age).not.toBeChecked()
    expect(agree).not.toBeChecked()
    expect(button).toBeDisabled()

    await userEvent.click(age)
    expect(button).toBeDisabled()
    await userEvent.click(agree)
    expect(button).toBeEnabled()
    await userEvent.click(button)
    expect(onAccept).toHaveBeenCalledOnce()
  })
})
