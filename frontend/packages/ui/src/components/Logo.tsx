/** Letter mark "A" in white on the primary colour, plus the wordmark (DESIGN_SYSTEM §2).
 * TODO(OPEN): a real logo later. */
export function Logo({ withWordmark = true }: { withWordmark?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2 font-bold text-text">
      <span
        aria-hidden="true"
        className="inline-flex size-9 items-center justify-center rounded-full bg-primary text-lg text-on-primary"
      >
        A
      </span>
      {withWordmark ? (
        <span className="text-xl">Alovia</span>
      ) : (
        <span className="sr-only">Alovia</span>
      )}
    </span>
  )
}
