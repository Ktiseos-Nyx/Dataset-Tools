import { useMemo, useReducer } from 'react'

export interface Actions<T> {
  setLeft: () => void
  setRight: () => void
  set: (value: T) => void
  toggle: () => void
}

function useToggle<T = boolean>(): [boolean, Actions<T>]
function useToggle<T>(defaultValue: T): [T, Actions<T>]
function useToggle<T, U>(
  defaultValue: T,
  reverseValue: U,
): [T | U, Actions<T | U>]
function useToggle<D, R>(
  defaultValue: D = false as unknown as D,
  reverseValue?: R,
) {
  const [state, dispatch] = useReducer(
    (
      state: D | R,
      action:
        | { type: 'toggle' }
        | { type: 'set'; payload: D | R }
        | { type: 'setLeft' }
        | { type: 'setRight' },
    ) => {
      const reverseValueOrigin = (
        reverseValue === undefined ? !defaultValue : reverseValue
      ) as D | R

      switch (action.type) {
        case 'toggle':
          return state === defaultValue ? reverseValueOrigin : defaultValue
        case 'set':
          return action.payload
        case 'setLeft':
          return defaultValue
        case 'setRight':
          return reverseValueOrigin
        default:
          return state
      }
    },
    defaultValue,
  )

  return [
    state,
    useMemo(() => {
      return {
        toggle: () => dispatch({ type: 'toggle' }),
        set: (value: D | R) => dispatch({ type: 'set', payload: value }),
        setLeft: () => dispatch({ type: 'setLeft' }),
        setRight: () => dispatch({ type: 'setRight' }),
      }
    }, [dispatch]),
  ]
}

export default useToggle
