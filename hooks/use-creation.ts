/* eslint-disable react-hooks/refs -- ahooks useCreation intentionally memoizes via refs during render */
import { isEqual } from 'es-toolkit/predicate'
import { useRef } from 'react'
import type { DependencyList } from 'react'

export function useCreation<T>(factory: () => T, deps: DependencyList) {
  const { current } = useRef({
    deps,
    obj: undefined as T,
    initialized: false,
  })

  if (current.initialized === false || !isEqual(current.deps, deps)) {
    current.deps = deps
    current.obj = factory()
    current.initialized = true
  }

  return current.obj
}
