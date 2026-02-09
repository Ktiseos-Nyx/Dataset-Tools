"use client";

import { Select } from "@base-ui/react/select";
import { Check, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import styles from "./select.module.css";

function SelectRoot<Value, Multiple extends boolean | undefined = undefined>(
  props: React.ComponentProps<typeof Select.Root<Value, Multiple>>
) {
  return <Select.Root<Value, Multiple> {...props} />;
}

function SelectTrigger({ className, children, render, ...props }: React.ComponentProps<typeof Select.Trigger>) {
  return (
    <Select.Trigger
      className={cn(!render && styles.trigger, className)}
      data-slot="select-trigger"
      nativeButton
      render={render}
      {...props}
    >
      {children}
    </Select.Trigger>
  );
}

function SelectValue({ className, children, ...props }: React.ComponentProps<typeof Select.Value>) {
  return (
    <Select.Value className={cn(styles.value, className)} data-slot="select-value" {...props}>
      {children}
    </Select.Value>
  );
}

function SelectIcon({ className, children, ...props }: React.ComponentProps<typeof Select.Icon>) {
  return (
    <Select.Icon className={cn(styles.icon, className)} {...props}>
      {children || <ChevronDown size={16} />}
    </Select.Icon>
  );
}

function SelectPortal({ ...props }: React.ComponentProps<typeof Select.Portal>) {
  return <Select.Portal {...props} />;
}

function SelectOverlay({ className, ...props }: React.ComponentProps<typeof Select.Backdrop>) {
  return <Select.Backdrop className={cn(styles.backdrop, className)} data-slot="select-backdrop" {...props} />;
}

function SelectPositioner({ className, ...props }: React.ComponentProps<typeof Select.Positioner>) {
  return <Select.Positioner className={cn(styles.positioner, className)} data-slot="select-positioner" {...props} />;
}

function SelectScrollUpArrow({ className, children, ...props }: React.ComponentProps<typeof Select.ScrollUpArrow>) {
  return (
    <Select.ScrollUpArrow className={cn(styles.scrollArrow, className)} data-slot="select-scrolluparrow" {...props}>
      {children || <ChevronDown size={16} style={{ transform: "rotate(180deg)" }} />}
    </Select.ScrollUpArrow>
  );
}

function SelectPopup({ className, ...props }: React.ComponentProps<typeof Select.Popup>) {
  return <Select.Popup className={cn(styles.popup, className)} {...props} />;
}

function SelectArrow({ className, ...props }: React.ComponentProps<typeof Select.Arrow>) {
  return <Select.Arrow className={cn(styles.arrow, className)} {...props} />;
}

function SelectScrollDownArrow({ className, children, ...props }: React.ComponentProps<typeof Select.ScrollDownArrow>) {
  return (
    <Select.ScrollDownArrow className={cn(styles.scrollArrow, className)} data-slot="select-scrolldownarrow" {...props}>
      {children || <ChevronDown size={16} />}
    </Select.ScrollDownArrow>
  );
}

function SelectList({ className, ...props }: React.ComponentProps<typeof Select.List>) {
  return <Select.List className={cn(styles.list, className)} {...props} />;
}

function SelectItem({ className, ...props }: React.ComponentProps<typeof Select.Item>) {
  return <Select.Item className={cn(styles.item, className)} {...props} />;
}

function SelectItemText({ className, ...props }: React.ComponentProps<typeof Select.ItemText>) {
  return <Select.ItemText className={cn(styles.itemText, className)} data-slot="select-itemtext" {...props} />;
}

function SelectGroup({ className, ...props }: React.ComponentProps<typeof Select.Group>) {
  return <Select.Group className={cn(styles.selectGroup, className)} data-slot="select-group" {...props} />;
}

function SelectGroupLabel({ className, ...props }: React.ComponentProps<typeof Select.GroupLabel>) {
  return <Select.GroupLabel className={cn(styles.groupLabel, className)} data-slot="select-grouplabel" {...props} />;
}

function SelectSeparator({ className, ...props }: React.ComponentProps<typeof Select.Separator>) {
  return <Select.Separator className={cn(styles.separator, className)} data-slot="select-separator" {...props} />;
}

function SelectItemIndicator({ className, children, ...props }: React.ComponentProps<typeof Select.ItemIndicator>) {
  return (
    <Select.ItemIndicator className={cn(styles.indicator, className)} data-slot="select-itemindicator" {...props}>
      {children || <Check size={16} />}
    </Select.ItemIndicator>
  );
}

function SelectSpacer() {
  return <div style={{ height: "4px", width: "100%" }} />;
}

export {
  SelectRoot as Select,
  SelectArrow,
  SelectGroup,
  SelectGroupLabel,
  SelectIcon,
  SelectItem,
  SelectItemIndicator,
  SelectItemText,
  SelectList,
  SelectOverlay,
  SelectPopup,
  SelectPortal,
  SelectPositioner,
  SelectRoot,
  SelectScrollDownArrow,
  SelectScrollUpArrow,
  SelectSeparator,
  SelectSpacer,
  SelectTrigger,
  SelectValue,
};
