/* Thin frontend only. Program logic lives in blocks.py on the backend.
   This file: tap blocks, call /api/expand, animate the returned steps. */

let program = [];
let blockDefs = {};
let sayText = "Hi, we're Utopia!";
let running = false;
let stopRequested = false;

const canvas = document.getElementById('stage');
const ctx = canvas.getContext('2d');
let catX = 80, catY = 0, catAngle = 0, bubble = '';

function drawCat() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#e8f7e8';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#333';
  ctx.fillRect(0, 480, canvas.width, 4); // ground
  ctx.save();
  ctx.translate(catX, 400 + catY);
  ctx.rotate(catAngle);
  ctx.font = '110px serif';
  ctx.textAlign = 'center';
  ctx.fillText('🐱', 0, 0);
  ctx.restore();
  if (bubble) {
    ctx.font = '28px sans-serif';
    const w = ctx.measureText(bubble).width + 40;
    ctx.fillStyle = 'white';
    ctx.strokeStyle = '#333';
    ctx.beginPath();
    ctx.roundRect(Math.min(catX + 60, canvas.width - w - 10), 240, w, 60, 16);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#111';
    ctx.textAlign = 'left';
    ctx.fillText(bubble, Math.min(catX + 80, canvas.width - w + 10), 278);
  }
}

function renderProgram() {
  const el = document.getElementById('program');
  el.innerHTML = program.length ? '' : '<span class="empty">No blocks yet</span>';
  program.forEach((b, i) => {
    const d = blockDefs[b.type] || {};
    const btn = document.createElement('button');
    btn.className = 'block';
    btn.style.background = d.color || '#ccc';
    btn.textContent = b.type === 'AGAIN' ? `AGAIN ×${b.count || 3}` : (d.label || b.type);
    btn.title = 'Tap to remove. Tap AGAIN to change its count.';
    btn.onclick = () => {
      if (b.type === 'AGAIN') {
        b.count = b.count === 3 ? 4 : b.count === 4 ? 2 : 3;
      } else {
        program.splice(i, 1);
      }
      renderProgram();
    };
    el.appendChild(btn);
  });
}

function renderSteps(steps) {
  const el = document.getElementById('steps');
  el.innerHTML = steps.length ? '' : '<span class="empty">Press GO to expand your program.</span>';
  steps.forEach((s, i) => {
    const span = document.createElement('span');
    span.className = 'step';
    span.style.background = s.color || '#ccc';
    span.textContent = s.label || s.type;
    span.id = 'step-' + i;
    el.appendChild(span);
  });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function animateStep(step) {
  const startX = catX;
  if (step.type === 'WALK') {
    const target = Math.min(startX + 90, canvas.width - 80);
    const t0 = performance.now();
    while (performance.now() - t0 < step.duration_ms && !stopRequested) {
      const p = (performance.now() - t0) / step.duration_ms;
      catX = startX + (target - startX) * p;
      drawCat(); await sleep(16);
    }
    catX = target; drawCat();
  } else if (step.type === 'JUMP') {
    const t0 = performance.now();
    while (performance.now() - t0 < step.duration_ms && !stopRequested) {
      const p = (performance.now() - t0) / step.duration_ms;
      catY = -80 * Math.sin(Math.PI * p);
      drawCat(); await sleep(16);
    }
    catY = 0; drawCat();
  } else if (step.type === 'SPIN') {
    const t0 = performance.now();
    while (performance.now() - t0 < step.duration_ms && !stopRequested) {
      const p = (performance.now() - t0) / step.duration_ms;
      catAngle = 2 * Math.PI * p;
      drawCat(); await sleep(16);
    }
    catAngle = 0; drawCat();
  } else if (step.type === 'SAY') {
    bubble = step.say_text || sayText;
    drawCat();
    await sleep(step.duration_ms);
    bubble = ''; drawCat();
  }
  await sleep(250);
}

async function runProgram() {
  if (running) return;
  const res = await fetch('/api/expand', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({program, say_text: sayText}),
  });
  const data = await res.json();
  const warnEl = document.getElementById('warnings');
  warnEl.textContent = (data.warnings || []).join(' ');
  renderSteps(data.steps || []);
  if (data.hard_error || !data.steps.length) return;
  running = true; stopRequested = false;
  catX = 80; catY = 0; catAngle = 0; bubble = ''; drawCat();
  for (let i = 0; i < data.steps.length && !stopRequested; i++) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    const cur = document.getElementById('step-' + i);
    if (cur) cur.classList.add('active');
    await animateStep(data.steps[i]);
  }
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  running = false;
}

async function init() {
  const res = await fetch('/api/blocks');
  const data = await res.json();
  sayText = data.say_text;
  data.blocks.forEach(d => { blockDefs[d.type] = d; });
  const palette = document.getElementById('palette');
  data.blocks.forEach(d => {
    const btn = document.createElement('button');
    btn.className = 'block big';
    btn.style.background = d.color;
    btn.textContent = d.label;
    btn.onclick = () => {
      const b = {type: d.type};
      if (d.type === 'AGAIN') b.count = 3;
      program.push(b);
      renderProgram();
    };
    palette.appendChild(btn);
  });
  document.getElementById('clearBtn').onclick = () => { program = []; renderProgram(); renderSteps([]); };
  document.getElementById('goBtn').onclick = runProgram;
  document.getElementById('stopBtn').onclick = () => {
    stopRequested = true; running = false;
    catX = 80; catY = 0; catAngle = 0; bubble = ''; drawCat();
  };
  document.getElementById('scanBtn').onclick = async () => {
    const input = document.getElementById('photoInput');
    if (!input.files.length) {
      document.getElementById('scanWarnings').textContent = 'Choose a photo first.';
      return;
    }
    const form = new FormData();
    form.append('photo', input.files[0]);
    const res = await fetch('/api/scan', {method: 'POST', body: form});
    const data = await res.json();
    document.getElementById('scanWarnings').textContent = (data.warnings || []).join(' ');
    // Confirm screen: detected program replaces the tapped program,
    // so the teacher can edit it (tap to remove / change AGAIN count)
    // before pressing GO. Nothing runs automatically from a scan.
    if (data.program && data.program.length) {
      program = data.program;
      renderProgram();
    }
    renderSteps((data.expanded && data.expanded.steps) || []);
  };
  renderProgram(); drawCat();
}
init();
