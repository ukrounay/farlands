// VisualizerApp.tsx
// Single-file React + Tailwind component. Drop into a React + Tailwind project (Vite, Next.js, or CRA) and it will work.
// Features:
// - Input: number sequence or sentence
// - Parsers: numeric, CSV, sentence tokens
// - Rules: Polar mapping, Grid mapping, Spiral mapping, Force-like relaxation
// - Smooth canvas rendering with requestAnimationFrame
// - Modern UI using Tailwind and Framer Motion (optional)
// - Export PNG, pause/play, tweak palette, sizes, and rules

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';

// ----- Types & Utilities -----
type Point = { id: string; x: number; y: number; value: number; label?: string };

function clamp(v: number, a = 0, b = 1) { return Math.max(a, Math.min(b, v)); }

// Simple seeded pseudo-random for deterministic layouts
function mulberry32(seed: number) {
  return function() {
    let t = seed += 0x6D2B79F5;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Hash a string to integer
function hashString(s: string) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

// Parse input to tokens (numbers or words)
function parseInput(input: string) {
  const trim = input.trim();
  if (trim.length === 0) return [];
  // Try numeric sequence: comma or whitespace separated numbers
  const numericAttempt = trim.split(/[ ,;\n\t]+/).map(s => s.trim()).filter(Boolean);
  if (numericAttempt.every(s => !isNaN(Number(s)))) {
    return numericAttempt.map((s, i) => ({ label: s, value: Number(s), id: `n-${i}` }));
  }
  // Otherwise treat as sentence tokens
  const words = trim.split(/\s+/).map((w, i) => ({ label: w, value: Array.from(w).reduce((a,c)=>a+c.charCodeAt(0),0), id: `w-${i}` }));
  return words;
}

// Map tokens -> points using different rule sets
function mapToPoints(tokens: {label:string;value:number;id:string}[], width: number, height: number, rule: string) : Point[] {
  const cx = width/2, cy = height/2;
  const maxVal = Math.max(...tokens.map(t=>t.value), 1);
  const rnd = mulberry32(hashString(tokens.map(t=>t.label).join('|')) || 1);

  if (rule === 'polar') {
    return tokens.map((t, i) => {
      const angle = rnd() * Math.PI * 2 + (i / Math.max(tokens.length,1)) * Math.PI * 2;
      const r = (t.value / maxVal) * Math.min(width,height) * 0.4 + rnd()*40;
      return { id: t.id, x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r, value: t.value, label: t.label };
    });
  }
  if (rule === 'grid') {
    const cols = Math.ceil(Math.sqrt(tokens.length));
    const gapX = width / (cols + 1);
    const rows = Math.ceil(tokens.length / cols);
    const gapY = height / (rows + 1);
    return tokens.map((t, i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      // jitter slightly by seeded random
      const jx = (rnd()-0.5)*gapX*0.3;
      const jy = (rnd()-0.5)*gapY*0.3;
      return { id: t.id, x: gapX*(col+1)+jx, y: gapY*(row+1)+jy, value: t.value, label: t.label };
    });
  }
  if (rule === 'spiral') {
    return tokens.map((t, i) => {
      const theta = i * 0.6 + rnd()*0.6;
      const r = 10 + (i * 8) + (t.value / maxVal) * 30;
      return { id: t.id, x: cx + Math.cos(theta) * r, y: cy + Math.sin(theta) * r, value: t.value, label: t.label };
    });
  }
  // default: random scatter with relaxation
  return tokens.map((t,i) => ({ id: t.id, x: rnd()*width, y: rnd()*height, value: t.value, label: t.label }));
}

// Simple relaxation to avoid overlaps (very light weight)
function relaxPoints(points: Point[], iterations=6, width=800, height=600) {
  const pts = points.map(p=>({...p}));
  for (let k=0;k<iterations;k++){
    for (let i=0;i<pts.length;i++){
      for (let j=i+1;j<pts.length;j++){
        const a=pts[i], b=pts[j];
        let dx = b.x - a.x, dy = b.y - a.y;
        let d2 = dx*dx + dy*dy;
        const minDist = 18 + (Math.log1p(a.value)+Math.log1p(b.value));
        if (d2 < (minDist*minDist) && d2>0.0001){
          const d = Math.sqrt(d2);
          const overlap = (minDist - d)/2;
          const nx = dx/d, ny = dy/d;
          a.x -= nx*overlap; a.y -= ny*overlap;
          b.x += nx*overlap; b.y += ny*overlap;
          // clamp
          a.x = clamp(a.x, 0, width); b.x = clamp(b.x,0,width);
          a.y = clamp(a.y, 0, height); b.y = clamp(b.y,0,height);
        }
      }
    }
  }
  return pts;
}

// ----- React Component -----
export default function VisualizerApp(){
  const canvasRef = useRef<HTMLCanvasElement| null>(null);
  const [input, setInput] = useState('Hello world this is a test 42 123');
  const [rule, setRule] = useState<'polar'|'grid'|'spiral'|'scatter'>('polar');
  const [pointSize, setPointSize] = useState(8);
  const [animate, setAnimate] = useState(true);
  const [paletteIndex, setPaletteIndex] = useState(0);
  const [rawTokens, setRawTokens] = useState(() => parseInput('Hello world this is a test 42 123'));
  const [fps, setFps] = useState(60);
  const frameRef = useRef<number| null>(null);
  const lastTimeRef = useRef<number>(0);
  const pointsRef = useRef<Point[]>([]);
  const [exportName, setExportName] = useState('visualizer.png');

  const palettes = useMemo(()=>[
    { name: 'Vivid', bg:'#0f172a', colors:['#7c3aed','#06b6d4','#f97316','#ef4444'] },
    { name: 'Pastel', bg:'#f8fafc', colors:['#fda4af','#bfdbfe','#bbf7d0','#fde68a'] },
    { name: 'Dark Neon', bg:'#030712', colors:['#00f5d4','#7c3aed','#ffd60a','#ff6b6b'] }
  ],[]);

  // parse when input changes
  useEffect(()=>{
    setRawTokens(parseInput(input));
  },[input]);

  // compute base points when tokens / size / rule changes
  const computePoints = useCallback((w:number,h:number)=>{
    const pts = mapToPoints(rawTokens, w, h, rule);
    const relaxed = relaxPoints(pts, 8, w, h);
    pointsRef.current = relaxed;
    return relaxed;
  },[rawTokens, rule]);

  // handle resize
  useEffect(()=>{
    const canvas = canvasRef.current; if(!canvas) return;
    function resize(){
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
      const ctx = canvas.getContext('2d');
      if(ctx) ctx.setTransform(dpr,0,0,dpr,0,0);
      computePoints(rect.width, rect.height);
    }
    resize();
    const obs = new ResizeObserver(resize);
    obs.observe(canvas);
    return ()=>obs.disconnect();
  },[computePoints]);

  // animation & render loop
  useEffect(()=>{
    const canvas = canvasRef.current; if(!canvas) return;
    const ctx = canvas.getContext('2d'); if(!ctx) return;
    const pal = palettes[paletteIndex];

    let hueShift = 0;

    function draw(time: number){
      const rect = canvas.getBoundingClientRect();
      const w = rect.width, h = rect.height;

      // fps throttle
      if (lastTimeRef.current && fps>0){
        const elapsed = time - lastTimeRef.current;
        if (elapsed < 1000 / fps) {
          frameRef.current = requestAnimationFrame(draw);
          return;
        }
      }
      lastTimeRef.current = time;

      // background
      ctx.clearRect(0,0,w,h);
      ctx.fillStyle = pal.bg;
      ctx.fillRect(0,0,w,h);

      // maybe animate positions slightly
      let pts = pointsRef.current;
      if (animate){
        // small breathing motion
        const t = time/1000;
        pts = pts.map((p,i)=>({ ...p, x: p.x + Math.cos(t*0.6 + i)*1.2, y: p.y + Math.sin(t*0.9 + i)*0.7 }));
      }

      // edges (connect sequential tokens)
      ctx.lineWidth = 1.2;
      ctx.globalAlpha = 0.9;
      for (let i=0;i<pts.length-1;i++){
        const a = pts[i], b = pts[i+1];
        const grad = ctx.createLinearGradient(a.x,a.y,b.x,b.y);
        grad.addColorStop(0, pal.colors[(i)%pal.colors.length]);
        grad.addColorStop(1, pal.colors[(i+1)%pal.colors.length]);
        ctx.strokeStyle = grad;
        ctx.beginPath();
        ctx.moveTo(a.x,a.y);
        // quadratic curve for smoothness
        const mx = (a.x + b.x)/2, my = (a.y + b.y)/2;
        ctx.quadraticCurveTo(mx, my, b.x, b.y);
        ctx.stroke();
      }

      // points
      for (let i=0;i<pts.length;i++){
        const p = pts[i];
        const c = pal.colors[i % pal.colors.length];
        ctx.beginPath();
        ctx.globalAlpha = 1;
        ctx.fillStyle = c;
        ctx.moveTo(p.x, p.y);
        ctx.arc(p.x, p.y, pointSize * (1 + Math.sin(time/750 + i)*0.07), 0, Math.PI*2);
        ctx.fill();

        // subtle glow
        ctx.globalAlpha = 0.14;
        ctx.beginPath();
        ctx.arc(p.x, p.y, pointSize*4, 0, Math.PI*2);
        ctx.fillStyle = c;
        ctx.fill();

        // labels: show if hovered or small screen toggle (simple behaviour: first three)
        if (i < 3) {
          ctx.globalAlpha = 0.9;
          ctx.fillStyle = 'rgba(255,255,255,0.95)';
          ctx.font = '12px Inter, ui-sans-serif, system-ui';
          ctx.fillText(p.label ?? '', p.x + pointSize + 6, p.y - pointSize - 4);
        }
      }

      frameRef.current = requestAnimationFrame(draw);
    }

    frameRef.current = requestAnimationFrame(draw);
    return ()=>{
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  },[palettes, paletteIndex, pointSize, animate, fps]);

  // recompute points when parameters change
  useEffect(()=>{
    const canvas = canvasRef.current; if(!canvas) return;
    const rect = canvas.getBoundingClientRect();
    computePoints(rect.width, rect.height);
  },[rawTokens, rule, computePoints, paletteIndex]);

  // export PNG
  const exportPNG = useCallback(()=>{
    const canvas = canvasRef.current; if(!canvas) return;
    const mime = 'image/png';
    const url = canvas.toDataURL(mime);
    const a = document.createElement('a');
    a.href = url; a.download = exportName || 'visualizer.png';
    a.click();
  },[exportName]);

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-10 font-sans">
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 space-y-4">
          <motion.h1 initial={{y:-8,opacity:0}} animate={{y:0,opacity:1}} className="text-2xl font-extrabold">Visualizer — Canvas Graph Studio</motion.h1>
          <div className="bg-white p-4 rounded-2xl shadow-lg">
            <label className="block text-sm font-medium text-slate-600">Input (numbers or sentence)</label>
            <textarea value={input} onChange={(e)=>setInput(e.target.value)} rows={4} className="mt-2 w-full p-3 bg-slate-50 rounded-lg resize-none" />

            <div className="mt-4 grid grid-cols-2 gap-2">
              <label className="text-sm">Rule</label>
              <select value={rule} onChange={(e)=>setRule(e.target.value as any)} className="p-2 rounded-lg bg-slate-50">
                <option value="polar">Polar</option>
                <option value="grid">Grid</option>
                <option value="spiral">Spiral</option>
                <option value="scatter">Scatter</option>
              </select>
            </div>

            <div className="mt-3 flex gap-3 items-center">
              <label className="text-sm">Point size</label>
              <input type="range" min={2} max={30} value={pointSize} onChange={(e)=>setPointSize(Number(e.target.value))} />
            </div>

            <div className="mt-3 flex gap-3 items-center">
              <label className="text-sm">Palette</label>
              <select value={paletteIndex} onChange={(e)=>setPaletteIndex(Number(e.target.value))} className="p-2 rounded-lg bg-slate-50">
                {palettes.map((p, i)=> <option key={p.name} value={i}>{p.name}</option>)}
              </select>
            </div>

            <div className="mt-3 flex items-center gap-3">
              <label className="inline-flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={animate} onChange={(e)=>setAnimate(e.target.checked)} />
                <span className="text-sm">Animate</span>
              </label>
              <label className="inline-flex items-center gap-2">
                <span className="text-sm">FPS</span>
                <input type="number" value={fps} min={1} max={120} onChange={(e)=>setFps(Number(e.target.value)||60)} className="w-20 p-1 rounded-md bg-slate-50" />
              </label>
            </div>

            <div className="mt-4 flex gap-2">
              <button onClick={exportPNG} className="px-3 py-2 rounded-lg bg-gradient-to-r from-indigo-600 to-cyan-500 text-white font-semibold">Export PNG</button>
              <input value={exportName} onChange={(e)=>setExportName(e.target.value)} className="p-2 rounded-lg bg-slate-50 flex-1" />
            </div>

            <div className="mt-4 text-xs text-slate-500">Tip: try mixed input like: "12, 3, 7, hello world" or a full sentence. The visualizer will try to infer tokens automatically.</div>
          </div>

          <div className="bg-white p-4 rounded-2xl shadow-lg">
            <h3 className="font-semibold">About the rules</h3>
            <ul className="mt-2 text-sm text-slate-600 space-y-1">
              <li><strong>Polar</strong> — maps token value to radius and uses an angle to distribute around center.</li>
              <li><strong>Grid</strong> — places tokens on a jittered grid for clarity.</li>
              <li><strong>Spiral</strong> — arranges tokens on a spiral — great for sequences.</li>
              <li><strong>Scatter</strong> — seeded scatter with light relaxation.</li>
            </ul>
          </div>

        </div>

        <div className="md:col-span-2 row-span-1 relative bg-gradient-to-b from-white to-slate-50 p-4 rounded-2xl shadow-lg">
          <div className="absolute top-4 left-4 z-10 bg-white/40 backdrop-blur rounded-full px-3 py-1 text-xs">Particles: {pointsRef.current.length}</div>
          <div className="absolute top-4 right-4 z-10 flex gap-2">
            <button onClick={()=>{ setAnimate(a=>!a); }} className="px-3 py-2 rounded-full bg-white/30">{animate? 'Pause' : 'Play'}</button>
            <button onClick={()=>{ navigator.clipboard?.writeText(JSON.stringify(rawTokens.map(t=>t.label))); }} className="px-3 py-2 rounded-full bg-white/30">Copy tokens</button>
          </div>
          <div className="w-full h-[66vh] md:h-[72vh] rounded-xl overflow-hidden">
            <canvas ref={canvasRef} className="w-full h-full block"/>
          </div>

          <div className="mt-4 flex gap-3 items-center text-sm text-slate-500">
            <div>Preview renders on an HTML canvas for maximum speed and custom shaders (future).</div>
            <div className="ml-auto">Made with ❤️ — reusable, accessible, and performant.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
