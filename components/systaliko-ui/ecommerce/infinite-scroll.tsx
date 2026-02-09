'use client';
import { Spinner } from '@/components/systaliko-ui/shadcn/spinner';
import {
  AnimatePresence,
  motion,
  useInView,
  UseInViewOptions,
} from 'motion/react';
import React from 'react';

interface InfiniteScrollProps extends React.ComponentPropsWithRef<'div'> {
  isPending: boolean;
  currentItemsLength: number;
  allItemsCount: number | null | undefined;
  loadMore: () => void;
}
interface InfiniteScrollCellProps extends React.ComponentPropsWithRef<'div'> {
  skelton?: React.ReactNode;
  amount?: UseInViewOptions['amount'];
}

export function InfiniteScrollCell({
  skelton,
  amount,
  children,
  ...props
}: InfiniteScrollCellProps) {
  const ref = React.useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, {
    once: true,
    amount,
  });

  return (
    <div ref={ref} {...props}>
      <AnimatePresence mode="wait">
        {!isInView ? (
          <motion.div
            key="skeleton"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{
              ease: 'easeOut',
            }}
          >
            {skelton}
          </motion.div>
        ) : (
          <motion.div
            key="content"
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              ease: 'easeOut',
            }}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function InfiniteScroll({
  currentItemsLength,
  isPending,
  allItemsCount,
  loadMore,
  children,
  ...props
}: InfiniteScrollProps) {
  const ref = React.useRef<HTMLDivElement | null>(null);
  const allLoaded = currentItemsLength === allItemsCount;
  const hasMore = !allLoaded && currentItemsLength > 0;

  React.useEffect(() => {
    const { current } = ref;

    if (isPending || allLoaded || !current) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !isPending && !allLoaded) {
          loadMore();
        }
      },
      { threshold: 1 },
    );

    observer.observe(current);

    return () => {
      observer.disconnect();
    };
  }, [isPending, allLoaded, currentItemsLength, loadMore]);

  return (
    <div {...props}>
      {children}
      {isPending && hasMore && (
        <div className="flex justify-center py-4">
          <Spinner />
        </div>
      )}
      {hasMore && <div ref={ref} />}
    </div>
  );
}
