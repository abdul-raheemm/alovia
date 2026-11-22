import { userMessage, type MedicalRecord, type RecordDownload } from '@alovia/shared'
import { Button, Card, ErrorState, FieldError, PageSkeleton, TextAreaField } from '@alovia/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Upload } from 'lucide-react'
import { useId, useRef, useState } from 'react'

import { formatDateTime } from '../../app/patients'
import { api } from '../../app/services'
import { StickyActions } from '../StickyActions'

export const RECORD_TYPES: Record<MedicalRecord['file_type'], string> = {
  ultrasound: 'Ultrasound',
  blood_report: 'Blood report',
  prescription: 'Prescription',
  other: 'Other',
}
// a hint for the file picker only; the server checks type, signature and size (config.yaml)
const ACCEPT = '.pdf,.jpg,.jpeg,.png'

/** Dashboard §14: upload to the private store, list, download through a 5-minute link.
 * Records are not deleted in v1 and patients do not see them in v1. */
export function RecordsTab({ patientId }: { patientId: string }) {
  const qc = useQueryClient()
  const key = ['doctor-records', patientId]
  const list = useQuery({
    queryKey: key,
    queryFn: () => api.get<MedicalRecord[]>(`/doctor/patients/${patientId}/records`),
  })
  const fileRef = useRef<HTMLInputElement>(null)
  const fileId = useId()
  const typeId = useId()
  const [fileType, setFileType] = useState<MedicalRecord['file_type']>('ultrasound')
  const [note, setNote] = useState('')
  const [problem, setProblem] = useState<string | null>(null)
  const upload = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData()
      form.append('file', file)
      form.append('file_type', fileType)
      if (note.trim()) form.append('note', note.trim())
      return api.post<MedicalRecord>(`/doctor/patients/${patientId}/records`, form)
    },
    onSuccess: () => {
      setNote('')
      if (fileRef.current) fileRef.current.value = ''
      void qc.invalidateQueries({ queryKey: key })
    },
  })
  const download = useMutation({
    mutationFn: (id: string) => api.get<RecordDownload>(`/doctor/records/${id}/download`),
    onSuccess: (link) => window.open(link.url, '_blank', 'noopener'),
  })

  return (
    <div className="flex flex-col gap-6">
      <section aria-labelledby="upload-heading" className="flex flex-col gap-3">
        <h2 id="upload-heading">Upload a record</h2>
        <form
          noValidate
          className="flex max-w-xl flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault()
            const file = fileRef.current?.files?.[0]
            setProblem(file ? null : 'Choose a file.')
            if (file) upload.mutate(file)
          }}
        >
          <div className="flex flex-col gap-1">
            <label htmlFor={fileId} className="font-semibold">
              File
            </label>
            <input
              id={fileId}
              ref={fileRef}
              type="file"
              accept={ACCEPT}
              aria-invalid={problem ? true : undefined}
              aria-describedby={problem ? `${fileId}-error` : undefined}
              className="min-h-11"
            />
            <FieldError id={`${fileId}-error`} message={problem ?? undefined} />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor={typeId} className="font-semibold">
              Type
            </label>
            <select
              id={typeId}
              value={fileType}
              onChange={(e) => setFileType(e.target.value as MedicalRecord['file_type'])}
              className="min-h-11 rounded-sm border border-border bg-surface px-3 text-base text-text"
            >
              {Object.entries(RECORD_TYPES).map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
          </div>
          <TextAreaField
            label="Note (optional)"
            value={note}
            maxLength={500}
            onChange={(e) => setNote(e.target.value)}
          />
          {upload.isError && (
            <p role="alert" className="text-urgent">
              {userMessage(upload.error, 'doctor')}
            </p>
          )}
          <StickyActions>
            <Button type="submit" className="self-start" loading={upload.isPending}>
              <Upload aria-hidden="true" className="size-5" />
              Upload
            </Button>
          </StickyActions>
        </form>
      </section>
      <section aria-labelledby="records-heading" className="flex flex-col gap-3">
        <h2 id="records-heading">Records</h2>
        {download.isError && (
          <p role="alert" className="text-urgent">
            {userMessage(download.error, 'doctor')}
          </p>
        )}
        {list.isPending ? (
          <PageSkeleton />
        ) : list.isError ? (
          <ErrorState
            message={userMessage(list.error, 'doctor')}
            onRetry={() => void list.refetch()}
          />
        ) : list.data.length === 0 ? (
          <Card>
            <p>No records yet.</p>
          </Card>
        ) : (
          <ul className="flex flex-col gap-3">
            {list.data.map((r) => (
              <li key={r.id}>
                <Card className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-col gap-1">
                    <p className="font-semibold">{r.original_filename}</p>
                    <p className="text-sm text-muted">
                      {RECORD_TYPES[r.file_type]} · {formatDateTime(r.uploaded_at)}
                      {r.uploaded_by_name ? ` · ${r.uploaded_by_name}` : ''}
                    </p>
                    {r.note && <p className="whitespace-pre-line">{r.note}</p>}
                  </div>
                  <Button
                    variant="secondary"
                    loading={download.isPending && download.variables === r.id}
                    onClick={() => download.mutate(r.id)}
                    aria-label={`Download ${r.original_filename}`}
                  >
                    <Download aria-hidden="true" className="size-5" />
                    Download
                  </Button>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
