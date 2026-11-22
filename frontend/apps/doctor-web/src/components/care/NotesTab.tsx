import { userMessage, type NoteRecord } from '@alovia/shared'
import { Button, Card, CheckboxField, ErrorState, PageSkeleton, TextAreaField } from '@alovia/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { formatDateTime } from '../../app/patients'
import { api } from '../../app/services'
import { StickyActions } from '../StickyActions'

/** Dashboard §15: private (doctors only) or shared, chosen when writing; a private note can
 * be shared later, never the other way; notes are not edited or deleted. */
export function NotesTab({ patientId }: { patientId: string }) {
  const qc = useQueryClient()
  const key = ['doctor-notes', patientId]
  const notes = useQuery({
    queryKey: key,
    queryFn: () => api.get<NoteRecord[]>(`/doctor/patients/${patientId}/notes`),
  })
  const [body, setBody] = useState('')
  const [shared, setShared] = useState(false)
  const [empty, setEmpty] = useState(false)
  const refresh = () => void qc.invalidateQueries({ queryKey: key })
  const write = useMutation({
    mutationFn: () =>
      api.post<NoteRecord>(`/doctor/patients/${patientId}/notes`, {
        body: body.trim(),
        visible_to_patient: shared,
      }),
    onSuccess: () => {
      setBody('')
      setShared(false)
      refresh()
    },
  })
  const share = useMutation({
    mutationFn: (id: string) => api.post<NoteRecord>(`/doctor/notes/${id}/share`, {}),
    onSuccess: refresh,
  })

  return (
    <div className="flex flex-col gap-6">
      <section aria-labelledby="new-note-heading" className="flex flex-col gap-3">
        <h2 id="new-note-heading">New note</h2>
        <form
          noValidate
          className="flex max-w-2xl flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault()
            setEmpty(!body.trim())
            if (body.trim()) write.mutate()
          }}
        >
          <TextAreaField
            label="Note"
            value={body}
            maxLength={2000}
            error={empty ? 'Please write the note.' : undefined}
            onChange={(e) => setBody(e.target.value)}
          />
          <CheckboxField
            label="Share with the patient (she sees it under Doctor notes; this cannot be undone)"
            checked={shared}
            onChange={(e) => setShared(e.target.checked)}
          />
          {write.isError && (
            <p role="alert" className="text-urgent">
              {userMessage(write.error, 'doctor')}
            </p>
          )}
          <StickyActions>
            <Button type="submit" className="self-start" loading={write.isPending}>
              Save note
            </Button>
          </StickyActions>
        </form>
      </section>
      <section aria-labelledby="notes-heading" className="flex flex-col gap-3">
        <h2 id="notes-heading">Notes</h2>
        {notes.isPending ? (
          <PageSkeleton />
        ) : notes.isError ? (
          <ErrorState
            message={userMessage(notes.error, 'doctor')}
            onRetry={() => void notes.refetch()}
          />
        ) : notes.data.length === 0 ? (
          <Card>
            <p>No notes yet.</p>
          </Card>
        ) : (
          <ul className="flex flex-col gap-3">
            {notes.data.map((n) => (
              <li key={n.id}>
                <Card className="flex flex-col gap-2">
                  <p className="text-sm text-muted">
                    {n.doctor_name} · {formatDateTime(n.created_at)} ·{' '}
                    <strong>{n.visible_to_patient ? 'Shared with the patient' : 'Private'}</strong>
                    {n.related_ref?.startsWith('genetic_assessment:') ? ' · genetic review' : ''}
                  </p>
                  <p className="whitespace-pre-line">{n.body}</p>
                  {!n.visible_to_patient && (
                    <Button
                      variant="secondary"
                      className="self-start"
                      loading={share.isPending && share.variables === n.id}
                      onClick={() => share.mutate(n.id)}
                    >
                      Share with patient
                    </Button>
                  )}
                </Card>
              </li>
            ))}
          </ul>
        )}
        {share.isError && (
          <p role="alert" className="text-urgent">
            {userMessage(share.error, 'doctor')}
          </p>
        )}
      </section>
    </div>
  )
}
