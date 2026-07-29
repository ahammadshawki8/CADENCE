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
function netMsg(e) { return (e instanceof TypeError) ? t("toastNet") : e.message; }

/* ---------- consent ---------- */
$("#agree").addEventListener("change", e => { $("#toRecord").disabled = !e.target.checked; });

/* ---------- recording ---------- */
let mediaRec, chunks = [], stream, audioCtx, analyser, meterRAF, seconds = 0, timerInt, wavBlob = null;
const micBtn = $("#micBtn"), recwrap = $("#record .recwrap");
buildMeter();
function buildMeter() { const m = $("#meter"); m.innerHTML = ""; for (let i = 0; i < 16; i++) m.appendChild(document.createElement("i")); }

/* ---------- multilingual passage + live word highlighting ---------- */
let PASSAGES = { en: { name: "English", dir: "ltr", rate: 2.4, text: "The North Wind and the Sun were disputing which was the stronger, when a traveler came along wrapped in a warm cloak." } };
let currentLang = "en";
let T = {};

/* i18n: t(key) with {var} interpolation; falls back to English then the key itself. */
function t(key, vars) {
  let s = (T[currentLang] && T[currentLang][key]) || (T.en && T.en[key]) || key;
  return vars ? s.replace(/\{(\w+)\}/g, (_, k) => (vars[k] != null ? vars[k] : "")) : s;
}
function applyLang() {
  document.documentElement.dir = (PASSAGES[currentLang] && PASSAGES[currentLang].dir) || "ltr";
  $$("[data-i18n]").forEach(el => { el.textContent = t(el.getAttribute("data-i18n")); });
  $$("[data-i18n-html]").forEach(el => { el.innerHTML = t(el.getAttribute("data-i18n-html")); });
  MSGS = [t("am1"), t("am2"), t("am3"), t("am4"), t("am5")];
  if (!recwrap.classList.contains("recording")) $("#timer").textContent = t("tap");
  if (lastResult && current === "results") renderResults(lastResult, lastResult._isExample);
}

(async function initLang() {
  try { PASSAGES = await (await fetch("/static/passages.json")).json(); } catch (e) { /* keep fallback */ }
  try { T = await (await fetch("/static/i18n.json")).json(); } catch (e) { /* english inline fallback */ }
  const sel = $("#langSel");
  sel.innerHTML = Object.entries(PASSAGES).map(([k, v]) => `<option value="${k}">${v.name}</option>`).join("");
  const nav = (navigator.language || "en").slice(0, 2);
  currentLang = PASSAGES[nav] ? nav : "en"; sel.value = currentLang;
  sel.addEventListener("change", () => { currentLang = sel.value; renderPassage(); applyLang(); });
  renderPassage(); applyLang();
})();

function renderPassage() {
  const p = PASSAGES[currentLang];
  const prompt = $("#prompt"); prompt.dir = p.dir || "ltr"; prompt.textContent = p.text;
}

micBtn.addEventListener("click", async () => {
  if (recwrap.classList.contains("recording")) return stopRec();
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
  } catch (err) { return toast(t("toastMic")); }
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const src = audioCtx.createMediaStreamSource(stream);
  analyser = audioCtx.createAnalyser(); analyser.fftSize = 512; src.connect(analyser); drawMeter();
  chunks = []; mediaRec = new MediaRecorder(stream);
  mediaRec.ondataavailable = e => e.data.size && chunks.push(e.data);
  mediaRec.onstop = finishRec; mediaRec.start();
  recwrap.classList.add("recording");
  seconds = 0; $("#timer").textContent = "0.0s · listening…";
  timerInt = setInterval(() => {
    seconds += 0.1;
    const hint = seconds < 30 ? "keep reading… (aim for ~30s)" : "great, tap to stop when done";
    $("#timer").textContent = seconds.toFixed(1) + "s · " + hint;
    if (seconds >= 60) stopRec();   // safety auto-stop
  }, 100);
  $("#playback").classList.add("hidden"); $("#analyzeBtn").disabled = true;
});
function drawMeter() {
  const bars = $$("#meter i"), data = new Uint8Array(analyser.frequencyBinCount);
  (function loop() {
    analyser.getByteFrequencyData(data);
    bars.forEach((b, i) => { b.style.height = 6 + ((data[i * 2] || 0) / 255) * 30 + "px"; });
    meterRAF = requestAnimationFrame(loop);
  })();
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
  if (seconds < 15) toast(t("toastShort"));
  $("#analyzeBtn").disabled = false;
}
function purgeRecording() {
  // Privacy: drop the recorded audio and revoke its blob URL so it is no longer
  // accessible (called the moment results are shown, and on recorder reset).
  wavBlob = null;
  const pb = $("#playback");
  if (pb.getAttribute("src")) { try { URL.revokeObjectURL(pb.src); } catch (e) {} pb.removeAttribute("src"); try { pb.load(); } catch (e) {} }
  pb.classList.add("hidden");
  $("#analyzeBtn").disabled = true;
}
function resetRecorder() { purgeRecording(); $("#timer").textContent = t("tap"); }

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
let MSGS = ["Listening to your voice…", "Measuring your pitch", "Reading your rhythm", "Checking voice clarity", "Almost there…"];
let msgInt;
async function analyze() {
  if (!wavBlob) return toast(t("toastRecordFirst"));
  go("analyzing"); cycleMsgs();
  const fd = new FormData(); fd.append("audio", wavBlob, "rec.wav"); const t0 = Date.now();
  try {
    const r = await fetch("/api/screen", { method: "POST", body: fd });
    const res = await r.json();
    if (!res.ok) throw new Error(res.error || res.detail || "analysis failed");
    await minWait(t0); stopMsgs(); renderResults(res); go("results"); purgeRecording();
  } catch (e) { stopMsgs(); toast(t("toastAnalyzeFail") + " " + netMsg(e)); go("record"); }
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
  } catch (e) { stopMsgs(); toast(t("toastExampleFail") + " " + netMsg(e)); go("record"); }
});

/* ---------- results ---------- */
const FAM_ICON = { pitch: "i-mark", jitter: "i-mark", shimmer: "i-mark", hnr: "i-mark",
  loudness: "i-chart", rhythm: "i-chart", spectral: "i-chart", articulation: "i-cpu", other: "i-chart" };
const FICON = f => FAM_ICON[f] || "i-chart";
const BAND_SFX = { low: "Low", moderate: "Mod", elevated: "Elev" };
const BAND_COLOR = { low: "#17b8a6", moderate: "#6c5ce7", elevated: "#f2775f" };
const BAND_VCOLOR = { low: "#0e8a7c", moderate: "#5b4fd0", elevated: "#d1543b" };
const FAM_KEY = f => "fam" + f.charAt(0).toUpperCase() + f.slice(1);
const REP_KEY = {
  "F0semitoneFrom27.5Hz_sma3nz_stddevNorm": "repPitch", "jitterLocal_sma3nz_amean": "repJitter",
  "shimmerLocaldB_sma3nz_amean": "repShimmer", "HNRdBACF_sma3nz_amean": "repHnr",
  "loudness_sma3_amean": "repLoudness", "VoicedSegmentsPerSec": "repVoiced"
};
function icon(id) { return `<svg class="ic"><use href="#${id}"/></svg>`; }
function famLabel(f) { return t(FAM_KEY(f.family)); }
function narrativeFor(res) {
  const pct = Math.round(res.probability_pd * 100);
  const conf = res.confidence != null && res.confidence < 0.66 ? t("narrConfLow") : t("narrConfHigh");
  return t("narr" + BAND_SFX[res.risk_band], { pct }) + " " + conf + " " + t("narrTail");
}
function renderResults(res, isExample) {
  lastResult = res; res._isExample = isExample;
  const pct = Math.round(res.probability_pd * 100), band = res.risk_band, sfx = BAND_SFX[band] || "Low";
  $("#resTitle").textContent = t(isExample ? "resTitleEx" : "resTitle");
  const fill = $("#gFill"); fill.style.stroke = BAND_COLOR[band] || BAND_COLOR.low; fill.style.strokeDashoffset = 515;
  requestAnimationFrame(() => setTimeout(() => { fill.style.strokeDashoffset = 515 * (1 - pct / 100); }, 60));
  countUp($("#gPct"), pct);
  $("#verdict").textContent = t("band" + sfx + "T") + ". " + t("band" + sfx + "X");
  $("#verdict").style.color = BAND_VCOLOR[band] || BAND_VCOLOR.low;
  $("#narrative").textContent = narrativeFor(res);
  const cc = $("#confChip");
  if (res.confidence != null) {
    const c = res.confidence, lvl = c >= 0.66 ? ["confHigh", "#0e8a7c", "i-check"] : c >= 0.4 ? ["confMed", "#c98a52", "i-search"] : ["confLow", "#d1543b", "i-search"];
    cc.hidden = false; cc.className = "confchip"; cc.style.color = lvl[1];
    cc.innerHTML = icon(lvl[2]) + t("confPrefix") + " " + t(lvl[0]) + " · " + t("confWindows", { n: res.n_windows || "" });
  } else { cc.hidden = true; }
  const maxS = Math.max(...res.top_factors.map(f => Math.abs(f.shap))) || 1;
  $("#factors").innerHTML = res.top_factors.map((f, i) => {
    const pd = f.shap > 0, w = Math.round(Math.abs(f.shap) / maxS * 100);
    return `<div class="factor" style="--d:${0.14 * i + 0.2}s">
      <div class="frow"><span class="fname">${icon(FICON(f.family))}${famLabel(f)}</span>
      <span class="tag2 ${pd ? "pd" : "hc"}">${icon(pd ? "i-up" : "i-down")}${t(pd ? "tagPd" : "tagHc")}</span></div>
      <div class="bar"><i class="${pd ? "pd" : "hc"}" data-w="${w}"></i></div></div>`;
  }).join("");
  setTimeout(() => $$("#factors .bar i").forEach(i => i.style.width = i.dataset.w + "%"), 400);
  $("#report").innerHTML = res.acoustic_report.map(s => `<div class="stat"><div class="sv">${fmtVal(s.value)}</div><div class="sl">${t(REP_KEY[s.key] || s.key)}</div></div>`).join("");
  $("#resDisclaimer").textContent = t("disclaimer");
  if (band === "low") confetti();
}
function fmtVal(v) { return Math.abs(v) >= 100 ? Math.round(v) : (Math.abs(v) >= 1 ? v.toFixed(2) : v.toFixed(3)); }
function countUp(el, target) { let n = 0; const step = Math.max(1, Math.round(target / 28)); const id = setInterval(() => { n += step; if (n >= target) { n = target; clearInterval(id); } el.innerHTML = n + "<span>%</span>"; }, 40); }
function confetti() {
  const box = $("#confetti"); box.innerHTML = ""; const cols = ["#6c5ce7", "#17b8a6", "#8b7ff0"];
  for (let i = 0; i < 46; i++) { const c = document.createElement("i"); c.style.left = Math.random() * 100 + "%"; c.style.background = cols[i % cols.length]; c.style.animationDuration = 2 + Math.random() * 2 + "s"; c.style.animationDelay = Math.random() * .6 + "s"; box.appendChild(c); }
  setTimeout(() => box.innerHTML = "", 4200);
}

/* ---------- PDF (browser print -> renders every script/language) ---------- */
function esc(s) { return String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }
$("#pdfBtn").addEventListener("click", (e) => {
  const res = lastResult; if (!res) return toast(t("toastRecordFirst"));
  ripple(e, e.currentTarget);
  const pct = Math.round(res.probability_pd * 100), band = res.risk_band, sfx = BAND_SFX[band] || "Low";
  const dir = (PASSAGES[currentLang] && PASSAGES[currentLang].dir) || "ltr";
  const maxS = Math.max(...res.top_factors.map(f => Math.abs(f.shap))) || 1;
  const factors = res.top_factors.map(f => {
    const pd = f.shap > 0;
    return `<tr><td>${esc(famLabel(f))}</td><td style="color:${pd ? "#c0392b" : "#1a8a5a"}">${t(pd ? "tagPd" : "tagHc")}</td>
      <td>${Math.round(Math.abs(f.shap) / maxS * 100)}%</td></tr>`;
  }).join("");
  const measures = res.acoustic_report.map(s => `<tr><td>${esc(t(REP_KEY[s.key] || s.key))}</td><td><b>${fmtVal(s.value)}</b></td></tr>`).join("");
  const bc = { low: "#1a8a5a", moderate: "#b8860b", elevated: "#c0392b" }[band] || "#1f2a44";
  const html = `<!doctype html><html dir="${dir}"><head><meta charset="utf-8"><title>Cadence Report</title>
  <style>
    body{font-family:'Segoe UI',system-ui,'Noto Sans',sans-serif;color:#1f2a44;margin:36px;line-height:1.5}
    .hd{background:#1f2a44;color:#fff;padding:12px 16px;border-radius:6px;font-weight:700;font-size:18px}
    h3{border-bottom:1px solid #d2d6e0;padding-bottom:4px;margin:22px 0 8px;font-size:14px;color:#1f2a44}
    .big{font-size:40px;font-weight:800;color:${bc}}
    .muted{color:#5a6070;font-size:13px} table{width:100%;border-collapse:collapse;font-size:13px}
    td{padding:4px 2px;border-bottom:1px solid #eee} .bar{height:6px;background:#eee;border-radius:4px;margin:6px 0 14px}
    .bar>i{display:block;height:100%;background:${bc};border-radius:4px;width:${pct}%}
    .disc{color:#c0392b;font-weight:600;font-size:12px;margin-top:6px}
    @media print{@page{margin:14mm}}
  </style></head><body>
    <div class="hd">${t("pdfHeader")}</div>
    <p class="muted">${t("pdfGenerated")}: ${new Date().toLocaleString()}</p>
    <h3>${t("pdfResult")}</h3>
    <div class="big">${pct}%</div>
    <div class="muted">${t("indicator")} · ${t("pdfBand")}: <b style="color:${bc}">${t("band" + sfx + "T")}</b></div>
    <div class="bar"><i></i></div>
    <h3>${t("pdfSummary")}</h3><p>${esc(narrativeFor(res))}</p>
    <h3>${t("told")}</h3><table>${factors}</table>
    <h3>${t("card")}</h3><table>${measures}</table>
    <h3>${t("pdfMethod")}</h3><p class="disc">${esc(t("disclaimer"))}</p>
    <p class="muted">github.com/ahammadshawki8/CADENCE</p>
    <script>window.onload=function(){setTimeout(function(){window.print();},250);}<\/script>
  </body></html>`;
  const w = window.open("", "_blank");
  if (!w) return toast(t("toastPdfFail"));
  w.document.open(); w.document.write(html); w.document.close();
});
