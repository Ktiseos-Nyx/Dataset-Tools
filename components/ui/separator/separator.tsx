"use client";

import { Separator } from "@base-ui/react/separator";
import { cn } from "@/lib/utils";
import styles from "./separator.module.css";

function SeparatorRoot({ className, ...props }: Separator.Props) {
  return <Separator className={cn(styles.root, className)} data-slot="separator" {...props} />;
}

export { SeparatorRoot as Separator };
