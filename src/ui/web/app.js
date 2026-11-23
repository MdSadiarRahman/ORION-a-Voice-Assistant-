/* ═════════════════════════════════════════════════════════════════════
   VOICEMATE AI — app.js  |  Deep Space Neural Command Engine
   Audio Synthesizer · Orbital Visualizer · Bridge Dispatcher
═════════════════════════════════════════════════════════════════════ */

'use strict';

// ── Application State ────────────────────────────────────────────────
const STATE = {
  serviceRunning: false,
  muted: false,
  voiceActive: false,
  autoScroll: true,
  currentTab: 0,
  agentState: 'idle', // 'idle' | 'listening' | 'thinking' | 'speaking' | 'offline'
  splashDismissed: false
};

let allLogs = [];

// ── Web Audio API Context (Optional Sci-Fi UI Feedback) ──────────────
let audioCtx = null;
function getAudioContext() {
  if (!audioCtx) {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) audioCtx = new AudioCtx();
    } catch (_) {}
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

/**
 * Futuristic multi-tone chord played on launch (only when user clicks)
 */
function playSciFiLaunchChime() {
  if (STATE.muted) return;
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const now = ctx.currentTime;
    const freqs = [329.63, 493.88, 659.25, 987.77]; // E4, B4, E5, B5 crystal chord

    freqs.forEach((f, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = i % 2 === 0 ? 'sine' : 'triangle';
      osc.frequency.setValueAtTime(f, now);
      osc.frequency.exponentialRampToValueAtTime(f * 1.5, now + 0.8 + i * 0.1);

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.04 / (i + 1), now + 0.08);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.2 + i * 0.15);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now + i * 0.05);
      osc.stop(now + 1.4 + i * 0.15);
    });
  } catch (_) {}
}

/**
 * Subtle UI feedback tick for button clicks
 */
function playUiTick(pitch = 880) {
  if (STATE.muted) return;
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(pitch, now);
    osc.frequency.exponentialRampToValueAtTime(pitch * 1.2, now + 0.04);

    gain.gain.setValueAtTime(0.025, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.05);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.05);
  } catch (_) {}
}

// ── Launch Splash Logic ──────────────────────────────────────────────
function dismissSplash(triggeredByUser = false) {
  if (STATE.splashDismissed) return;
  STATE.splashDismissed = true;

  if (triggeredByUser) {
    playSciFiLaunchChime();
  }

  const splash = document.getElementById('splash');
  if (splash) {
    splash.classList.add('dismissed');
    setTimeout(() => {
      try { splash.remove(); } catch (_) {}
    }, 700);
  }
}

function onSplashClick() {
  dismissSplash(true);
}

// ── DOM Initialization ──────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  // Animate splash progress bar smoothly to 100% over 2.4s
  const bar = document.getElementById('splashBar');
  if (bar) {
    let p = 0;
    const interval = setInterval(() => {
      p += 4;
      bar.style.width = Math.min(p, 100) + '%';
      if (p >= 100) {
        clearInterval(interval);
      }
    }, 90);
  }

  // Auto-dismiss after 2.5 seconds if not clicked
  setTimeout(() => {
    dismissSplash(false);
  }, 2500);

  // Initialize Canvas Orbital Visualizer
  initVisualizer();

  // Initialize Pill Glider
  updatePillGlider(0);
  window.addEventListener('resize', () => updatePillGlider(STATE.currentTab));

  // Telemetry Poll Loop
  startTelemetryPoll();

  // Initial welcome logs
  appendLog('INFO', 'VoiceMate AI Neural Core Initialized (Aethermind Engine)');
  appendLog('SUCCESS', 'pywebview Desktop Web-Shell সংযুক্ত হয়েছে');
});

// ── Tab Switching & Glider Navigation ────────────────────────────────
function switchTab(idx) {
  STATE.currentTab = idx;
  playUiTick(600 + idx * 120);

  // Update tabs
  for (let i = 0; i < 3; i++) {
    const btn = document.getElementById(`pill-${i}`);
    const panel = document.getElementById(`tab-${i}`);
    if (btn) {
      btn.classList.toggle('active', i === idx);
      btn.setAttribute('aria-selected', i === idx ? 'true' : 'false');
    }
    if (panel) {
      panel.classList.toggle('active', i === idx);
    }
  }

  updatePillGlider(idx);
}

function updatePillGlider(idx) {
  const glider = document.getElementById('pillGlider');
  const targetBtn = document.getElementById(`pill-${idx}`);
  if (!glider || !targetBtn) return;

  const left = targetBtn.offsetLeft;
  const width = targetBtn.offsetWidth;

  glider.style.transform = `translateX(${left - 4}px)`;
  glider.style.width = `${width}px`;
}

// ── HUD Controls ────────────────────────────────────────────────────
async function toggleService() {
  playUiTick();
  try {
    const result = await safeApi('toggle_service');
    if (result && result.is_running !== undefined) {
      setServiceState(result.is_running);
    }
  } catch (e) {
    appendLog('ERROR', 'Service toggle ব্যর্থ: ' + e);
  }
}

function setServiceState(running) {
  STATE.serviceRunning = running;
  const toggle = document.getElementById('svcToggle');
  if (toggle) {
    toggle.classList.toggle('active', running);
  }
  if (running) {
    setStatus('online', 'ONLINE');
    appendLog('INFO', 'ভয়েস সার্ভিস সক্রিয় করা হয়েছে');
  } else {
    setStatus('offline', 'OFFLINE');
    appendLog('WARN', 'ভয়েস সার্ভিস সাময়িক স্থগিত');
  }
}

function toggleMute() {
  STATE.muted = !STATE.muted;
  const icon = document.getElementById('muteIcon');
  if (icon) {
    icon.textContent = STATE.muted ? '🔇' : '🔊';
  }
  if (!STATE.muted) playUiTick(1000);
  appendLog('INFO', `অডিও ফিডব্যাক: ${STATE.muted ? 'নিঃশব্দ (Muted)' : 'সক্রিয় (Unmuted)'}`);
}

function openSettings() {
  playUiTick();
  appendLog('AGENT', 'Settings ইন্টারফেস অনুরোধ করা হয়েছে');
  appendChat('SYSTEM', 'সেটিংস অপশন: মাইক্রোফোন, স্পিচ ভয়েস ও API কনফিগারেশন।', 'system');
}

// ── Status Dot & Label Helper ───────────────────────────────────────
function setStatus(cls, label) {
  const pill = document.getElementById('statusPill');
  const text = document.getElementById('statusText');
  if (!pill || !text) return;

  pill.className = `status-pill ${cls}`;
  text.textContent = label;
}

// ── Voice Mode Toggle ───────────────────────────────────────────────
async function toggleVoice() {
  playUiTick(750);
  try {
    await safeApi('toggle_voice');
    STATE.voiceActive = !STATE.voiceActive;
    const btn = document.getElementById('micBtn');
    if (btn) {
      btn.classList.toggle('active', STATE.voiceActive);
    }
  } catch (e) {
    appendLog('ERROR', 'Voice mode পরিবর্তন ব্যর্থ: ' + e);
  }
}

// ── Send Command ────────────────────────────────────────────────────
async function sendCommand() {
  const input = document.getElementById('cmdInput');
  if (!input) return;

  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  appendChat('আপনি', text, 'user');
  playUiTick(900);

  try {
    await safeApi('send_command', text);
  } catch (e) {
    appendChat('SYSTEM', 'ব্যাকএন্ড কমান্ড পৌঁছায়নি: ' + e, 'system');
  }
}

// ── Quick Action Chip ───────────────────────────────────────────────
async function quickAction(prompt) {
  playUiTick(800);
  appendChat('আপনি', prompt, 'user');
  try {
    await safeApi('trigger_quick_action', prompt);
  } catch (e) {
    appendChat('SYSTEM', 'Quick Action ব্যর্থ: ' + e, 'system');
  }
}

// ── Toolkit Action Trigger ──────────────────────────────────────────
async function runToolkit(agentName, promptTitle) {
  playUiTick(650);
  const param = window.prompt(promptTitle || 'টাস্ক লিখুন:', '');
  if (param === null) return;

  appendLog('AGENT', `টুলকিট সক্রিয়: ${agentName} — "${param}"`);
  switchTab(0); // View agent feedback in Tab 0

  try {
    await safeApi('run_toolkit_action', agentName, param);
  } catch (e) {
    appendLog('ERROR', `টুলকিট চালনায় ত্রুটি: ${e}`);
  }
}

// ── Telemetry Polling ───────────────────────────────────────────────
function startTelemetryPoll() {
  async function poll() {
    try {
      const data = await safeApi('get_telemetry');
      if (data) updateTelemetry(data);
    } catch (_) {}
    setTimeout(poll, 15000); // 15 sec periodic poll
  }
  setTimeout(poll, 1500);
}

// ── Python Bridge Push Callbacks (invoked via evaluate_js) ───────────
window.onAgentStateChange = function(state) {
  const st = state.state || 'idle';
  STATE.agentState = st;

  const map = {
    idle:      ['online', 'ONLINE'],
    listening: ['listening', 'LISTENING'],
    thinking:  ['thinking', 'THINKING'],
    speaking:  ['speaking', 'SPEAKING'],
    offline:   ['offline', 'OFFLINE']
  };

  const [cls, lbl] = map[st] || ['online', 'ONLINE'];
  setStatus(cls, lbl);

  const badge = document.getElementById('vizBadge');
  if (badge) badge.textContent = lbl;

  updateOrbState(st);

  if (state.message) {
    appendChat('VoiceMate AI', state.message, 'agent');
  }
};

window.appendChat = appendChat;
window.appendLog = function(tag, msg) { appendLog(tag, msg); };

window.updateTelemetry = function(data) {
  if (data.battery !== undefined && data.battery !== null) {
    const pct = document.getElementById('batPct');
    if (pct) pct.textContent = data.battery + '%';

    const charge = document.getElementById('batCharge');
    if (charge) charge.style.display = data.charging ? 'inline' : 'none';
  }

  if (data.engine) {
    const engName = document.getElementById('engineName');
    if (engName) engName.textContent = data.engine;
  }

  if (data.is_running !== undefined) {
    setServiceState(data.is_running);
  }
};

function updateTelemetry(d) {
  window.updateTelemetry(d);
}

// ── Chat Stream Render Helper ───────────────────────────────────────
function appendChat(sender, text, type) {
  const stream = document.getElementById('chatStream');
  if (!stream) return;

  const welcome = document.getElementById('chatWelcome');
  if (welcome) welcome.remove();

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${type || 'agent'}`;

  const avatar = document.createElement('div');
  avatar.className = 'bubble-avatar';
  avatar.textContent = type === 'user' ? '👤' : (type === 'system' ? '⚙' : '◈');

  const body = document.createElement('div');
  body.className = 'bubble-body font-bengali';
  body.textContent = text;

  const time = document.createElement('div');
  time.className = 'bubble-time font-mono';
  time.textContent = new Date().toLocaleTimeString('bn-BD', { hour: '2-digit', minute: '2-digit' });

  if (type === 'system') {
    body.className = 'bubble-body font-mono text-xs text-emerald-400 bg-emerald-950/20 border border-emerald-500/30';
    bubble.appendChild(body);
  } else {
    body.appendChild(time);
    bubble.appendChild(avatar);
    bubble.appendChild(body);
  }

  stream.appendChild(bubble);
  stream.scrollTop = stream.scrollHeight;
}

// ── Cyber Telemetry Console Log Helper ──────────────────────────────
function appendLog(tag, msg) {
  const ts = new Date().toLocaleTimeString('en-GB', { hour12: false });
  allLogs.push({ ts, tag, msg });

  const consoleBox = document.getElementById('teleConsole');
  if (!consoleBox) return;

  const searchInput = document.getElementById('teleSearch');
  const filter = searchInput ? searchInput.value.toLowerCase() : '';

  const line = buildLogLine(ts, tag, msg);
  if (filter && !msg.toLowerCase().includes(filter) && !tag.toLowerCase().includes(filter)) {
    line.classList.add('hidden');
  }

  consoleBox.appendChild(line);
  if (STATE.autoScroll) {
    consoleBox.scrollTop = consoleBox.scrollHeight;
  }
}

function buildLogLine(ts, tag, msg) {
  const line = document.createElement('div');
  line.className = 'log-line';
  line.dataset.msg = msg.toLowerCase();
  line.dataset.tag = tag.toLowerCase();

  const tagMap = {
    INFO: 'info',
    AGENT: 'agent',
    SUCCESS: 'success',
    WARN: 'warn',
    ERROR: 'error'
  };
  const tagCls = tagMap[tag.toUpperCase()] || 'info';

  line.innerHTML = `
    <span class="log-ts">${ts}</span>
    <span class="log-tag ${tagCls}">[${tag.toUpperCase()}]</span>
    <span class="log-msg">${escapeHtml(msg)}</span>
  `;
  return line;
}

function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function filterLogs() {
  const searchInput = document.getElementById('teleSearch');
  const q = searchInput ? searchInput.value.toLowerCase() : '';

  document.querySelectorAll('.log-line').forEach(line => {
    const match = !q || line.dataset.msg.includes(q) || line.dataset.tag.includes(q);
    line.classList.toggle('hidden', !match);
  });
}

function clearLogs() {
  playUiTick();
  const consoleBox = document.getElementById('teleConsole');
  if (consoleBox) consoleBox.innerHTML = '';
  allLogs = [];
  appendLog('INFO', 'লগ কনসোল পরিষ্কার করা হয়েছে');
}

function toggleAutoScroll() {
  playUiTick();
  STATE.autoScroll = !STATE.autoScroll;
  const btn = document.getElementById('autoScrollBtn');
  if (btn) {
    btn.classList.toggle('on', STATE.autoScroll);
    btn.textContent = STATE.autoScroll ? '⬇ Auto-Scroll ON' : '⏸ Auto-Scroll OFF';
  }
}

// ── pywebview API Safe Call ──────────────────────────────────────────
async function safeApi(method, ...args) {
  if (!window.pywebview || !window.pywebview.api) {
    if (method === 'get_telemetry') {
      return { battery: 92, charging: false, engine: '⚡ Gemini 3.8 Flash', is_running: false };
    }
    return { status: 'mock' };
  }
  return await window.pywebview.api[method](...args);
}

// ═════════════════════════════════════════════════════════════════════
//  CANVAS ORBITAL VISUALIZER (60 FPS Aethermind Audio Reactor)
// ═════════════════════════════════════════════════════════════════════
let orbCanvas, orbCtx, orbAnim;
let orbState = 'idle';
let orbTime = 0;

function initVisualizer() {
  orbCanvas = document.getElementById('orbCanvas');
  if (!orbCanvas) return;
  orbCtx = orbCanvas.getContext('2d');
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
  drawVisualizer();
}

function resizeCanvas() {
  if (!orbCanvas || !orbCanvas.parentElement) return;
  orbCanvas.width = orbCanvas.parentElement.offsetWidth;
  orbCanvas.height = orbCanvas.parentElement.offsetHeight;
}

function updateOrbState(st) {
  orbState = st;
}

function drawVisualizer() {
  if (!orbCanvas || !orbCtx) return;
  orbAnim = requestAnimationFrame(drawVisualizer);
  orbTime += 0.018;

  const W = orbCanvas.width;
  const H = orbCanvas.height;
  const cx = W / 2;
  const cy = H / 2;

  orbCtx.clearRect(0, 0, W, H);

  // Dynamic theme colors per agent state
  const colors = {
    idle:      { core: '#06B6D4', ring: '#7C3AED', wave: '#67E8F9' },
    listening: { core: '#06B6D4', ring: '#06B6D4', wave: '#A78BFA' },
    thinking:  { core: '#7C3AED', ring: '#A78BFA', wave: '#C4B5FD' },
    speaking:  { core: '#F59E0B', ring: '#FBBF24', wave: '#FCD34D' },
    offline:   { core: '#F43F5E', ring: '#FB7185', wave: '#FDA4AF' }
  };
  const c = colors[orbState] || colors.idle;

  const speed = orbState === 'thinking' ? 2.2 : (orbState === 'speaking' ? 1.6 : (orbState === 'listening' ? 1.4 : 0.8));

  // 1. Bilateral Spectrum Wave Bars
  const bars = 28;
  const barW = 3;
  const maxSpan = Math.min(W * 0.44, 320);
  const step = maxSpan / bars;

  for (let i = 0; i < bars; i++) {
    let amp = Math.sin(orbTime * speed * 2 + i * 0.45);
    let h = 6 + Math.abs(amp) * 36;

    if (orbState === 'idle') h *= 0.35;
    if (orbState === 'listening') h = 10 + Math.abs(Math.sin(orbTime * 4 + i * 0.7)) * 42;
    if (orbState === 'speaking') h = 12 + Math.abs(Math.sin(orbTime * 5 + i * 0.6)) * 48;

    const alpha = 0.25 + 0.5 * (h / 50);
    orbCtx.fillStyle = hexToRgba(c.wave, alpha);

    // Right Spectrum
    const rx = cx + step * (i + 0.6);
    orbCtx.fillRect(rx - barW / 2, cy - h / 2, barW, h);

    // Left Spectrum
    const lx = cx - step * (i + 0.6);
    orbCtx.fillRect(lx - barW / 2, cy - h / 2, barW, h);
  }

  // 2. Orbital Sci-Fi Rings
  const rings = [
    { r: 52, spd: speed * 0.8,  dash: [8, 6], w: 1.5, col: c.ring,  alpha: 0.7 },
    { r: 36, spd: -speed * 1.2, dash: [4, 4], w: 1.2, col: c.core,  alpha: 0.6 },
    { r: 22, spd: speed * 1.5,  dash: [],     w: 1.0, col: '#FFF',   alpha: 0.5 }
  ];

  rings.forEach(ring => {
    orbCtx.save();
    orbCtx.translate(cx, cy);
    orbCtx.rotate(orbTime * ring.spd);

    orbCtx.beginPath();
    orbCtx.arc(0, 0, ring.r, 0, Math.PI * 2);
    orbCtx.setLineDash(ring.dash);
    orbCtx.strokeStyle = hexToRgba(ring.col, ring.alpha);
    orbCtx.lineWidth = ring.w;
    orbCtx.shadowColor = ring.col;
    orbCtx.shadowBlur = 10;
    orbCtx.stroke();

    // Satellite node on outermost ring
    if (ring.dash.length > 0) {
      orbCtx.beginPath();
      orbCtx.arc(ring.r, 0, 3, 0, Math.PI * 2);
      orbCtx.fillStyle = '#FFF';
      orbCtx.shadowBlur = 14;
      orbCtx.shadowColor = ring.col;
      orbCtx.fill();
    }

    orbCtx.restore();
  });

  // 3. Glowing Neural Core
  const pulse = 1 + 0.16 * Math.sin(orbTime * (orbState === 'idle' ? 1.5 : 3.5));
  const grad = orbCtx.createRadialGradient(cx, cy, 0, cx, cy, 18 * pulse);
  grad.addColorStop(0, '#FFFFFF');
  grad.addColorStop(0.35, hexToRgba(c.core, 0.9));
  grad.addColorStop(0.8, hexToRgba(c.ring, 0.4));
  grad.addColorStop(1, 'transparent');

  orbCtx.beginPath();
  orbCtx.arc(cx, cy, 18 * pulse, 0, Math.PI * 2);
  orbCtx.fillStyle = grad;
  orbCtx.shadowColor = c.core;
  orbCtx.shadowBlur = 24 * pulse;
  orbCtx.fill();
}

function hexToRgba(hex, alpha) {
  let c = hex.replace('#', '');
  if (c.length === 3) c = c.split('').map(x => x + x).join('');
  const num = parseInt(c, 16);
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return `rgba(${r},${g},${b},${alpha})`;
}
