
import { useRef, useEffect } from "react";

/**
 * DigitalTwin — self-contained compliance topology canvas.
 *
 * Drop-in: does not depend on any other file, theme, or global.
 * Renders an ivory card with an animated node graph (hover to highlight,
 * pulses travel along edges). Matches the chic light palette.
 *
 * Optional props:
 *   - title, subtitle : header text
 *   - height          : canvas height in px (default 560)
 *   - nodes, edges    : override the demo topology with your own scan data
 *
 * Node shape: { id, label, score, x, y, r, hub?, col }
 *   x / y are 0..1 fractions of the canvas. col is a hex string.
 * Edge shape: [fromId, toId]
 */

const PAL = {
  ivory: "#FAF7F2",
  cream: "#EDE7DA",
  ink: "#16120E",
  ink3: "#5C5248",
  ink4: "#8C8278",
  border: "rgba(22,18,14,0.10)",
  sage: "#5A7A6A",
  sage2: "#3D5C4E",
  slate: "#4A6080",
  amber: "#C87840",
  amber2: "#A85A28",
  rust: "#B85C38",
  gold: "#B8923A",
};

const DEFAULT_NODES = [];

const DEFAULT_EDGES = [];

function hexA(hex, alpha) {
  const a = Math.round(Math.max(0, Math.min(1, alpha)) * 255).toString(16).padStart(2, "0");
  return hex + a;
}

export default function DigitalTwin({
  title = "Compliance Digital Twin",
  subtitle = "Live organizational compliance topology · real-time health",
  height = 560,
  nodes = [],
  edges = [],
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let W = 0, H = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
    let _pendingResize = null;
    const applyResize = (w, h, newDpr) => {
      W = w; H = h; dpr = newDpr;
      canvas.width = Math.max(1, Math.floor(W * dpr));
      canvas.height = Math.max(1, Math.floor(H * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const resize = () => {
      const newW = canvas.clientWidth;
      const newH = canvas.clientHeight;
      const newDpr = Math.min(window.devicePixelRatio || 1, 2);
      // debounce and only apply when values change meaningfully
      if (_pendingResize) clearTimeout(_pendingResize);
      _pendingResize = setTimeout(() => {
        if (Math.abs(newDpr - dpr) > 0.01 || newW !== W || newH !== H) {
          applyResize(newW, newH, newDpr);
        }
        _pendingResize = null;
      }, 80);
    };
    // initial apply
    applyResize(canvas.clientWidth, canvas.clientHeight, dpr);
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const N = nodes.map((n, i) => ({ ...n, phase: i * 0.65, speed: 0.35 + (i % 5) * 0.06 }));
    const byId = (id) => N.find((n) => n.id === id);
    const E = edges.map(([a, b]) => ({ a, b, _px: null, _py: null }));
    const particles = [];

    let hovered = null;
    const onMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left, my = e.clientY - rect.top;
      hovered = null;
      for (const n of N) {
        const nx = n.x * W, ny = n.y * H;
        if (Math.hypot(mx - nx, my - ny) < n.r + 12) hovered = n.id;
      }
    };
    const onLeave = () => { hovered = null; };
    canvas.addEventListener("mousemove", onMove);
    canvas.addEventListener("mouseleave", onLeave);
    const onClick = (e) => {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left, my = e.clientY - rect.top;
      for (const n of N) {
        const nx = n.x * W;
        const ny = n._displayY != null ? n._displayY : n.y * H + floatY(n, (performance.now() - start) / 1000);
        if (Math.hypot(mx - nx, my - ny) < n.r + 6) {
          handleNodeClick(n);
          break;
        }
      }
    };
    canvas.addEventListener("click", onClick);

    const spawnParticles = (src, target, now) => {
      const count = 4;
      const dx = target.x - src.x;
      const dy = target.y - src.y;
      const dist = Math.max(1, Math.hypot(dx, dy));
      const ux = dx / dist;
      const uy = dy / dist;
      const px = -uy;
      const py = ux;
      const startRadius = Math.max(10, src.r * 0.6);
      const endOffset = Math.max(10, target.r * 0.4);
      for (let i = 0; i < count; i++) {
        const offset = (i - (count - 1) / 2) * 8;
        const sx = src.x + ux * startRadius + px * offset;
        const sy = src.y + uy * startRadius + py * offset;
        const tx = target.x - ux * endOffset;
        const ty = target.y - uy * endOffset;
        const duration = 700 + i * 90;
        const delay = i * 64;
        particles.push({ sx, sy, tx, ty, birth: now + delay, duration, r: 2 + (count - i) * 0.2, col: src.col, alpha: 1 });
      }
    };

    const handleNodeClick = (node) => {
      if (!node.hub) return;
      const now = performance.now();
      const t = (now - start) / 1000;
      const target = {
        x: node.x * W,
        y: node._displayY != null ? node._displayY : node.y * H + floatY(node, t)
      };
      for (const edge of E) {
        let srcId = null;
        if (edge.a === node.id) srcId = edge.b;
        else if (edge.b === node.id) srcId = edge.a;
        if (!srcId) continue;
        const src = byId(srcId);
        if (!src) continue;
        const source = {
          x: src.x * W,
          y: src._displayY != null ? src._displayY : src.y * H + floatY(src, t),
          r: src.r,
          col: src.col
        };
        spawnParticles(source, target, now);
      }
    };

    let start = performance.now(), raf;
    const floatY = (n, t) => (reduce ? 0 : Math.sin(t * n.speed + n.phase) * 2.4);

    const drawNode = (n, t) => {
      const nx = n.x * W;
      const targetY = n.y * H + floatY(n, t);
      if (n._displayY == null) n._displayY = targetY;
      const ny = n._displayY;
      const isH = hovered === n.id;
      const r = isH ? n.r * 1.1 : n.r;

      const bloom = ctx.createRadialGradient(nx, ny, r * 0.2, nx, ny, r * 2.8);
      bloom.addColorStop(0, hexA(n.col, isH ? 0.28 : 0.12));
      bloom.addColorStop(1, hexA(n.col, 0));
      ctx.beginPath(); ctx.arc(nx, ny, r * 2.8, 0, Math.PI * 2);
      ctx.fillStyle = bloom; ctx.fill();

      ctx.beginPath(); ctx.arc(nx, ny, r, 0, Math.PI * 2);
      const fill = ctx.createRadialGradient(nx - r * 0.25, ny - r * 0.25, 0, nx, ny, r);
      fill.addColorStop(0, "rgba(250,247,242,0.96)");
      fill.addColorStop(1, "rgba(237,231,218,0.86)");
      ctx.fillStyle = fill; ctx.fill();
      ctx.strokeStyle = hexA(n.col, isH ? 1 : 0.8);
      ctx.lineWidth = isH ? 2.5 : 1.8; ctx.stroke();

      ctx.beginPath(); ctx.arc(nx, ny, r * 0.74, 0, Math.PI * 2);
      ctx.strokeStyle = hexA(n.col, 0.16); ctx.lineWidth = 1; ctx.stroke();

      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillStyle = n.col;
      ctx.font = `700 ${n.hub ? 22 : 15}px Inter, system-ui, sans-serif`;
      ctx.fillText(n.score + "%", nx, ny);

      const lines = String(n.label).split("\n");
      ctx.fillStyle = "rgba(22,18,14,0.55)";
      ctx.font = `500 ${n.hub ? 11 : 10}px Inter, system-ui, sans-serif`;
      lines.forEach((l, i) => ctx.fillText(l, nx, ny + r + 11 + i * 12));
    };

    let last = performance.now();
    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      const now = performance.now();
      const t = (now - start) / 1000; // seconds elapsed
      let dt = (now - last) / 1000;
      if (!isFinite(dt) || dt <= 0) dt = 0.016;
      dt = Math.min(0.06, dt); // clamp large jumps
      last = now;

      // update smooth display positions for nodes
      const motionScale = particles.length > 0 ? 0.22 : 1;
      for (const n of N) {
        const targetY = n.y * H + floatY(n, t) * motionScale;
        if (n._displayY == null) n._displayY = targetY;
        const alpha = 1 - Math.exp(-dt * (particles.length > 0 ? 18 : 12));
        n._displayY += (targetY - n._displayY) * alpha;
      }
      const bg = ctx.createRadialGradient(W * 0.5, H * 0.5, 0, W * 0.5, H * 0.5, W * 0.6);
      bg.addColorStop(0, "rgba(201,169,110,0.03)");
      bg.addColorStop(1, "transparent");
      ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);

      for (const edge of E) {
        const na = byId(edge.a), nb = byId(edge.b);
        if (!na || !nb) continue;
        const ax = na.x * W, ay = na._displayY;
        const bx = nb.x * W, by = nb._displayY;
        const hi = hovered === edge.a || hovered === edge.b;
        const eg = ctx.createLinearGradient(ax, ay, bx, by);
        eg.addColorStop(0, hexA(na.col, hi ? 0.6 : 0.27));
        eg.addColorStop(1, hexA(nb.col, hi ? 0.6 : 0.27));
        ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by);
        ctx.strokeStyle = eg; ctx.lineWidth = hi ? 1.5 : 0.8; ctx.stroke();

        if (particles.length === 0) {
          // smooth pulse animation only when no interaction particles are active
          const tp = (Math.sin(t * 1.1 + (ax + ay) * 0.001) + 1) / 2;
          const targetPx = ax + (bx - ax) * tp, targetPy = ay + (by - ay) * tp;
          if (edge._px == null) { edge._px = targetPx; edge._py = targetPy; }
          const edgeAlpha = 1 - Math.exp(-dt * 30);
          edge._px += (targetPx - edge._px) * edgeAlpha;
          edge._py += (targetPy - edge._py) * edgeAlpha;
          ctx.beginPath(); ctx.arc(edge._px, edge._py, hi ? 3 : 1.8, 0, Math.PI * 2);
          ctx.fillStyle = hexA(na.col, hi ? 0.8 : 0.47); ctx.fill();
        }
      }

      // particles spawned by interactions (smooth, time-based motion)
      const particleNow = performance.now();
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        if (particleNow < p.birth) continue;
        const elapsed = particleNow - p.birth;
        const prog = Math.min(1.2, elapsed / p.duration);
        const eprog = prog < 1 ? 1 - Math.pow(1 - prog, 3) : 1;
        const x = p.sx + (p.tx - p.sx) * eprog;
        const y = p.sy + (p.ty - p.sy) * eprog;
        const fade = prog < 1 ? 1 : Math.max(0, 1 - (prog - 1) / 0.3);
        const alpha = p.alpha * fade;
        ctx.beginPath(); ctx.arc(x, y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = hexA(p.col, Math.max(0, Math.min(alpha, 1)));
        ctx.fill();
        if (prog >= 1.2) particles.splice(i, 1);
      }

      N.forEach((n) => drawNode(n, t));
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      canvas.removeEventListener("mousemove", onMove);
      canvas.removeEventListener("mouseleave", onLeave);
      canvas.removeEventListener("click", onClick);
      if (_pendingResize) { clearTimeout(_pendingResize); _pendingResize = null; }
    };
  }, [nodes, edges]);

  const legend = [
    [PAL.sage, "Excellent (90–100%)"],
    [PAL.slate, "Good (80–89%)"],
    [PAL.amber, "At risk (70–79%)"],
    [PAL.rust, "Critical (<70%)"],
  ];

  return (
    <div style={{
      position: "relative", background: PAL.ivory,
      border: `1px solid ${PAL.border}`, borderRadius: 18, overflow: "hidden",
      boxShadow: "0 1px 3px rgba(22,18,14,0.04)",
    }}>
      <div style={{ padding: "24px 28px 4px" }}>
        <div style={{ fontFamily: "'Instrument Serif', Georgia, serif", fontStyle: "italic", fontSize: 26, color: PAL.ink, lineHeight: 1.1 }}>
          {title}
        </div>
        <div style={{ fontSize: 12.5, color: PAL.ink4, marginTop: 4 }}>{subtitle}</div>
      </div>

      <div style={{ position: "relative", height }}>
        <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />
        <div style={{
          position: "absolute", bottom: 18, left: 24, display: "flex", flexDirection: "column", gap: 7,
          background: "rgba(245,240,232,0.85)", backdropFilter: "blur(12px)",
          padding: "12px 16px", borderRadius: 12, border: `1px solid ${PAL.border}`,
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: PAL.ink4, marginBottom: 2 }}>
            Health Index
          </div>
          {legend.map(([c, label]) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: PAL.ink3, fontWeight: 500 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: c, flexShrink: 0 }} />
              {label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
