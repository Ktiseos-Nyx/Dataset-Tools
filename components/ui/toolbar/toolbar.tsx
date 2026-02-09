"use client";

import { Toolbar } from "@base-ui/react/toolbar";
import { cn } from "@/lib/utils";
import styles from "./toolbar.module.css";

function ToolbarRoot({ className, orientation = "horizontal", ...props }: Toolbar.Root.Props) {
  return (
    <Toolbar.Root
      className={cn(styles.root, className)}
      data-orientation={orientation}
      data-slot="toolbar-root"
      orientation={orientation}
      {...props}
    />
  );
}

function ToolbarButton({ className, ...props }: Toolbar.Button.Props) {
  return <Toolbar.Button className={cn(styles.button, className)} {...props} />;
}

function ToolbarLink({ className, ...props }: Toolbar.Link.Props) {
  return <Toolbar.Link className={cn(styles.link, className)} {...props} />;
}

function ToolbarInput({ className, ...props }: Toolbar.Input.Props) {
  return <Toolbar.Input className={cn(styles.input, className)} {...props} />;
}

function ToolbarGroup({ className, ...props }: Toolbar.Group.Props) {
  return <Toolbar.Group className={cn(styles.group, className)} {...props} />;
}

function ToolbarSeparator({ className, ...props }: Toolbar.Separator.Props) {
  return <Toolbar.Separator className={cn(styles.separator, className)} data-slot="toolbar-separator" {...props} />;
}

export { ToolbarRoot as Toolbar, ToolbarButton, ToolbarGroup, ToolbarInput, ToolbarLink, ToolbarSeparator };
