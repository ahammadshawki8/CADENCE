/* Cadence — animated single-page flow */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const ORDER = ["welcome", "learn", "record", "analyzing", "results"];
let current = "welcome";

/* ---------- sparkles ---------- */
(function sparkle() {
  const box = $("#sparkles");
  for (let i = 0; i < 26; i++) {
    const s = document.createElement("span");
    s.textContent = "✦";
    s.style.left = Math.random() * 100 + "%";
    s.style.top = Math.random() * 100 + "%";
    s.style.fontSize = 8 + Math.random() * 14 + "px";
    s.style.animationDelay = Math.random() * 3.4 + "s";
    box.appendChild(s);
  }
})();

/* ---------- navigation ---------- */
function go(id) {
  if (id === current) return;
  const from = $("#" + current), to = $("#" + id);
  from.classList.add("leave");
  setTimeout(() => { from.classList.remove("show", "leave"); to.classList.add("show"); }, 260);
  current = id;
  const idx = ORDER.indexOf(id);
  $$("#steps span").forEach((d, i) => {
    d.classList.toggle("on", i === idx);
    d.classList.toggle("done", i < idx);
  });
}
$$("[data-go]").forEach(b => b.addEventListener("click", e => {
  if (b.disabled) return;
  ripple(e, b);
  const dest = b.dataset.go;
  if (dest === "analyzing") return analyze();      // special handlers
  if (dest === "record" && current === "results") resetRecorder();
  go(dest);
}));

function ripple(e, btn) {
  const r = document.createElement("span");
  r.className = "ripple";
  const rect = btn.getBoundingClientRect();
  const d = Math.max(rect.width, rect.height);
  r.style.width = r.style.height = d + "px";
  r.style.left = (e.clientX - rect.left - d / 2) + "px";
  r.style.top = (e.clientY - rect.top - d / 2) + "px";
  btn.appendChild(r);
  setTimeout(() => r.remove(), 600);
}
function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3200);
}

/* ---------- consent ---------- */
$("#agree").addEventListener("change", e => { $("#toRecord").disabled = !e.target.checked; });

/* ---------- recording ---------- */
let mediaRec, chunks = [], stream, audioCtx, analyser, meterRAF, seconds = 0, timerInt, wavBlob = null;
const micBtn = $("#micBtn"), recwrap = $("#record .recwrap");

buildMeter();
function buildMeter() { const m = $("#meter"); m.innerHTML = ""; for (let i = 0; i < 16; i++) m.appendChild(document.createElement("i")); }

micBtn.addEventListener("click", async () => {
  if (recwrap.classList.contains("recording")) return stopRec();
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: false, noiseSuppression: false, autoGainControl: false }
    });
  } catch (err) { return toast("🎤 We need mic permission to listen. Please allow it!"); }

  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const src = audioCtx.createMediaStreamSource(stream);
  analyser = audioCtx.createAnalyser(); analyser.fftSize = 64; src.connect(analyser);
  drawMeter();

  chunks = [];
  mediaRec = new MediaRecorder(stream);
  mediaRec.ondataavailable = e => e.data.size && chunks.push(e.data);
  mediaRec.onstop = finishRec;
  mediaRec.start();

  recwrap.classList.add("recording");
  seconds = 0; $("#timer").textContent = "0.0s · listening…";
  timerInt = setInterval(() => { seconds += 0.1; $("#timer").textContent = seconds.toFixed(1) + "s · tap to stop"; }, 100);
  $("#playback").classList.add("hidden");
  $("#analyzeBtn").disabled = true;
});

function drawMeter() {
  const bars = $$("#meter i"), data = new Uint8Array(analyser.frequencyBinCount);
  (function loop() {
    analyser.getByteFrequencyData(data);
    bars.forEach((b, i) => { const v = data[i * 2] || 0; b.style.height = 6 + (v / 255) * 30 + "px"; });
    meterRAF = requestAnimationFrame(loop);
  })();
}

function stopRec() {
  clearInterval(timerInt); cancelAnimationFrame(meterRAF);
  recwrap.classList.remove("recording");
  if (mediaRec && mediaRec.state !== "inactive") mediaRec.stop();
}

async function finishRec() {
  stream.getTracks().forEach(t => t.stop());
  $("#timer").textContent = "got it! ✨ (" + seconds.toFixed(1) + "s)";
  const blob = new Blob(chunks, { type: chunks[0]?.type || "audio/webm" });
  const buf = await blob.arrayBuffer();
  const audio = await audioCtx.decodeAudioData(buf);
  wavBlob = encodeWav(resampleMono(audio, 16000), 16000);
  const url = URL.createObjectURL(wavBlob);
  const pb = $("#playback"); pb.src = url; pb.classList.remove("hidden");
  if (seconds < 3) { toast("A little short! Try ~6s for a better read 💫"); }
  $("#analyzeBtn").disabled = false;
}

function resetRecorder() {
  wavBlob = null; $("#analyzeBtn").disabled = true;
  $("#playback").classList.add("hidden"); $("#timer").textContent = "tap the mic to start";
}

/* ---------- audio helpers ---------- */
function resampleMono(audioBuffer, targetSr) {
  const ch = audioBuffer.numberOfChannels, len = audioBuffer.length;
  const mono = new Float32Array(len);
  for (let c = 0; c < ch; c++) { const d = audioBuffer.getChannelData(c); for (let i = 0; i < len; i++) mono[i] += d[i] / ch; }
  const ratio = audioBuffer.sampleRate / targetSr;
  const outLen = Math.floor(len / ratio), out = new Float32Array(outLen);
  for (let i = 0; i < outLen; i++) {
    const pos = i * ratio, i0 = Math.floor(pos), frac = pos - i0;
    out[i] = (mono[i0] || 0) * (1 - frac) + (mono[i0 + 1] || 0) * frac;
  }
  return out;
}
function encodeWav(samples, sr) {
  const buf = new ArrayBuffer(44 + samples.length * 2), view = new DataView(buf);
  const w = (o, s) => { for (let i = 0; i < s.length; i++) view.setUint8(o + i, s.charCodeAt(i)); };
  w(0, "RIFF"); view.setUint32(4, 36 + samples.length * 2, true); w(8, "WAVE"); w(12, "fmt ");
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, sr, true); view.setUint32(28, sr * 2, true); view.setUint16(32, 2, true);
  view.setUint16(34, 16, true); w(36, "data"); view.setUint32(40, samples.length * 2, true);
  let o = 44; for (let i = 0; i < samples.length; i++) { const s = Math.max(-1, Math.min(1, samples[i])); view.setInt16(o, s * 0x7fff, true); o += 2; }
  return new Blob([view], { type: "audio/wav" });
}

/* ---------- analyze ---------- */
const MSGS = ["Listening to your voice…", "Measuring your pitch 🎵", "Feeling the rhythm 🥁",
  "Checking voice clarity ✨", "Almost there! 🌸"];
let msgInt;
async function analyze() {
  if (!wavBlob) return toast("Record your voice first! 🎤");
  go("analyzing"); cycleMsgs();
  const fd = new FormData(); fd.append("audio", wavBlob, "rec.wav");
  const t0 = Date.now();
  try {
    const r = await fetch("/api/screen", { method: "POST", body: fd });
    const res = await r.json();
    if (!res.ok) throw new Error(res.error || res.detail || "analysis failed");
    await minWait(t0); stopMsgs(); renderResults(res); go("results");
  } catch (e) { stopMsgs(); toast("Hmm, that didn’t work: " + e.message); go("record"); }
}
function cycleMsgs() { let i = 0; $("#analyzeMsg").textContent = MSGS[0]; msgInt = setInterval(() => { i = (i + 1) % MSGS.length; $("#analyzeMsg").textContent = MSGS[i]; }, 900); }
function stopMsgs() { clearInterval(msgInt); }
const minWait = t0 => new Promise(r => setTimeout(r, Math.max(0, 1900 - (Date.now() - t0))));

/* ---------- example path ---------- */
$("#exampleBtn").addEventListener("click", async () => {
  go("analyzing"); cycleMsgs(); const t0 = Date.now();
  try {
    const r = await fetch("/api/examples"); const j = await r.json();
    const pick = j.examples[Math.floor(Math.random() * j.examples.length)];
    await minWait(t0); stopMsgs(); renderResults(pick.result, true); go("results");
  } catch (e) { stopMsgs(); toast("Couldn’t load an example 😢"); go("record"); }
});

/* ---------- results ---------- */
const ICON = k => k.startsWith("f0") ? "🎵" : k.startsWith("jitter") ? "〰️" : k.startsWith("shimmer") ? "🔊"
  : k.startsWith("hnr") ? "✨" : (k.startsWith("onset") || k.includes("segments")) ? "⚡" : k.startsWith("pause") ? "⏸️"
  : k.startsWith("mfcc") ? "🎚️" : k.startsWith("zcr") ? "📶" : "🌈";
const BANDS = {
  low: { c: "#8fe3c4", title: "Bright & clear! 🌿", txt: "Your voice shows patterns typical of healthy speech. Lovely!" },
  moderate: { c: "#ffc9a8", title: "A few things to note 🌼", txt: "Some speech patterns are worth keeping an eye on — nothing to worry about on its own." },
  elevated: { c: "#ff9aa2", title: "Some patterns we’d gently flag 🌸", txt: "A few voice patterns resemble those seen in Parkinson’s. This is only a screening signal — please consider chatting with a doctor." }
};

function renderResults(res, isExample) {
  const pct = Math.round(res.probability_pd * 100), band = res.risk_band, b = BANDS[band] || BANDS.low;
  $("#resTitle").textContent = (isExample ? "Example voice report 🌟" : "Your voice report 🌟");
  // gauge
  const fill = $("#gFill"); fill.style.stroke = b.c;
  fill.style.strokeDashoffset = 515; // reset
  requestAnimationFrame(() => setTimeout(() => { fill.style.strokeDashoffset = 515 * (1 - pct / 100); }, 60));
  countUp($("#gPct"), pct);
  $("#verdict").textContent = b.title + " " + b.txt;
  $("#verdict").style.color = band === "elevated" ? "#d15b6a" : (band === "moderate" ? "#c98a52" : "#2f9c78");
  // factors
  const maxS = Math.max(...res.top_factors.map(f => Math.abs(f.shap))) || 1;
  $("#factors").innerHTML = res.top_factors.map((f, i) => {
    const pd = f.shap > 0, w = Math.round(Math.abs(f.shap) / maxS * 100);
    return `<div class="factor" style="--d:${0.15 * i + 0.2}s">
      <div class="frow"><span><span class="fico">${ICON(f.feature)}</span>${f.label}</span>
      <span class="tag2 ${pd ? "pd" : "hc"}">${pd ? "↑ Parkinson’s" : "↓ healthy"}</span></div>
      <div class="bar"><i class="${pd ? "pd" : "hc"}" data-w="${w}"></i></div></div>`;
  }).join("");
  setTimeout(() => $$("#factors .bar i").forEach(i => i.style.width = i.dataset.w + "%"), 400);
  // report card
  $("#report").innerHTML = res.acoustic_report.map(s =>
    `<div class="stat"><div class="sv">${fmtVal(s.value)}</div><div class="sl">${s.label}</div></div>`).join("");
  $("#resDisclaimer").textContent = res.disclaimer;
  if (band === "low") confetti();
}
function fmtVal(v) { return Math.abs(v) >= 100 ? Math.round(v) : (Math.abs(v) >= 1 ? v.toFixed(2) : v.toFixed(3)); }
function countUp(el, target) {
  let n = 0; const step = Math.max(1, Math.round(target / 28));
  const id = setInterval(() => { n += step; if (n >= target) { n = target; clearInterval(id); } el.innerHTML = n + "<span>%</span>"; }, 40);
}
function confetti() {
  const box = $("#confetti"); box.innerHTML = ""; const cols = ["#b8a4ff", "#8fe3c4", "#ffc9a8", "#9fe4ff", "#ff9aa2"];
  for (let i = 0; i < 60; i++) { const c = document.createElement("i"); c.style.left = Math.random() * 100 + "%";
    c.style.background = cols[i % cols.length]; c.style.animationDuration = 2 + Math.random() * 2 + "s";
    c.style.animationDelay = Math.random() * .6 + "s"; box.appendChild(c); }
  setTimeout(() => box.innerHTML = "", 4200);
}
