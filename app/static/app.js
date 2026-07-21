/* Cadence - flow, recording, results, PDF, info pages */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const ORDER = ["welcome", "learn", "record", "analyzing", "results"];
let current = "welcome", lastResult = null;

/* ---------- navigation ---------- */
function go(id) {
  if (id === current) return;
  if (current === "record") stopRec();               // don't leave the mic hot
  const from = $("#" + current), to = $("#" + id);
  from.classList.add("leave");
  setTimeout(() => { from.classList.remove("show", "leave"); to.classList.add("show"); window.scrollTo(0, 0); }, 250);
  current = id;
  const idx = ORDER.indexOf(id);
  $("#steps").classList.toggle("hide", idx < 0);      // hide dots on info pages
  $$("#steps span").forEach((d, i) => { d.classList.toggle("on", i === idx); d.classList.toggle("done", i < idx); });
  $("#homeBtn").classList.toggle("show", id !== "welcome");
}
$$("[data-go]").forEach(b => b.addEventListener("click", e => {
  if (b.disabled) return; ripple(e, b);
  const dest = b.dataset.go;
  if (dest === "analyzing") return analyze();
  if (dest === "record" && current === "results") resetRecorder();
  go(dest);
}));
$("#homeBtn").addEventListener("click", () => go("welcome"));
$$("[data-info]").forEach(b => b.addEventListener("click", () => go(b.dataset.info)));

function ripple(e, btn) {
  const r = document.createElement("span"); r.className = "ripple";
  const rect = btn.getBoundingClientRect(), d = Math.max(rect.width, rect.height);
  r.style.width = r.style.height = d + "px";
  r.style.left = (e.clientX - rect.left - d / 2) + "px";
  r.style.top = (e.clientY - rect.top - d / 2) + "px";
  btn.appendChild(r); setTimeout(() => r.remove(), 600);
}
function toast(msg) { const t = $("#toast"); t.textContent = msg; t.classList.add("show"); setTimeout(() => t.classList.remove("show"), 3600); }
function netMsg(e) { return (e instanceof TypeError) ? "Can't reach the server. Please make sure the app server is running, then try again." : e.message; }

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
    stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
  } catch (err) { return toast("We need microphone permission to listen. Please allow it."); }
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const src = audioCtx.createMediaStreamSource(stream);
  analyser = audioCtx.createAnalyser(); analyser.fftSize = 64; src.connect(analyser); drawMeter();
  chunks = []; mediaRec = new MediaRecorder(stream);
  mediaRec.ondataavailable = e => e.data.size && chunks.push(e.data);
  mediaRec.onstop = finishRec; mediaRec.start();
  recwrap.classList.add("recording");
  seconds = 0; $("#timer").textContent = "0.0s · listening…";
  timerInt = setInterval(() => { seconds += 0.1; $("#timer").textContent = seconds.toFixed(1) + "s · tap to stop"; }, 100);
  $("#playback").classList.add("hidden"); $("#analyzeBtn").disabled = true;
});
function drawMeter() {
  const bars = $$("#meter i"), data = new Uint8Array(analyser.frequencyBinCount);
  (function loop() { analyser.getByteFrequencyData(data); bars.forEach((b, i) => { b.style.height = 6 + ((data[i * 2] || 0) / 255) * 30 + "px"; }); meterRAF = requestAnimationFrame(loop); })();
}
function stopRec() {
  clearInterval(timerInt); cancelAnimationFrame(meterRAF);
  if (recwrap.classList.contains("recording")) recwrap.classList.remove("recording");
  if (mediaRec && mediaRec.state !== "inactive") mediaRec.stop();
}
async function finishRec() {
  stream.getTracks().forEach(t => t.stop());
  $("#timer").textContent = "captured (" + seconds.toFixed(1) + "s)";
  const blob = new Blob(chunks, { type: chunks[0]?.type || "audio/webm" });
  const audio = await audioCtx.decodeAudioData(await blob.arrayBuffer());
  wavBlob = encodeWav(resampleMono(audio, 16000), 16000);
  const pb = $("#playback"); pb.src = URL.createObjectURL(wavBlob); pb.classList.remove("hidden");
  if (seconds < 3) toast("A little short - try ~6 seconds for a better read.");
  $("#analyzeBtn").disabled = false;
}
function resetRecorder() { wavBlob = null; $("#analyzeBtn").disabled = true; $("#playback").classList.add("hidden"); $("#timer").textContent = "tap the mic to start"; }

function resampleMono(ab, sr) {
  const n = ab.numberOfChannels, len = ab.length, mono = new Float32Array(len);
  for (let c = 0; c < n; c++) { const d = ab.getChannelData(c); for (let i = 0; i < len; i++) mono[i] += d[i] / n; }
  const ratio = ab.sampleRate / sr, out = new Float32Array(Math.floor(len / ratio));
  for (let i = 0; i < out.length; i++) { const p = i * ratio, i0 = Math.floor(p), f = p - i0; out[i] = (mono[i0] || 0) * (1 - f) + (mono[i0 + 1] || 0) * f; }
  return out;
}
function encodeWav(s, sr) {
  const buf = new ArrayBuffer(44 + s.length * 2), v = new DataView(buf);
  const w = (o, t) => { for (let i = 0; i < t.length; i++) v.setUint8(o + i, t.charCodeAt(i)); };
  w(0, "RIFF"); v.setUint32(4, 36 + s.length * 2, true); w(8, "WAVE"); w(12, "fmt ");
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true); v.setUint32(24, sr, true);
  v.setUint32(28, sr * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); w(36, "data"); v.setUint32(40, s.length * 2, true);
  let o = 44; for (let i = 0; i < s.length; i++) { const x = Math.max(-1, Math.min(1, s[i])); v.setInt16(o, x * 0x7fff, true); o += 2; }
  return new Blob([v], { type: "audio/wav" });
}

/* ---------- analyze ---------- */
const MSGS = ["Listening to your voice…", "Measuring your pitch", "Reading your rhythm", "Checking voice clarity", "Almost there…"];
let msgInt;
async function analyze() {
  if (!wavBlob) return toast("Please record your voice first.");
  go("analyzing"); cycleMsgs();
  const fd = new FormData(); fd.append("audio", wavBlob, "rec.wav"); const t0 = Date.now();
  try {
    const r = await fetch("/api/screen", { method: "POST", body: fd });
    const res = await r.json();
    if (!res.ok) throw new Error(res.error || res.detail || "analysis failed");
    await minWait(t0); stopMsgs(); renderResults(res); go("results");
  } catch (e) { stopMsgs(); toast("Sorry, that didn’t work. " + netMsg(e)); go("record"); }
}
function cycleMsgs() { let i = 0; $("#analyzeMsg").textContent = MSGS[0]; msgInt = setInterval(() => { i = (i + 1) % MSGS.length; $("#analyzeMsg").textContent = MSGS[i]; }, 900); }
function stopMsgs() { clearInterval(msgInt); }
const minWait = t0 => new Promise(r => setTimeout(r, Math.max(0, 1900 - (Date.now() - t0))));

$("#exampleBtn").addEventListener("click", async () => {
  go("analyzing"); cycleMsgs(); const t0 = Date.now();
  try {
    const j = await (await fetch("/api/examples")).json();
    const pick = j.examples[Math.floor(Math.random() * j.examples.length)];
    await minWait(t0); stopMsgs(); renderResults(pick.result, true); go("results");
  } catch (e) { stopMsgs(); toast("Couldn’t load an example. " + netMsg(e)); go("record"); }
});

/* ---------- results ---------- */
const FICON = k => /^(f0|jitter|shimmer|hnr|voiced)/.test(k) ? "i-mark" : k.startsWith("mfcc") ? "i-cpu" : "i-chart";
const BANDS = {
  low: { c: "#17b8a6", title: "Bright and clear", txt: "Your voice shows patterns typical of healthy speech." },
  moderate: { c: "#6c5ce7", title: "A few patterns to note", txt: "Some speech patterns are worth keeping an eye on - nothing conclusive on its own." },
  elevated: { c: "#f2775f", title: "Some patterns worth checking", txt: "A few voice patterns resemble those seen in Parkinson’s. This is only a screening signal - consider talking with a doctor." }
};
function icon(id) { return `<svg class="ic"><use href="#${id}"/></svg>`; }
function renderResults(res, isExample) {
  lastResult = res;
  const pct = Math.round(res.probability_pd * 100), band = res.risk_band, b = BANDS[band] || BANDS.low;
  $("#resTitle").textContent = isExample ? "Example voice report" : "Your voice report";
  const fill = $("#gFill"); fill.style.stroke = b.c; fill.style.strokeDashoffset = 515;
  requestAnimationFrame(() => setTimeout(() => { fill.style.strokeDashoffset = 515 * (1 - pct / 100); }, 60));
  countUp($("#gPct"), pct);
  $("#verdict").textContent = b.title + ". " + b.txt;
  $("#verdict").style.color = band === "elevated" ? "#d1543b" : (band === "moderate" ? "#5b4fd0" : "#0e8a7c");
  $("#narrative").textContent = res.narrative || "";
  const maxS = Math.max(...res.top_factors.map(f => Math.abs(f.shap))) || 1;
  $("#factors").innerHTML = res.top_factors.map((f, i) => {
    const pd = f.shap > 0, w = Math.round(Math.abs(f.shap) / maxS * 100);
    return `<div class="factor" style="--d:${0.14 * i + 0.2}s">
      <div class="frow"><span class="fname">${icon(FICON(f.feature))}${f.label}</span>
      <span class="tag2 ${pd ? "pd" : "hc"}">${icon(pd ? "i-up" : "i-down")}${pd ? "Parkinson’s" : "healthy"}</span></div>
      <div class="bar"><i class="${pd ? "pd" : "hc"}" data-w="${w}"></i></div></div>`;
  }).join("");
  setTimeout(() => $$("#factors .bar i").forEach(i => i.style.width = i.dataset.w + "%"), 400);
  $("#report").innerHTML = res.acoustic_report.map(s => `<div class="stat"><div class="sv">${fmtVal(s.value)}</div><div class="sl">${s.label}</div></div>`).join("");
  $("#resDisclaimer").textContent = res.disclaimer;
  if (band === "low") confetti();
}
function fmtVal(v) { return Math.abs(v) >= 100 ? Math.round(v) : (Math.abs(v) >= 1 ? v.toFixed(2) : v.toFixed(3)); }
function countUp(el, target) { let n = 0; const step = Math.max(1, Math.round(target / 28)); const id = setInterval(() => { n += step; if (n >= target) { n = target; clearInterval(id); } el.innerHTML = n + "<span>%</span>"; }, 40); }
function confetti() {
  const box = $("#confetti"); box.innerHTML = ""; const cols = ["#6c5ce7", "#17b8a6", "#8b7ff0"];
  for (let i = 0; i < 46; i++) { const c = document.createElement("i"); c.style.left = Math.random() * 100 + "%"; c.style.background = cols[i % cols.length]; c.style.animationDuration = 2 + Math.random() * 2 + "s"; c.style.animationDelay = Math.random() * .6 + "s"; box.appendChild(c); }
  setTimeout(() => box.innerHTML = "", 4200);
}

/* ---------- PDF ---------- */
$("#pdfBtn").addEventListener("click", async (e) => {
  if (!lastResult) return toast("Run an analysis first.");
  ripple(e, e.currentTarget);
  try {
    const r = await fetch("/api/report", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(lastResult) });
    if (!r.ok) throw new Error("report failed");
    const blob = await r.blob(), url = URL.createObjectURL(blob), a = document.createElement("a");
    a.href = url; a.download = "cadence_voice_report.pdf"; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  } catch (err) { toast("Could not generate PDF: " + err.message); }
});
