'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

/* -------------------------------------------------------------------------------------------------
 * Types
 * -----------------------------------------------------------------------------------------------*/

type Align = 'start' | 'center' | 'end'

type Particle = {
  id: number
  content: React.ReactNode
}

type ActionHintContextValue = {
  emit: (content: React.ReactNode) => void
}

/* -------------------------------------------------------------------------------------------------
 * Context
 * -----------------------------------------------------------------------------------------------*/

const ActionHintContext = React.createContext<ActionHintContextValue | null>(
  null
)

export function useActionHint() {
  const context = React.useContext(ActionHintContext)
  if (!context) {
    throw new Error('useActionHint must be used within an ActionHintEmitter')
  }
  return context
}

/* -------------------------------------------------------------------------------------------------
 * ActionHintEmitter
 * -----------------------------------------------------------------------------------------------*/

interface ActionHintEmitterProps {
  children: React.ReactNode
  className?: string
  /** Horizontal alignment of the hint relative to the emitter */
  align?: Align
  /** Vertical margin (gap) between the hint and the emitter in pixels */
  margin?: number
  /** Duration of the fade animation in milliseconds */
  duration?: number
}

export const ActionHintEmitter = React.forwardRef<
  HTMLDivElement,
  ActionHintEmitterProps
>(function ActionHintEmitter(
  { children, className, align = 'center', margin = 4, duration = 1500 },
  forwardedRef
) {
  const [particles, setParticles] = React.useState<Particle[]>([])
  const idRef = React.useRef(0)

  const emit = React.useCallback(
    (content: React.ReactNode) => {
      const id = idRef.current++

      // Clear all existing particles and add new one
      setParticles([{ id, content }])

      // Remove after animation completes
      setTimeout(() => {
        setParticles((prev) => prev.filter((p) => p.id !== id))
      }, duration)
    },
    [duration]
  )

  const contextValue = React.useMemo(() => ({ emit }), [emit])

  return (
    <ActionHintContext.Provider value={contextValue}>
      <div ref={forwardedRef} className={cn('relative inline-flex', className)}>
        {children}
        {particles.map((particle) => (
          <ActionHintParticle
            key={particle.id}
            align={align}
            margin={margin}
            duration={duration}
          >
            {particle.content}
          </ActionHintParticle>
        ))}
      </div>
    </ActionHintContext.Provider>
  )
})

/* -------------------------------------------------------------------------------------------------
 * ActionHintParticle
 * -----------------------------------------------------------------------------------------------*/

const alignToPosition: Record<
  Align,
  { left?: string; right?: string; transform: string }
> = {
  start: { left: '0', transform: 'translateY(-100%)' },
  center: { left: '50%', transform: 'translateX(-50%) translateY(-100%)' },
  end: { right: '0', transform: 'translateY(-100%)' },
}

function ActionHintParticle({
  children,
  align,
  margin,
  duration,
}: {
  children: React.ReactNode
  align: Align
  margin: number
  duration: number
}) {
  const positionStyles = alignToPosition[align]

  return (
    <>
      <style>
        {`
          @keyframes action-hint-fade {
            0% {
              opacity: 1;
              margin-top: var(--action-hint-margin);
            }
            100% {
              opacity: 0;
              margin-top: calc(var(--action-hint-margin) - 1rem);
            }
          }
        `}
      </style>
      <div
        data-slot="action-hint-particle"
        className={cn(
          'pointer-events-none absolute top-0 z-50',
          'rounded-md px-2 py-1 text-xs font-medium whitespace-nowrap shadow-sm',
          'bg-secondary text-secondary-foreground'
        )}
        style={
          {
            ...positionStyles,
            '--action-hint-margin': `${-margin}px`,
            animation: `action-hint-fade ${duration}ms ease-out forwards`,
          } as React.CSSProperties
        }
      >
        {children}
      </div>
    </>
  )
}
