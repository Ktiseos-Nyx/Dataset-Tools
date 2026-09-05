"use client";

import {
  Children,
  type ComponentProps,
  type CSSProperties,
  type KeyboardEvent,
  type ReactNode,
  type Ref,
  useCallback,
  useId,
  useRef,
  useState,
} from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const EASE_OUT = [0.22, 1, 0.36, 1] as const;
const DEFAULT_CONTENT_MAX_WIDTH = "min(32rem, calc(100vw - 2rem))";

const TOOLBAR_TRANSITION = {
  width: { duration: 0.2, ease: EASE_OUT },
  opacity: { duration: 0.14, ease: EASE_OUT },
} as const;
const TRIGGER_SURFACE_TRANSITION = { duration: 0.18, ease: EASE_OUT } as const;
// An icon swap is a tiny state change, so keep it snappy: ease-out, well
// under 150ms — the copy button's copy → check treatment, trimmed a touch
// because the swap runs exit-then-enter and the perceived time is doubled.
const TRIGGER_ICON_TRANSITION = {
  duration: 0.1,
  ease: [0.215, 0.61, 0.355, 1],
} as const;
const TRIGGER_ICON_VARIANTS = {
  hidden: { opacity: 0, scale: 0.5 },
  visible: { opacity: 1, scale: 1 },
} as const;
const TOOLBAR_PADDING = 2;
/** Must match the toolbar surface's `border` class. */
const TOOLBAR_BORDER_WIDTH = 1;
const TRIGGER_RADIUS_OPEN = 8;
const TRIGGER_RADIUS_CLOSED = TRIGGER_RADIUS_OPEN + TOOLBAR_PADDING;

type ExpandableToolbarSide = "start" | "end" | "center";
type ExpandableToolbarAnchor = "toolbar" | "trigger";
type ExpandableToolbarTriggerProps = ComponentProps<"button"> & {
  "data-state": "open" | "closed";
};

export type ExpandableToolbarClassNames = {
  triggerWrapper?: string;
  trigger?: string;
  triggerSeparator?: string;
  panel?: string;
  content?: string;
};

export type ExpandableToolbarTriggerRenderProps = {
  open: boolean;
  disabled: boolean;
  label: string;
  controlsId: string;
  triggerProps: ExpandableToolbarTriggerProps;
};

type ExpandableToolbarBaseProps = Omit<
  ComponentProps<"div">,
  "children" | "defaultValue" | "onChange"
> & {
  /** Controlled open state. */
  open?: boolean;
  /** Initial open state for uncontrolled usage. */
  defaultOpen?: boolean;
  /** Called whenever the toolbar requests an open-state change. */
  onOpenChange?: (open: boolean) => void;
  /**
   * Which side of the trigger the content should expand into. `center` splits
   * the children into two panels flanking the trigger, so the toolbar grows
   * symmetrically while the trigger stays put.
   */
  side?: ExpandableToolbarSide;
  /** Whether the full toolbar or only the trigger participates in layout. */
  anchor?: ExpandableToolbarAnchor;
  expandLabel?: string;
  collapseLabel?: string;
  controlsId?: string;
  disabled?: boolean;
  /** Close the toolbar when Escape is pressed inside it. */
  closeOnEscape?: boolean;
  contentMaxWidth?: CSSProperties["maxWidth"];
  classNames?: ExpandableToolbarClassNames;
  children: ReactNode;
};

type ExpandableToolbarDefaultTriggerProps = {
  /** Icon used by the default trigger when the toolbar is closed. */
  expandIcon: ReactNode;
  /** Icon used by the default trigger when the toolbar is open. */
  collapseIcon?: ReactNode;
  renderTrigger?: never;
};

type ExpandableToolbarCustomTriggerProps = {
  expandIcon?: ReactNode;
  collapseIcon?: ReactNode;
  /**
   * Replace the default icon button trigger while keeping the measured panel,
   * ARIA attributes, and open-state plumbing.
   */
  renderTrigger: (props: ExpandableToolbarTriggerRenderProps) => ReactNode;
};

export type ExpandableToolbarProps = ExpandableToolbarBaseProps &
  (ExpandableToolbarDefaultTriggerProps | ExpandableToolbarCustomTriggerProps);

export function ExpandableToolbar({
  open,
  defaultOpen = false,
  onOpenChange,
  side = "start",
  anchor = "toolbar",
  expandIcon,
  collapseIcon,
  expandLabel = "Expand toolbar",
  collapseLabel = "Collapse toolbar",
  controlsId,
  disabled = false,
  closeOnEscape = true,
  contentMaxWidth = DEFAULT_CONTENT_MAX_WIDTH,
  className,
  classNames,
  renderTrigger,
  children,
  role,
  "aria-label": ariaLabel = "Expandable toolbar",
  onKeyDown,
  style,
  ...props
}: ExpandableToolbarProps) {
  const generatedId = useId();
  const panelId = controlsId ?? `${generatedId}-panel`;
  const triggerRef = useRef<HTMLButtonElement>(null);
  const triggerWrapperRef = useRef<HTMLDivElement>(null);
  const [startContentRef, startContentWidth] =
    useMeasuredWidth<HTMLDivElement>();
  const [endContentRef, endContentWidth] = useMeasuredWidth<HTMLDivElement>();
  const [internalOpen, setInternalOpen] = useState(defaultOpen);
  const shouldReduceMotion = useReducedMotion();
  const controlled = open !== undefined;
  const isOpen = controlled ? open : internalOpen;
  const currentLabel = isOpen ? collapseLabel : expandLabel;

  // `center` flanks the trigger with two panels: the first half of the
  // children expands into the start side, the rest into the end side.
  const childArray = Children.toArray(children);
  const splitIndex = Math.ceil(childArray.length / 2);
  const startChildren =
    side === "start"
      ? childArray
      : side === "center"
        ? childArray.slice(0, splitIndex)
        : [];
  const endChildren =
    side === "end"
      ? childArray
      : side === "center"
        ? childArray.slice(splitIndex)
        : [];
  const startPanelId = side === "center" ? `${panelId}-start` : panelId;
  const endPanelId = side === "center" ? `${panelId}-end` : panelId;
  const startPanelWidth = isOpen ? startContentWidth : 0;

  const focusTrigger = useCallback(() => {
    const trigger =
      triggerRef.current ?? getFirstFocusableElement(triggerWrapperRef.current);

    trigger?.focus();
  }, []);

  const setOpen = useCallback(
    (nextOpen: boolean) => {
      if (disabled) return;

      if (!controlled) {
        setInternalOpen(nextOpen);
      }

      onOpenChange?.(nextOpen);
    },
    [controlled, disabled, onOpenChange],
  );

  const toggleOpen = useCallback(() => {
    setOpen(!isOpen);
  }, [isOpen, setOpen]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      onKeyDown?.(event);

      if (event.defaultPrevented) return;

      if (closeOnEscape && isOpen && event.key === "Escape") {
        event.stopPropagation();
        setOpen(false);
        focusTrigger();
        return;
      }

      // `role="toolbar"` promises horizontal arrow-key navigation (ARIA APG),
      // so move focus between the visible controls. Text-entry controls keep
      // the arrows for caret movement.
      if (!TOOLBAR_NAV_KEYS.includes(event.key)) return;

      const activeElement = document.activeElement;

      if (activeElement instanceof HTMLElement && isTextEntry(activeElement)) {
        return;
      }

      // Collapsed panels carry `inert` + `aria-hidden`, so filter on that
      // rather than on layout: `offsetParent` is also null for `position:
      // fixed` elements that are perfectly visible.
      const focusables = Array.from(
        event.currentTarget.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
      ).filter(
        (element) =>
          !element.closest("[inert],[hidden],[aria-hidden='true']"),
      );

      if (focusables.length === 0) return;

      const currentIndex = focusables.indexOf(activeElement as HTMLElement);
      const lastIndex = focusables.length - 1;
      let nextIndex: number;

      if (event.key === "Home") {
        nextIndex = 0;
      } else if (event.key === "End") {
        nextIndex = lastIndex;
      } else if (event.key === "ArrowRight") {
        nextIndex = currentIndex < 0 ? 0 : (currentIndex + 1) % focusables.length;
      } else {
        nextIndex =
          currentIndex < 0
            ? lastIndex
            : (currentIndex - 1 + focusables.length) % focusables.length;
      }

      event.preventDefault();
      focusables[nextIndex]?.focus();
    },
    [closeOnEscape, focusTrigger, isOpen, onKeyDown, setOpen],
  );

  const triggerRadius = isOpen ? TRIGGER_RADIUS_OPEN : TRIGGER_RADIUS_CLOSED;
  const triggerTransition = shouldReduceMotion
    ? { duration: 0 }
    : TRIGGER_SURFACE_TRANSITION;
  const transition = shouldReduceMotion ? { duration: 0 } : TOOLBAR_TRANSITION;
  const triggerProps = {
    type: "button",
    disabled,
    "aria-label": currentLabel,
    "aria-expanded": isOpen,
    "aria-controls":
      side === "center" ? `${startPanelId} ${endPanelId}` : panelId,
    "data-state": isOpen ? "open" : "closed",
    className: classNames?.trigger,
    onClick: toggleOpen,
  } satisfies ExpandableToolbarTriggerProps;

  const trigger = (
    <motion.div
      ref={triggerWrapperRef}
      data-slot="expandable-toolbar-trigger-wrapper"
      data-state={isOpen ? "open" : "closed"}
      className={cn(
        "group/expandable-toolbar-trigger relative isolate flex size-8 shrink-0 items-center justify-center",
        classNames?.triggerWrapper,
      )}
    >
      {!renderTrigger ? (
        <motion.span
          aria-hidden="true"
          data-slot="expandable-toolbar-trigger-surface"
          initial={false}
          animate={{
            inset: isOpen ? 0 : -TOOLBAR_PADDING,
            borderRadius: triggerRadius,
          }}
          transition={triggerTransition}
          className={cn(
            "pointer-events-none absolute z-0 bg-muted opacity-0 transition-opacity",
            "group-hover/expandable-toolbar-trigger:opacity-100 group-data-[state=open]/expandable-toolbar-trigger:opacity-100",
            "dark:bg-muted/50",
            disabled && "hidden",
          )}
        />
      ) : null}
      {renderTrigger ? (
        renderTrigger({
          open: isOpen,
          disabled,
          label: currentLabel,
          controlsId: panelId,
          triggerProps,
        })
      ) : (
        <DefaultExpandableToolbarTrigger
          open={isOpen}
          expandIcon={expandIcon}
          collapseIcon={collapseIcon}
          triggerProps={triggerProps}
        />
      )}
    </motion.div>
  );

  const separator = (
    <span
      aria-hidden="true"
      data-slot="expandable-toolbar-trigger-separator"
      className={cn(
        "mx-1 h-5 w-px shrink-0 bg-border",
        classNames?.triggerSeparator,
      )}
    />
  );

  const renderPanel = (
    position: "start" | "end",
    id: string,
    content: ReactNode[],
    contentRef: Ref<HTMLDivElement>,
    contentWidth: number,
  ) => (
    <motion.div
      initial={false}
      id={id}
      aria-hidden={!isOpen}
      inert={!isOpen ? true : undefined}
      data-slot="expandable-toolbar-panel"
      data-state={isOpen ? "open" : "closed"}
      animate={{ width: isOpen ? contentWidth : 0, opacity: isOpen ? 1 : 0 }}
      transition={transition}
      className={cn(
        "flex min-w-0 overflow-hidden whitespace-nowrap",
        position === "start" ? "justify-end" : "justify-start",
        !isOpen && "pointer-events-none",
        classNames?.panel,
      )}
      style={{ maxWidth: contentMaxWidth }}
    >
      <div
        ref={contentRef}
        data-slot="expandable-toolbar-content"
        className={cn(
          "flex w-max shrink-0 flex-nowrap items-center gap-1",
          classNames?.content,
        )}
      >
        {position === "end" ? separator : null}
        {content}
        {position === "start" ? separator : null}
      </div>
    </motion.div>
  );

  const toolbar = (
    <div
      role={role ?? "toolbar"}
      aria-label={ariaLabel}
      data-slot="expandable-toolbar"
      data-state={isOpen ? "open" : "closed"}
      data-side={side}
      className={cn(
        "inline-flex max-w-full items-center overflow-hidden rounded-lg border bg-background text-foreground shadow-sm",
        className,
      )}
      onKeyDown={handleKeyDown}
      style={{ ...style, padding: TOOLBAR_PADDING }}
      {...props}
    >
      {startChildren.length > 0
        ? renderPanel(
            "start",
            startPanelId,
            startChildren,
            startContentRef,
            startContentWidth,
          )
        : null}
      {trigger}
      {endChildren.length > 0
        ? renderPanel(
            "end",
            endPanelId,
            endChildren,
            endContentRef,
            endContentWidth,
          )
        : null}
    </div>
  );

  if (anchor === "trigger") {
    return (
      <div
        data-slot="expandable-toolbar-anchor"
        data-state={isOpen ? "open" : "closed"}
        data-side={side}
        className="relative inline-flex size-8 shrink-0"
      >
        <motion.div
          className={cn(
            "absolute top-0",
            side === "start" && "right-0",
            side === "end" && "left-0",
          )}
          // For `center`, the box's left edge starts one border + padding to
          // the left of the anchor slot and shifts by the start panel's width
          // as it opens, so the trigger itself never moves — both panels
          // appear to grow out of it symmetrically.
          style={
            side === "center"
              ? { left: -(TOOLBAR_PADDING + TOOLBAR_BORDER_WIDTH) }
              : undefined
          }
          animate={
            side === "center" ? { x: -startPanelWidth } : undefined
          }
          transition={
            shouldReduceMotion ? { duration: 0 } : TOOLBAR_TRANSITION.width
          }
        >
          {toolbar}
        </motion.div>
      </div>
    );
  }

  return toolbar;
}

function DefaultExpandableToolbarTrigger({
  open,
  expandIcon,
  collapseIcon,
  triggerProps,
}: {
  open: boolean;
  expandIcon?: ReactNode;
  collapseIcon?: ReactNode;
  triggerProps: ExpandableToolbarTriggerProps;
}) {
  const shouldReduceMotion = useReducedMotion();
  const { className, ...buttonProps } = triggerProps;
  const icon = open ? (collapseIcon ?? expandIcon) : expandIcon;
  const swapsIcon = collapseIcon != null;
  const iconTransition = shouldReduceMotion
    ? { duration: 0 }
    : TRIGGER_ICON_TRANSITION;

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      className={cn(
        "relative z-10 size-full bg-transparent text-muted-foreground hover:bg-transparent hover:text-foreground aria-expanded:bg-transparent aria-expanded:text-foreground active:scale-100 active:translate-y-0 active:not-aria-[haspopup]:translate-y-0 dark:hover:bg-transparent",
        className,
      )}
      {...buttonProps}
    >
      {swapsIcon ? (
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={open ? "collapse" : "expand"}
            aria-hidden="true"
            variants={TRIGGER_ICON_VARIANTS}
            initial="hidden"
            animate="visible"
            exit="hidden"
            transition={iconTransition}
            className="flex items-center justify-center"
          >
            {icon}
          </motion.span>
        </AnimatePresence>
      ) : (
        <span aria-hidden="true" className="flex items-center justify-center">
          {icon}
        </span>
      )}
    </Button>
  );
}

const FOCUSABLE_SELECTOR =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function getFirstFocusableElement(element: HTMLElement | null) {
  return element?.querySelector<HTMLElement>(FOCUSABLE_SELECTOR) ?? null;
}

const TOOLBAR_NAV_KEYS = ["ArrowLeft", "ArrowRight", "Home", "End"];

/** Controls where the arrow keys belong to the caret, not to toolbar nav. */
function isTextEntry(element: HTMLElement) {
  return (
    element instanceof HTMLTextAreaElement ||
    element.isContentEditable ||
    (element instanceof HTMLInputElement &&
      !["button", "checkbox", "radio", "range", "submit", "reset"].includes(
        element.type,
      ))
  );
}

function useMeasuredWidth<T extends HTMLElement>() {
  const [width, setWidth] = useState(0);
  const observerRef = useRef<ResizeObserver | null>(null);

  // A callback ref (rather than a mount-only effect) so a panel that mounts
  // later — `side` flipping to "center", children growing past one — is still
  // measured and observed instead of animating open to width 0.
  const ref = useCallback((element: T | null) => {
    observerRef.current?.disconnect();
    observerRef.current = null;

    if (!element) return;

    const updateWidth = (nextWidth: number) => {
      setWidth((currentWidth) =>
        currentWidth === nextWidth ? currentWidth : nextWidth,
      );
    };

    updateWidth(readElementWidth(element));

    if (typeof ResizeObserver === "undefined") return;

    const resizeObserver = new ResizeObserver((entries) => {
      updateWidth(readElementWidth(element, entries[0]));
    });

    resizeObserver.observe(element);
    observerRef.current = resizeObserver;
  }, []);

  return [ref, width] as const;
}

function readElementWidth(
  element: HTMLElement,
  entry?: ResizeObserverEntry,
) {
  const borderBoxSize = Array.isArray(entry?.borderBoxSize)
    ? entry?.borderBoxSize[0]
    : entry?.borderBoxSize;

  if (borderBoxSize) {
    return Math.ceil(borderBoxSize.inlineSize);
  }

  return Math.ceil(element.getBoundingClientRect().width || element.scrollWidth);
}
