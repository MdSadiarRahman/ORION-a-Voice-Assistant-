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

function setServiceState(running, quiet = false) {
  const changed = STATE.serviceRunning !== running;
  STATE.serviceRunning = running;
  const toggle = document.getElementById('svcToggle');
  if (toggle) {
    toggle.classList.toggle('active', running);
  }
  if (!changed) return;
  if (running) {
    setStatus('online', 'ONLINE');
    if (!quiet) appendLog('INFO', 'ভয়েস সার্ভিস সক্রিয় করা হয়েছে');
  } else {
    setStatus('offline', 'OFFLINE');
    if (!quiet) appendLog('WARN', 'ভয়েস সার্ভিস সাময়িক স্থগিত');
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

async function openSettings() {
  playUiTick();
  const modal = document.getElementById('settingsModal');
  if (!modal) return;
  try {
    const cfg = await safeApi('get_settings');
    if (cfg) {
      const provEl = document.getElementById('cfgProvider');
      const langEl = document.getElementById('cfgLang');
      const hintEl = document.getElementById('cfgKeyHint');
      const keyEl = document.getElementById('cfgApiKey');
      if (provEl) provEl.value = cfg.provider || 'auto';
      if (langEl) langEl.value = cfg.language || 'bn-BD';
      if (keyEl) keyEl.value = '';
      if (hintEl) {
        hintEl.textContent = cfg.has_api_key
          ? `Current Key: ${cfg.api_key_masked} (active)`
          : 'No Gemini API Key configured yet';
      }
    }
  } catch (e) {
    appendLog('WARN', 'Settings load fallback: ' + e);
  }
  modal.classList.remove('hidden');
}

function closeSettings() {
  const modal = document.getElementById('settingsModal');
  if (modal) modal.classList.add('hidden');
}

async function saveSettings() {
  playUiTick(950);
  const provider = document.getElementById('cfgProvider')?.value || 'auto';
  const api_key = document.getElementById('cfgApiKey')?.value || '';
  const language = document.getElementById('cfgLang')?.value || 'bn-BD';
  try {
    const res = await safeApi('save_settings', { provider, api_key, language });
    if (res && res.status === 'ok') {
      appendLog('SUCCESS', `সেটিংস সংরক্ষণ হয়েছে (Engine: ${provider}, Lang: ${language})`);
      appendChat('SYSTEM', `সেটিংস আপডেট হয়েছে: Provider=${provider}, Language=${language}`, 'system');
      closeSettings();
    } else {
      appendLog('ERROR', 'Settings save error: ' + (res?.message || 'unknown'));
    }
  } catch (e) {
    appendLog('ERROR', 'Settings save failed: ' + e);
  }
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
    const res = await safeApi('toggle_voice');
    STATE.voiceActive = (res && res.is_listening !== undefined) ? Boolean(res.is_listening) : !STATE.voiceActive;
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
  if (prompt === 'Typing Mode') {
    playUiTick(800);
    appendChat('আপনি', 'Typing Mode', 'user');
    try {
      await safeApi('send_command', 'typing mode');
    } catch (e) {
      appendChat('SYSTEM', 'Typing Mode চালু করা যায়নি: ' + e, 'system');
    }
    return;
  }

  const actions = {
    'Open App': ['open_app', 'কোন অ্যাপ খুলবেন?'],
    'Search Web': ['web_search', 'কী সার্চ করবেন?'],
    'Document Q&A': ['document_qa', 'প্রশ্ন এবং চাইলে PDF/DOCX ফাইলের নাম দিন:'],
    'Product Price': ['product_price', 'কোন পণ্যের দাম জানতে চান?']
  };
  const action = actions[prompt];
  if (!action) return;
  await runToolkit(action[0], action[1]);
}

// ── Supported capability action ────────────────────────────────────
async function runToolkit(agentName, promptTitle) {
  const param = window.prompt(promptTitle || 'টাস্ক লিখুন:', '');
  if (param === null || !param.trim()) return;
  playUiTick(650);
  appendChat('আপনি', `${promptTitle || ''} ${param}`.trim(), 'user');
  switchTab(0); // View agent feedback in Tab 0

  try {
    const result = await safeApi('run_toolkit_action', agentName, param.trim());
    if (result && result.status === 'error') {
      appendChat('SYSTEM', result.message || 'এই কাজটি সমর্থিত নয়।', 'system');
    }
  } catch (e) {
    appendChat('SYSTEM', `কাজটি শুরু করা যায়নি: ${e}`, 'system');
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
  const isRunning = state.is_running !== undefined ? state.is_running : true;
  STATE.serviceRunning = isRunning;

  let st = state.state || (isRunning ? 'idle' : 'offline');
  if (!isRunning) st = 'offline';
  STATE.agentState = st;

  const map = {
    idle:      ['online', 'ONLINE'],
    listening: ['listening', 'LISTENING'],
    thinking:  ['thinking', 'THINKING'],
    speaking:  ['speaking', 'SPEAKING'],
    offline:   ['offline', 'OFFLINE']
  };

  const [cls, lbl] = map[st] || (isRunning ? ['online', 'ONLINE'] : ['offline', 'OFFLINE']);
  setStatus(cls, lbl);

  const badge = document.getElementById('vizBadge');
  if (badge) badge.textContent = lbl;

  updateOrbState(st);

  STATE.voiceActive = (st === 'listening');
  const micBtn = document.getElementById('micBtn');
  if (micBtn) micBtn.classList.toggle('active', STATE.voiceActive);

  if (state.message) {
    appendChat('VoiceMate AI', state.message, 'agent');
  }
};

window.appendChat = appendChat;
window.appendLog = appendLog;

window.updateTelemetry = function(data) {
  if (data.is_running !== undefined) {
    setServiceState(data.is_running, true);
  }
  if (data.is_listening !== undefined) {
    STATE.voiceActive = Boolean(data.is_listening);
    const micBtn = document.getElementById('micBtn');
    if (micBtn) micBtn.classList.toggle('active', STATE.voiceActive);
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
      return { is_running: false };
    }
    return { status: 'mock' };
  }
  return await window.pywebview.api[method](...args);
}

// ═════════════════════════════════════════════════════════════════════
//  SOLAR-ORBIT 60 FPS AUDIO-REACTIVE VISUALIZER (HTML5 Canvas)
// ═════════════════════════════════════════════════════════════════════
let orbCanvas, orbCtx, orbAnim;
let orbState = 'idle';
let orbTime = 0;

function initVisualizer() {
  orbCanvas = document.getElementById('orbCanvas');
  if (!orbCanvas) return;
  orbCtx = orbCanvas.getContext('2d');
  resizeCanvas();

  window.removeEventListener('resize', resizeCanvas);
  window.addEventListener('resize', resizeCanvas);

  if (orbAnim) cancelAnimationFrame(orbAnim);
  drawVisualizer();
}

function resizeCanvas() {
  if (!orbCanvas) return;
  const p = orbCanvas.parentElement;
  orbCanvas.width = p && p.clientWidth > 50 ? p.clientWidth : 750;
  orbCanvas.height = p && p.clientHeight > 30 ? p.clientHeight : 160;
}

function updateOrbState(st) {
  orbState = st;
}

function drawVisualizer() {
  if (!orbCanvas || !orbCtx) return;
  orbAnim = requestAnimationFrame(drawVisualizer);
  orbTime += 0.018;

  try {
    const W = orbCanvas.width || 750;
    const H = orbCanvas.height || 160;
    const cx = W / 2;
    const cy = H / 2;

    orbCtx.clearRect(0, 0, W, H);

    // ── State-Specific Palettes & Speeds ────────────────────────────────
    const stateThemes = {
      idle: {
        core: '#8B5CF6',
        corona: '#7C3AED',
        ring1: '#7C3AED',
        ring2: '#A78BFA',
        ring3: '#6D28D9',
        bars: '#8B5CF6',
        speed: 0.75,
        ripple: 0.35,
      },
      listening: {
        core: '#06B6D4',
        corona: '#0891B2',
        ring1: '#06B6D4',
        ring2: '#22D3EE',
        ring3: '#67E8F9',
        bars: '#06B6D4',
        speed: 1.5,
        ripple: 1.0,
      },
      thinking: {
        core: '#F59E0B',
        corona: '#D97706',
        ring1: '#7C3AED',
        ring2: '#F59E0B',
        ring3: '#A78BFA',
        bars: '#FBBF24',
        speed: 2.1,
        ripple: 0.85,
      },
      speaking: {
        core: '#10B981',
        corona: '#059669',
        ring1: '#06B6D4',
        ring2: '#10B981',
        ring3: '#34D399',
        bars: '#10B981',
        speed: 1.4,
        ripple: 0.9,
      },
      offline: {
        core: '#F43F5E',
        corona: '#BE123C',
        ring1: '#F43F5E',
        ring2: '#FB7185',
        ring3: '#E11D48',
        bars: '#F43F5E',
        speed: 0.5,
        ripple: 0.2,
      }
    };

    const theme = stateThemes[orbState] || stateThemes.idle;
    const spd = theme.speed;

    // ── 1. Bilateral Wide Spectrum Harmonic Bars ─────────────────────────
    const sideBars = 20;
    const barW = 3;
    const maxSpan = Math.min(W * 0.38, 260);
    const step = maxSpan / sideBars;
    const startOffset = 110; // start outside solar rings

    for (let i = 0; i < sideBars; i++) {
      let waveAmp = Math.sin(orbTime * spd * 2.2 + i * 0.4);
      let barH = 5 + Math.abs(waveAmp) * (24 * theme.ripple);

      if (orbState === 'listening') {
        barH += Math.abs(Math.sin(orbTime * 4.5 + i * 0.8)) * 18;
      } else if (orbState === 'speaking') {
        barH += Math.abs(Math.cos(orbTime * 3.5 + i * 0.5)) * 16;
      }

      const alpha = 0.2 + 0.45 * Math.min(barH / 35, 1);
      orbCtx.fillStyle = hexToRgba(theme.bars, alpha);

      // Right wing
      const rx = cx + startOffset + step * i;
      orbCtx.fillRect(rx - barW / 2, cy - barH / 2, barW, barH);

      // Left wing
      const lx = cx - startOffset - step * i;
      orbCtx.fillRect(lx - barW / 2, cy - barH / 2, barW, barH);
    }

    // ── 2. Reactive Circular Audio Spectrum Bars (surrounding core) ─────
    const circleBars = 36;
    const innerR = 24;

    for (let j = 0; j < circleBars; j++) {
      const angle = (j / circleBars) * Math.PI * 2;
      let circAmp = Math.sin(orbTime * spd * 3.0 + j * 0.6);
      let barLen = 5 + Math.abs(circAmp) * (14 * theme.ripple);

      if (orbState === 'listening') {
        barLen += Math.abs(Math.sin(orbTime * 5.0 + j * 1.2)) * 12;
      } else if (orbState === 'thinking') {
        barLen += (j % 2 === 0 ? 8 : 2);
      } else if (orbState === 'speaking') {
        barLen += Math.abs(Math.sin(orbTime * 3.5 + j * 0.8)) * 10;
      }

      const cosA = Math.cos(angle);
      const sinA = Math.sin(angle);
      const x1 = cx + cosA * innerR;
      const y1 = cy + sinA * innerR;
      const x2 = cx + cosA * (innerR + barLen);
      const y2 = cy + sinA * (innerR + barLen);

      orbCtx.beginPath();
      orbCtx.moveTo(x1, y1);
      orbCtx.lineTo(x2, y2);
      orbCtx.lineWidth = 1.5;
      orbCtx.strokeStyle = hexToRgba(theme.bars, Math.min(1, 0.45 + (barLen / 30) * 0.4));
      orbCtx.stroke();
    }

    // ── 3. Solar-Orbit Tilted Counter-Rotating Planetary Rings ──────────
    const solarRings = [
      { rx: 54, ry: 22, tilt: -0.32, spd: spd * 1.1,  col: theme.ring1, dash: [6, 4], nodeSize: 3.5 },
      { rx: 76, ry: 28, tilt: 0.42,  spd: -spd * 1.35, col: theme.ring2, dash: [4, 6], nodeSize: 4.0 },
      { rx: 96, ry: 34, tilt: -0.16, spd: spd * 0.75,  col: theme.ring3, dash: [8, 8], nodeSize: 3.0 },
    ];

    solarRings.forEach((rObj) => {
      orbCtx.save();
      orbCtx.translate(cx, cy);
      orbCtx.rotate(rObj.tilt);

      // Orbit ellipse path (using scale + arc for 100% cross-engine compatibility)
      orbCtx.save();
      orbCtx.scale(1, rObj.ry / rObj.rx);
      orbCtx.beginPath();
      orbCtx.arc(0, 0, rObj.rx, 0, Math.PI * 2);
      orbCtx.setLineDash(rObj.dash);
      orbCtx.strokeStyle = hexToRgba(rObj.col, 0.65);
      orbCtx.lineWidth = 1.4;
      orbCtx.shadowColor = rObj.col;
      orbCtx.shadowBlur = 10;
      orbCtx.stroke();
      orbCtx.restore();

      // Orbiting planetary node along the tilted ellipse
      const theta = orbTime * rObj.spd;
      const nx = rObj.rx * Math.cos(theta);
      const ny = rObj.ry * Math.sin(theta);

      // Node trailing glow
      orbCtx.beginPath();
      orbCtx.arc(nx, ny, rObj.nodeSize * 1.8, 0, Math.PI * 2);
      orbCtx.fillStyle = hexToRgba(rObj.col, 0.35);
      orbCtx.fill();

      // Node solid body
      orbCtx.beginPath();
      orbCtx.arc(nx, ny, rObj.nodeSize, 0, Math.PI * 2);
      orbCtx.fillStyle = '#FFFFFF';
      orbCtx.shadowColor = rObj.col;
      orbCtx.shadowBlur = 14;
      orbCtx.fill();

      orbCtx.restore();
    });

    // ── 4. Central Glowing Energy Core ──────────────────────────────────
    const breathFreq = orbState === 'idle' ? 1.6 : (orbState === 'thinking' ? 3.8 : 2.5);
    const pulse = 1 + 0.16 * Math.sin(orbTime * breathFreq);
    const coreRadius = 15 * pulse;

    // Outer Corona Glow
    const coronaGrad = orbCtx.createRadialGradient(cx, cy, 0, cx, cy, coreRadius * 2.2);
    coronaGrad.addColorStop(0, hexToRgba(theme.corona, 0.8));
    coronaGrad.addColorStop(0.5, hexToRgba(theme.core, 0.35));
    coronaGrad.addColorStop(1, 'transparent');

    orbCtx.beginPath();
    orbCtx.arc(cx, cy, coreRadius * 2.2, 0, Math.PI * 2);
    orbCtx.fillStyle = coronaGrad;
    orbCtx.fill();

    // Core Solid Gradient with White Flare
    const coreGrad = orbCtx.createRadialGradient(cx, cy, 0, cx, cy, coreRadius);
    coreGrad.addColorStop(0, '#FFFFFF');
    coreGrad.addColorStop(0.35, hexToRgba(theme.core, 0.95));
    coreGrad.addColorStop(0.85, hexToRgba(theme.corona, 0.7));
    coreGrad.addColorStop(1, 'transparent');

    orbCtx.beginPath();
    orbCtx.arc(cx, cy, coreRadius, 0, Math.PI * 2);
    orbCtx.fillStyle = coreGrad;
    orbCtx.shadowColor = theme.core;
    orbCtx.shadowBlur = 25 * pulse;
    orbCtx.fill();

  } catch (err) {
    console.error('Visualizer render error:', err);
  }
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
