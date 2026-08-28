import { Suspense, lazy } from 'react'

const BackgroundCanvas = lazy(() =>
  import('./BackgroundCanvas').then((m) => ({ default: m.BackgroundCanvas }))
)

/**
 * Scene wrapper: positions the 3D canvas fixed behind all content.
 * Uses React.lazy + Suspense so the canvas doesn't block initial paint.
 * Fallback: plain void-colored div (coding_conventions.md rule 9).
 */
export function SceneWrapper() {
  return (
    <div
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
      }}
    >
      <Suspense
        fallback={
          <div
            style={{
              width: '100%',
              height: '100%',
              backgroundColor: 'var(--color-void)',
            }}
          />
        }
      >
        <BackgroundCanvas />
      </Suspense>
    </div>
  )
}
