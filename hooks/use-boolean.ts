import { useMemo } from 'react'
import useToggle from '@/hooks/use-toggle'

export function useBoolean(defaultValue: boolean = false) {
  const [state, actions] = useToggle(defaultValue)

  return [
    state,
    useMemo(
      () => ({
        set: (value: boolean) => actions.set(value),
        setTrue: () => actions.set(true),
        setFalse: () => actions.set(false),
        toggle: () => actions.toggle(),
      }),
      [actions],
    ),
  ] as const
}
