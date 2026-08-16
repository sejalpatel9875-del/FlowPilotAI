"use client";

import React, { useEffect, useRef } from "react";
import { useTheme } from "@/app/providers";
import { ACCENT_COLOR_MAP, AI_CORE_COLOR_MAP } from "@/utils/tokenGenerator";

export const AmbientCanvasBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const { themeConfig } = useTheme();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // 1. Accessibility / Motion Check
    if (
      themeConfig.motion === "off" ||
      themeConfig.backgroundEffect === "none" ||
      (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)
    ) {
      const ctx = canvas.getContext("2d");
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener("resize", handleResize);

    // Color Resolution from Theme
    const accentRgb = ACCENT_COLOR_MAP[themeConfig.primaryAccent]?.rgb || "46, 123, 255";
    const aiCoreRgb = AI_CORE_COLOR_MAP[themeConfig.aiCoreColor]?.rgb || "0, 229, 255";

    const isLightOrWarm = themeConfig.background === "light" || themeConfig.background === "warm";
    const baseAlpha = isLightOrWarm ? 0.20 : 0.40;

    // Node Count & Velocity based on Motion setting
    let nodeCount = Math.min(28, Math.floor(window.innerWidth / 50));
    let speedMult = 0.35;

    if (themeConfig.motion === "subtle") {
      nodeCount = Math.min(16, Math.floor(window.innerWidth / 70));
      speedMult = 0.15;
    } else if (themeConfig.motion === "immersive") {
      nodeCount = Math.min(44, Math.floor(window.innerWidth / 35));
      speedMult = 0.55;
    }

    const nodes: Array<{
      x: number;
      y: number;
      vx: number;
      vy: number;
      radius: number;
      rgb: string;
      alpha: number;
    }> = [];

    const colorPalette = [accentRgb, aiCoreRgb, "139, 92, 246"];

    for (let i = 0; i < nodeCount; i++) {
      nodes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * speedMult,
        vy: (Math.random() - 0.5) * speedMult,
        radius: Math.random() * 2 + 1,
        rgb: colorPalette[i % colorPalette.length],
        alpha: Math.random() * baseAlpha + 0.1,
      });
    }

    let time = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      time += 0.01;

      // 1. Grid Background Effect
      if (themeConfig.backgroundEffect === "grid") {
        ctx.strokeStyle = `rgba(${accentRgb}, ${isLightOrWarm ? 0.04 : 0.03})`;
        ctx.lineWidth = 1;
        const gridSize = 40;
        for (let x = 0; x < width; x += gridSize) {
          ctx.beginPath();
          ctx.moveTo(x, 0);
          ctx.lineTo(x, height);
          ctx.stroke();
        }
        for (let y = 0; y < height; y += gridSize) {
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(width, y);
          ctx.stroke();
        }
      }

      // 2. Aurora Wave Effect
      if (themeConfig.backgroundEffect === "aurora") {
        const grad1 = ctx.createRadialGradient(
          width * 0.3 + Math.sin(time) * 80,
          height * 0.2 + Math.cos(time * 0.8) * 50,
          20,
          width * 0.3,
          height * 0.2,
          400
        );
        grad1.addColorStop(0, `rgba(${aiCoreRgb}, ${isLightOrWarm ? 0.06 : 0.08})`);
        grad1.addColorStop(1, "transparent");
        ctx.fillStyle = grad1;
        ctx.fillRect(0, 0, width, height);

        const grad2 = ctx.createRadialGradient(
          width * 0.7 + Math.cos(time * 0.7) * 70,
          height * 0.8 + Math.sin(time) * 60,
          20,
          width * 0.7,
          height * 0.8,
          450
        );
        grad2.addColorStop(0, `rgba(${accentRgb}, ${isLightOrWarm ? 0.05 : 0.07})`);
        grad2.addColorStop(1, "transparent");
        ctx.fillStyle = grad2;
        ctx.fillRect(0, 0, width, height);
      }

      // 3. Particle Mesh Connections
      if (themeConfig.backgroundEffect === "particles" || themeConfig.backgroundEffect === "aurora") {
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const dx = nodes[i].x - nodes[j].x;
            const dy = nodes[i].y - nodes[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < 130) {
              const edgeAlpha = (1 - dist / 130) * (isLightOrWarm ? 0.08 : 0.12);
              ctx.beginPath();
              ctx.moveTo(nodes[i].x, nodes[i].y);
              ctx.lineTo(nodes[j].x, nodes[j].y);
              ctx.strokeStyle = `rgba(${nodes[i].rgb}, ${edgeAlpha})`;
              ctx.lineWidth = 0.75;
              ctx.stroke();
            }
          }
        }

        // Draw particle nodes
        for (const node of nodes) {
          node.x += node.vx;
          node.y += node.vy;

          if (node.x < 0) node.x = width;
          if (node.x > width) node.x = 0;
          if (node.y < 0) node.y = height;
          if (node.y > height) node.y = 0;

          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${node.rgb}, ${node.alpha})`;
          ctx.shadowColor = `rgba(${node.rgb}, 0.5)`;
          ctx.shadowBlur = themeConfig.motion === "immersive" ? 10 : 5;
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [themeConfig]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 h-full w-full opacity-90 transition-opacity duration-700"
    />
  );
};
