"use client";

import * as React from "react";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";

interface BrushCleaningProps extends React.SVGAttributes<SVGSVGElement> {
  size?: number;
  animateOnHover?: boolean;
}

/**
 * BrushCleaning — an animated brush icon.
 * Based on the animate-ui library's icon pattern. Uses motion/react to
 * animate a gentle sweep on hover when `animateOnHover` is true.
 */
export function BrushCleaning({
  size = 24,
  animateOnHover = false,
  className,
  ...props
}: BrushCleaningProps) {
  const [hovered, setHovered] = React.useState(false);

  return (
    <motion.svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("lucide lucide-brush-cleaning", className)}
      onMouseEnter={() => animateOnHover && setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      {...(props as React.ComponentProps<typeof motion.svg>)}
    >
      {/* Brush handle */}
      <motion.path
        d="m16 22-1-4"
        animate={hovered ? { rotate: [0, -6, 6, 0] } : { rotate: 0 }}
        transition={{ duration: 0.5, ease: "easeInOut" }}
        style={{ originX: "16px", originY: "22px" }}
      />
      {/* Brush head */}
      <motion.path
        d="M19 13.99a1 1 0 0 0 1-1V12a2 2 0 0 0-2-2h-3a1 1 0 0 1-1-1V4a2 2 0 0 0-4 0v5a1 1 0 0 1-1 1H6a2 2 0 0 0-2 2v.99a1 1 0 0 0 1 1"
        animate={hovered ? { y: [0, -1, 0] } : { y: 0 }}
        transition={{ duration: 0.4, ease: "easeInOut" }}
      />
      {/* Bristle lines */}
      <motion.path
        d="M5 14h14l1.973 6.767A1 1 0 0 1 20 22H4a1 1 0 0 1-.973-1.233z"
        animate={hovered ? { scale: [1, 1.02, 1] } : { scale: 1 }}
        transition={{ duration: 0.4, ease: "easeInOut" }}
        style={{ originX: "12px", originY: "18px" }}
      />
    </motion.svg>
  );
}
