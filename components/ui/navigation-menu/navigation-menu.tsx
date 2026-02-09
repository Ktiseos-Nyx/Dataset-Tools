"use client";
import { NavigationMenu } from "@base-ui/react/navigation-menu";
import { cn } from "@/lib/utils";
import styles from "./navigation-menu.module.css";

function NavigationMenuRoot({ className, ...props }: NavigationMenu.Root.Props) {
  return <NavigationMenu.Root className={cn(styles.root, className)} data-slot="navigationmenu-root" {...props} />;
}

function NavigationMenuList({ className, ...props }: NavigationMenu.List.Props) {
  return <NavigationMenu.List className={cn(styles.list, className)} data-slot="navigationmenu-list" {...props} />;
}

function NavigationMenuItem({ className, ...props }: NavigationMenu.Item.Props) {
  return <NavigationMenu.Item className={cn(className)} {...props} />;
}

function NavigationMenuTrigger({ className, ...props }: NavigationMenu.Trigger.Props) {
  return (
    <NavigationMenu.Trigger className={cn(styles.trigger, className)} data-slot="navigationmenu-trigger" {...props} />
  );
}

function NavigationMenuContent({ className, ...props }: NavigationMenu.Content.Props) {
  return (
    <NavigationMenu.Content className={cn(styles.content, className)} data-slot="navigationmenu-content" {...props} />
  );
}

function NavigationMenuIcon({ className, ...props }: NavigationMenu.Icon.Props) {
  return <NavigationMenu.Icon className={cn(styles.chevron, className)} data-slot="navigationmenu-icon" {...props} />;
}

function NavigationMenuLink({ className, ...props }: NavigationMenu.Link.Props) {
  return <NavigationMenu.Link className={className || styles.link} data-slot="navigationmenu-link" {...props} />;
}

function NavigationMenuPortal({ children, ...props }: NavigationMenu.Portal.Props) {
  return <NavigationMenu.Portal {...props}>{children}</NavigationMenu.Portal>;
}

function NavigationMenuBackdrop({ className, ...props }: NavigationMenu.Backdrop.Props) {
  return (
    <NavigationMenu.Backdrop
      className={cn(styles.backdrop, className)}
      data-slot="navigationmenu-backdrop"
      {...props}
    />
  );
}

function NavigationMenuPositioner({ className, children, ...props }: NavigationMenu.Positioner.Props) {
  return (
    <NavigationMenu.Positioner
      className={cn(styles.positioner, className)}
      data-slot="navigationmenu-positioner"
      {...props}
    >
      {children}
    </NavigationMenu.Positioner>
  );
}

function NavigationMenuPopup({ className, children, ...props }: NavigationMenu.Popup.Props) {
  return (
    <NavigationMenu.Popup className={cn(styles.popup, className)} {...props}>
      {children}
    </NavigationMenu.Popup>
  );
}

function NavigationMenuArrow({ className, ...props }: NavigationMenu.Arrow.Props) {
  return (
    <NavigationMenu.Arrow className={cn(styles.arrow, className)} {...props}>
      <svg aria-hidden="true" fill="none" height="8" viewBox="0 0 16 8" width="16">
        <path className={styles.arrowFill} d="M8 0L16 8H0L8 0Z" />
        <path className={styles.arrowOuterStroke} d="M8 0L0 8" fill="none" stroke="currentColor" strokeWidth="1" />
        <path className={styles.arrowOuterStroke} d="M8 0L16 8" fill="none" stroke="currentColor" strokeWidth="1" />
      </svg>
    </NavigationMenu.Arrow>
  );
}

function NavigationMenuViewport({ className, ...props }: NavigationMenu.Viewport.Props) {
  return (
    <NavigationMenu.Viewport
      className={cn(styles.viewport, className)}
      data-slot="navigationmenu-viewport"
      {...props}
    />
  );
}

const navigationMenuTriggerStyle = () => styles.trigger;

export {
  NavigationMenuRoot as NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuTrigger,
  NavigationMenuIcon,
  NavigationMenuContent,
  NavigationMenuLink,
  NavigationMenuPortal,
  NavigationMenuBackdrop,
  NavigationMenuPositioner,
  NavigationMenuPopup,
  NavigationMenuArrow,
  NavigationMenuViewport,
  navigationMenuTriggerStyle,
};
