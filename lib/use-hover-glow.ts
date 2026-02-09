import { type MotionProps, type Easing } from "motion/react";

export interface UseHoverGlowOptions {
  glowColor?: string;

  glowBlur?: number;

  glowSpread?: number;

  duration?: number;

  ease?: Easing | Easing[];

  scale?: number;

  innerGlow?: boolean;
}

export function useHoverGlow(options: UseHoverGlowOptions = {}): MotionProps {
  const {
    glowColor = "rgba(59, 130, 246, 0.5)",
    glowBlur = 20,
    glowSpread = 5,
    duration = 0.3,
    ease = "easeOut",
    scale = 1.02,
    innerGlow = false,
  } = options;

  const baseShadow = "0 2px 8px rgba(0, 0, 0, 0.1)";
  const glowShadow = `0 0 ${glowBlur}px ${glowSpread}px ${glowColor}`;
  const innerGlowShadow = innerGlow
    ? `inset 0 0 ${glowBlur / 2}px ${glowColor}`
    : "";

  const hoverShadow = innerGlow
    ? `${baseShadow}, ${glowShadow}, ${innerGlowShadow}`
    : `${baseShadow}, ${glowShadow}`;

  return {
    initial: {
      scale: 1,
      boxShadow: baseShadow,
    },
    whileHover: {
      scale,
      boxShadow: hoverShadow,
    },
    transition: {
      duration,
      ease,
    },
  };
}
