import { isFunction } from 'es-toolkit/predicate'
import { useRef, useState } from 'react'
import { useCreation } from '@/hooks/use-creation'
import { useMemoizedFn } from '@/hooks/use-memoized-fn'
import type { Dispatch, SetStateAction } from 'react'

type ResetState = () => void

export function useResetState<S>(
  initialState: S | (() => S),
): readonly [S, Dispatch<SetStateAction<S>>, ResetState] {
  const initialStateRef = useRef(initialState)
  const initialStateMemo = useCreation(
    () =>
      isFunction(initialStateRef.current)
        ? initialStateRef.current()
        : initialStateRef.current,
    [],
  )

  const [state, setState] = useState(initialStateMemo)

  const resetState = useMemoizedFn(() => {
    setState(initialStateMemo)
  })

  return [state, setState, resetState]
}
