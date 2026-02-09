'use client'

import { useState, useMemo, useCallback, Children } from 'react'

export function useInfiniteList({
  pageSize,
  initialItems,
  initialPage = 1,
}: {
  pageSize: number
  initialItems?: unknown[]
  initialPage?: number
}) {
  const [requestedPage, setRequestedPage] = useState(initialPage)

  const bias = useMemo(() => {
    const bias = Math.max(0, (initialItems?.length ?? 0) - pageSize)
    if (bias !== pageSize && bias !== 0) {
      console.warn(
        `[useInfiniteList] bias (${bias}) differs from pageSize (${pageSize}). ` +
          `This will cause instantly displayed items to be appended with more items when the next page loads.`
      )
    }
    return bias
  }, [initialItems?.length, pageSize])

  const displayLimit = requestedPage * pageSize

  const nextPage = useCallback(() => {
    setRequestedPage((current) => current + 1)
  }, [])

  return {
    offset: requestedPage * pageSize + bias,
    displayLimit,
    pageSize,
    nextPage,
  }
}

export function MaskedList({
  children,
  displayLimit,
}: ReturnType<typeof useInfiniteList> & { children: React.ReactNode }) {
  const childArray = Children.toArray(children)
  const visibleChildren = childArray.slice(0, displayLimit)
  return <>{visibleChildren}</>
}
