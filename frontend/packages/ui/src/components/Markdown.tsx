import { Marked } from 'marked'
import { useMemo } from 'react'

const marked = new Marked({
  gfm: true,
  renderer: {
    // task-list boxes in the documents are text, not form controls (axe: unlabelled inputs)
    checkbox: ({ checked }) => (checked ? '☑ ' : '☐ '),
  },
})

/** Renders one of the project's own Markdown documents (legal pages, credits).
 * Only trusted, committed files from docs/ are passed in — never user input. */
export function Markdown({ source }: { source: string }) {
  const html = useMemo(
    // wide tables scroll sideways on phones; tabindex lets keyboard users scroll them too
    () => marked.parse(source, { async: false }).replaceAll('<table>', '<table tabindex="0">'),
    [source],
  )
  return <div className="prose-legal" dangerouslySetInnerHTML={{ __html: html }} />
}
