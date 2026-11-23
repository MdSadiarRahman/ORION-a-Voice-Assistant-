/* ══════════════════════════════════════════════════
   ORION AI — app.js  |  Bridge Client + Visualizer
══════════════════════════════════════════════════ */

'use strict';

// ── State ──────────────────────────────────────────
const STATE = {
  serviceRunning: false,
  muted: false,
  voiceActive: false,
  autoScroll: true,
  currentTab: 0,
  agentState: 'idle',    // idle | listening | thinking | speaking
};

let allLogs = [];        // {ts, tag, msg} for filter
const audioCtx = (() => { try { return new (window.AudioContext || window.webkitAudioContext)(); } catch { return null; } })();

// ── Splash ─────────────────────────────────────────
function dismissSplash() {
  const sp = document.getElementById('splash');
  sp.classList.add('hidden');
  setTimeout(() => sp.remove(), 700);
}

window.addEventListener('DOMContentLoaded', () => {
  setTimeout(dismissSplash, 1600);   // auto-dismiss after 1.6 s
  initVisualizer();
  startTelemetryPoll();
  appendLog('INFO', 'ORION AI Desktop — Neural Command Center initialized');
  appendLog('INFO', 'pywebview bridge প্রস্তুত');
});

// ── Tab Navigation ──────────────────────────────────
function switchTab(idx) {
  STATE.currentTab = idx;
  document.querySelectorAll('.tab-panel').forEach((p, i) => p.classList.toggle('active', i === idx));
  document.querySelectorAll('.pill').forEach((p, i) => p.classList.toggle('active', i === idx));
  playUiTick();
}

// ── HUD Controls ───────────────────────────────────
async function toggleService() {
  try {
    const result = await safeApi('toggle_service');
    if (result && result.is_running !== undefined) {
      updateServiceBtn(result.is_running);
    }
  } catch (e) { appendLog('ERROR', 'Service toggle failed: ' + e); }
}

function updateServiceBtn(running) {
  STATE.serviceRunning = running;
  const btn = document.getElementById('serviceBtn');
  const icon = document.getElementById('serviceIcon');
  const txt = document.getElementById('serviceTxt');
  if (running) {
    btn.classList.add('active');
    icon.textContent = '⏹';
    txt.textContent = 'STOP';
    setStatus('online', 'ONLINE');
  } else {
    btn.classList.remove('active');
    icon.textContent = '▶';
    txt.textContent = 'START';
    setStatus('offline', 'OFFLINE');
  }
}

function toggleMute() {
  STATE.muted = !STATE.muted;
  document.getElementById('muteIcon').textContent = STATE.muted ? '🔇' : '🔊';
}

// ── Status Dot ─────────────────────────────────────
function setStatus(cls, label) {
  const dot = document.getElementById('statusDot');
  const lbl = document.getElementById('statusLabel');
  dot.className = 'status-dot ' + cls;
  lbl.textContent = label;
}

// ── Voice Toggle ───────────────────────────────────
async function toggleVoice() {
  try {
    const result = await safeApi('toggle_voice');
    STATE.voiceActive = !STATE.voiceActive;
    const btn = document.getElementById('voiceBtn');
    btn.classList.toggle('listening', STATE.voiceActive);
    playUiTick();
  } catch (e) { appendLog('ERROR', 'Voice toggle failed: ' + e); }
}

// ── Send Command ───────────────────────────────────
async function sendCommand() {
  const inp = document.getElementById('cmdInput');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  appendChat('আপনি', text, 'user');
  playUiTick();
  try {
    await safeApi('send_command', text);
  } catch (e) {
    appendChat('SYSTEM', 'Backend unreachable: ' + e, 'system');
  }
}

// ── Quick Action ───────────────────────────────────
async function quickAction(prompt) {
  appendChat('আপনি', prompt, 'user');
  playUiTick();
  try {
    await safeApi('trigger_quick_action', prompt);
  } catch (e) {
    appendChat('SYSTEM', 'Quick action failed: ' + e, 'system');
  }
}

// ── Toolkit Action ─────────────────────────────────
async function runToolkit(agentName, promptText) {
  const param = window.prompt(promptText || 'টাস্ক লিখুন:', '');
  if (param === null) return;
  appendLog('AGENT', `Toolkit: ${agentName} — "${param}"`);
  switchTab(0);   // jump to chat tab to see response
  try {
    await safeApi('run_toolkit_action', agentName, param);
  } catch (e) {
    appendLog('ERROR', 'Toolkit action failed: ' + e);
  }
}

// ── Telemetry Polling ──────────────────────────────
function startTelemetryPoll() {
  async function poll() {
    try {
      const t = await safeApi('get_telemetry');
      if (t) updateTelemetry(t);
    } catch (_) {}
    setTimeout(poll, 30000);
  }
  setTimeout(poll, 2000);
}

// ── Push Callbacks (called from Python via evaluate_js) ──

window.onAgentStateChange = function(state) {
  STATE.agentState = state.state || 'idle';
  const map = { idle: ['online','IDLE'], listening: ['listen','LISTENING'],
                thinking: ['think','THINKING'], speaking: ['speak','SPEAKING'], error: ['error','ERROR'] };
  const [cls, lbl] = map[STATE.agentState] || ['online','IDLE'];
  setStatus(cls, lbl);
  document.getElementById('orbLabel').textContent = lbl;
  updateOrbState(STATE.agentState);

  if (state.message) appendChat('ORION', state.message, 'agent');
};

window.appendChat = appendChat;

window.appendLog = function(tag, msg) { appendLog(tag, msg); };

window.updateTelemetry = function(data) {
  if (data.battery !== undefined) {
    document.getElementById('batteryPct').textContent = data.battery + '%';
    document.getElementById('chargeIcon').style.display = data.charging ? 'inline' : 'none';
  }
  if (data.engine) document.getElementById('engineBadge').textContent = data.engine;
  if (data.is_running !== undefined) updateServiceBtn(data.is_running);
};

function updateTelemetry(t) {
  window.updateTelemetry(t);
}

// ── Chat Helpers ───────────────────────────────────
function appendChat(sender, text, type) {
  const stream = document.getElementById('chatStream');
  // remove welcome widget on first message
  const welcome = stream.querySelector('.chat-welcome');
  if (welcome) welcome.remove();

  const wrap = document.createElement('div');
  wrap.className = 'chat-bubble ' + (type || 'agent');

  const avatar = document.createElement('div');
  avatar.className = 'bubble-avatar';
  avatar.textContent = type === 'user' ? '👤' : (type === 'system' ? '⚙' : '◈');

  const body = document.createElement('div');
  body.className = 'bubble-body';
  body.textContent = text;

  const time = document.createElement('div');
  time.className = 'bubble-time';
  time.textContent = new Date().toLocaleTimeString('bn-BD', {hour:'2-digit', minute:'2-digit'});

  if (type !== 'system') {
    body.appendChild(document.createElement('br'));
    body.appendChild(time);
  }

  if (type === 'system') {
    wrap.appendChild(body);
  } else {
    wrap.appendChild(avatar);
    wrap.appendChild(body);
  }

  stream.appendChild(wrap);
  stream.scrollTop = stream.scrollHeight;
}

// ── Log Helpers ────────────────────────────────────
function appendLog(tag, msg) {
  const ts = new Date().toLocaleTimeString('en-GB', {hour12: false});
  allLogs.push({ ts, tag, msg });

  const console_ = document.getElementById('teleConsole');
  const filter = document.getElementById('teleSearch').value.toLowerCase();

  const line = buildLogLine(ts, tag, msg);
  if (filter && !msg.toLowerCase().includes(filter) && !tag.toLowerCase().includes(filter)) {
    line.classList.add('hidden');
  }

  console_.appendChild(line);
  if (STATE.autoScroll) console_.scrollTop = console_.scrollHeight;
}

function buildLogLine(ts, tag, msg) {
  const line = document.createElement('div');
  line.className = 'log-line';
  line.dataset.msg = msg.toLowerCase();
  line.dataset.tag = tag.toLowerCase();

  const tagMap = { INFO:'info', AGENT:'agent', SUCCESS:'success', WARN:'warn', ERROR:'error' };
  const tagCls = tagMap[tag.toUpperCase()] || 'info';

  line.innerHTML = `<span class="log-ts">${ts}</span>
    <span class="log-tag ${tagCls}">[${tag.toUpperCase()}]</span>
    <span class="log-msg">${escHtml(msg)}</span>`;
  return line;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function filterLogs() {
  const q = document.getElementById('teleSearch').value.toLowerCase();
  document.querySelectorAll('.log-line').forEach(l => {
    const match = !q || l.dataset.msg.includes(q) || l.dataset.tag.includes(q);
    l.classList.toggle('hidden', !match);
  });
}

function clearLogs() {
  document.getElementById('teleConsole').innerHTML = '';
  allLogs = [];
  appendLog('INFO', 'Log console cleared');
}

function toggleAutoScroll() {
  STATE.autoScroll = !STATE.autoScroll;
  const btn = document.getElementById('autoScrollBtn');
  btn.classList.toggle('on', STATE.autoScroll);
  btn.textContent = '⬇ Auto-Scroll ' + (STATE.autoScroll ? 'ON' : 'OFF');
}

// ── API Bridge Helper ──────────────────────────────
async function safeApi(method, ...args) {
  if (!window.pywebview || !window.pywebview.api) {
    console.warn('pywebview bridge not ready, method:', method);
    // For development/preview: return mock data
    if (method === 'get_telemetry') return { battery: 85, charging: false, engine: '⚡ Gemini 3.8 Flash', is_running: false };
    return { status: 'mock' };
  }
  return await window.pywebview.api[method](...args);
}

// ── UI Sounds (optional, non-blocking) ────────────
function playUiTick() {
  if (STATE.muted || !audioCtx) return;
  try {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain); gain.connect(audioCtx.destination);
    osc.type = 'sine'; osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.03, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.08);
    osc.start(); osc.stop(audioCtx.currentTime + 0.08);
  } catch (_) {}
}

// ══════════════════════════════════════════════════
//  ORBITAL VISUALIZER (Canvas Animation)
// ══════════════════════════════════════════════════
let orbCanvas, orbCtx, orbAnim, orbState = 'idle';
let orbTime = 0;

function initVisualizer() {
  orbCanvas = document.getElementById('orbCanvas');
  orbCtx = orbCanvas.getContext('2d');
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
  drawOrb();
}

function resizeCanvas() {
  if (!orbCanvas) return;
  orbCanvas.width = orbCanvas.parentElement.offsetWidth;
  orbCanvas.height = 180;
}

function updateOrbState(state) { orbState = state; }

function drawOrb() {
  if (!orbCanvas || !orbCtx) return;
  orbAnim = requestAnimationFrame(drawOrb);
  orbTime += 0.016;

  const W = orbCanvas.width, H = orbCanvas.height;
  const cx = W / 2, cy = H / 2;

  orbCtx.clearRect(0, 0, W, H);

  // Color map per state
  const colors = {
    idle:      { ring: '#00D4FF', core: '#00D4FF', spec: '#8B5CF6' },
    listening: { ring: '#00D4FF', core: '#00FFFF', spec: '#00D4FF' },
    thinking:  { ring: '#8B5CF6', core: '#A78BFA', spec: '#8B5CF6' },
    speaking:  { ring: '#FFAA00', core: '#FFD700', spec: '#FF8C00' },
    error:     { ring: '#FF4466', core: '#FF6688', spec: '#FF2244' },
  };
  const c = colors[orbState] || colors.idle;
  const speed = orbState === 'thinking' ? 1.6 : (orbState === 'speaking' ? 1.2 : 0.7);

  // ── Spectrum bars (bilateral) ──
  const barCount = 24;
  const barW = 3;
  const spread = Math.min(W * 0.42, 300);
  const barSpacing = spread / barCount;

  for (let i = 0; i < barCount; i++) {
    let amp = 0.3 + 0.7 * Math.abs(Math.sin(orbTime * speed * 1.5 + i * 0.4));
    if (orbState === 'idle') amp *= 0.35;
    if (orbState === 'listening') amp = 0.4 + 0.6 * Math.abs(Math.sin(orbTime * 3 + i * 0.5));
    const barH = 8 + amp * 60;
    const alpha = 0.4 + 0.5 * amp;

    orbCtx.fillStyle = hexAlpha(c.spec, alpha);

    // Right side
    const rx = cx + barSpacing * (i + 0.5);
    orbCtx.fillRect(rx - barW / 2, cy - barH / 2, barW, barH);

    // Left side
    const lx = cx - barSpacing * (i + 0.5);
    orbCtx.fillRect(lx - barW / 2, cy - barH / 2, barW, barH);
  }

  // ── Orbital rings ──
  const rings = [
    { r: 55, speed: speed * 0.7,  alpha: 0.6, dash: [8, 8]  },
    { r: 38, speed: -speed * 1.1, alpha: 0.5, dash: [4, 6]  },
    { r: 22, speed: speed * 1.4,  alpha: 0.4, dash: []      },
  ];

  rings.forEach(ring => {
    orbCtx.save();
    orbCtx.translate(cx, cy);
    orbCtx.rotate(orbTime * ring.speed);
    orbCtx.beginPath();
    orbCtx.arc(0, 0, ring.r, 0, Math.PI * 2);
    orbCtx.setLineDash(ring.dash);
    orbCtx.strokeStyle = hexAlpha(c.ring, ring.alpha);
    orbCtx.lineWidth = 1.5;
    orbCtx.shadowColor = c.ring;
    orbCtx.shadowBlur = 8;
    orbCtx.stroke();

    // Bright node on ring
    const nx = ring.r, ny = 0;
    orbCtx.beginPath();
    orbCtx.arc(nx, ny, 3, 0, Math.PI * 2);
    orbCtx.fillStyle = c.ring;
    orbCtx.shadowBlur = 12;
    orbCtx.fill();
    orbCtx.restore();
  });

  // ── Core glow ──
  const pulseFactor = 1 + 0.15 * Math.sin(orbTime * (orbState === 'idle' ? 1.5 : 3));
  const gradient = orbCtx.createRadialGradient(cx, cy, 0, cx, cy, 18 * pulseFactor);
  gradient.addColorStop(0, hexAlpha(c.core, 0.95));
  gradient.addColorStop(0.4, hexAlpha(c.core, 0.5));
  gradient.addColorStop(1, 'transparent');

  orbCtx.beginPath();
  orbCtx.arc(cx, cy, 18 * pulseFactor, 0, Math.PI * 2);
  orbCtx.fillStyle = gradient;
  orbCtx.shadowColor = c.core;
  orbCtx.shadowBlur = 24 * pulseFactor;
  orbCtx.fill();
}

function hexAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1,3),16), g = parseInt(hex.slice(3,5),16), b = parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${alpha})`;
}
