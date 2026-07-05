import { useEffect } from "react";
import confetti from "canvas-confetti";

interface ConfettiBurstProps {
  burst: number;
  origin: { x: number; y: number };
}

export function ConfettiBurst({ burst, origin }: ConfettiBurstProps) {
  useEffect(() => {
    if (burst === 0) return;
    confetti({
      particleCount: 52,
      spread: 68,
      startVelocity: 24,
      gravity: 0.9,
      scalar: 0.75,
      origin,
      colors: ["#21d4fd", "#c026d3", "#f59e0b", "#f8fafc"],
      disableForReducedMotion: true,
      zIndex: 100,
    });
  }, [burst, origin]);

  return null;
}
