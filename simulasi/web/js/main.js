import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { Sky } from 'three/addons/objects/Sky.js';
import { buildCommon, buildScenario, setTerrain, sampleTerrain, updateLights, toV } from './world.js';
import { Traffic } from './vehicles.js';
import { Driver } from './drive.js';

const $ = id => document.getElementById(id);
const showErr = (msg) => { const l = $('loading'); l.style.display = 'grid'; l.innerHTML = `<div style="max-width:800px;color:#ffb4b4;white-space:pre-wrap">Terjadi kesalahan:
${msg}</div>`; };
addEventListener('error', e => showErr(`${e.message}
${e.filename}:${e.lineno}`));
addEventListener('unhandledrejection', e => showErr(String(e.reason && (e.reason.stack || e.reason))));
const DESC = {
  S0: 'Kondisi sekarang: median pagar stainless baru. Dari Lembang ke Gerlong harus putar balik di bukaan A (±35 m selatan mulut Gerlong) lalu belok kiri. Dari bawah putar balik di bukaan B (dekat gerbang UPI). Truk/bus maju-mundur saat putar balik; angkot ngetem di sudut Gerlong.',
  S0_tahap1: 'Solusi murah (tanpa konstruksi): truk & bus dilarang putar balik di sini, angkot dilarang ngetem di mulut Gerlong. Geometri sama dengan S0.',
  S1: 'Median dibuka di mulut Gerlong + APILL 2 fase adaptif: fase khusus belok kanan dari Lembang ke Gerlong (5–14 s, menyesuaikan antrean). Lajur kanan arah turun 60 m jadi lajur khusus belok kanan. Bukaan A ditutup; bukaan B tetap untuk kendaraan kecil. Tertib ngetem.',
  S2: 'U-turn layang (putar balik layang) 480 m: naik dari lajur median arah turun di dekat UPI, loop R 13 m di ±200 m selatan, mendarat di lajur arah naik 70 m sebelum Gerlong → belok kiri. Butuh pelebaran jalan & pembebasan lahan di zona loop. Bukaan A ditutup, B dipindah ke utara.',
};
const CAMS = {
  'Ikhtisar': { pos: [170, -170, 150], target: [0, -30, 0] },
  'Bukaan A': { pos: [32, -112, 22], target: [-6, -67, -1.6] },
  'Mulut Gerlong': { pos: [38, 8, 20], target: [-8, -33, 0] },
  'Bukaan B': { pos: [60, 30, 26], target: [20, 72, 5] },
  'Flyover (S2)': { pos: [95, -300, 48], target: [-22, -160, 0] },
  'Pejalan kaki': { pos: [-18, -27, 1.7], target: [12, -55, 0] },
};

// ------------------------------------------------------------------ renderer & adegan
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 0.55;
$('view').appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xc9d6e0, 350, 1100);
const camera = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.3, 4000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.maxPolarAngle = Math.PI * 0.495;

const sky = new Sky(); sky.scale.setScalar(4000); scene.add(sky);
const sun = new THREE.Vector3().setFromSphericalCoords(1, THREE.MathUtils.degToRad(50), THREE.MathUtils.degToRad(140));
Object.assign(sky.material.uniforms, {}); sky.material.uniforms.sunPosition.value.copy(sun);
sky.material.uniforms.turbidity.value = 6; sky.material.uniforms.rayleigh.value = 1.4;
scene.add(new THREE.HemisphereLight(0xdfe9f3, 0x6b6450, 1.25));
const dl = new THREE.DirectionalLight(0xfff3e0, 2.4);
dl.position.copy(sun).multiplyScalar(300); dl.castShadow = true;
dl.shadow.mapSize.set(2048, 2048);
Object.assign(dl.shadow.camera, { left: -120, right: 120, top: 120, bottom: -120, near: 10, far: 900 });
dl.shadow.bias = -0.0004;
scene.add(dl, dl.target);

function setCam(name) {
  const c = CAMS[name]; if (!c) return;
  const z = (p) => p[2] + sampleTerrain(p[0], p[1]);
  camera.position.copy(toV(c.pos[0], c.pos[1], z(c.pos)));
  controls.target.copy(toV(c.target[0], c.target[1], z(c.target)));
  controls.update();
}

// ------------------------------------------------------------------ data
let common = null, scen = null, scenKey = null;
const traffic = new Traffic(scene);
const driver = new Driver(scene, camera);
driver.onCrash = () => flash('Tabrakan! Hati-hati.');

async function loadJSON(u) { const r = await fetch(u); return r.json(); }
async function loadScenario(key) {
  const base = key.split('_')[0];
  if (scen && scenKey === base) return;
  const data = await loadJSON(`data/scene_${base}.json`);
  if (scen) { scene.remove(scen.group); scen.group.traverse(o => { if (o.geometry) o.geometry.dispose(); }); }
  scen = buildScenario(data, scene); scenKey = base;
}
async function init() {
  const t0 = performance.now(), lap = (m) => console.log(`[muat] ${m}: ${Math.round(performance.now() - t0)} ms`);
  common = await loadJSON('data/common.json'); lap('common.json');
  setTerrain(common.terrain);
  buildCommon(common, scene); lap('dunia bersama');
  await loadScenario('S0'); lap('skenario');
  setCam(new URLSearchParams(location.search).get('kamera') || 'Ikhtisar');
  $('loading').style.display = 'none';
  const cams = $('cams');
  for (const n of Object.keys(CAMS)) { const b = document.createElement('button'); b.textContent = n; b.onclick = () => { driver.camMode = 0; setCam(n); }; cams.appendChild(b); }
  connect();
}

// ------------------------------------------------------------------ WebSocket
let ws = null, simTime = 0;
function send(o) { if (ws && ws.readyState === 1) ws.send(JSON.stringify(o)); }
function connect() {
  ws = new WebSocket(`ws://${location.hostname || '127.0.0.1'}:8765`);
  ws.onopen = () => { $('conn').textContent = '● terhubung ke SUMO'; $('conn').style.color = '#2fb67c'; };
  ws.onclose = () => { $('conn').textContent = '○ terputus — jalankan: python bridge/server.py'; $('conn').style.color = '#e34948'; setTimeout(connect, 2000); };
  ws.onmessage = async ev => {
    const m = JSON.parse(ev.data);
    if (m.type === 'hello') {
      const sel = $('scen'); sel.innerHTML = '';
      for (const [k, l] of Object.entries(m.scenarios)) { const o = document.createElement('option'); o.value = k; o.textContent = l; sel.appendChild(o); }
      const qs = new URLSearchParams(location.search);
      if (qs.get('mulai') && m.scenarios[qs.get('mulai')]) {
        sel.value = qs.get('mulai');
        send({ cmd: 'start', scenario: sel.value, scale: +(qs.get('kepadatan') || 1), seed: 7 });
        if (qs.get('cepat')) { $('speed').value = qs.get('cepat'); }
      }
      $('desc').textContent = DESC[sel.value];
    } else if (m.type === 'started') {
      traffic.clear(); driver.stop(); $('hud').style.display = 'none';
      await loadScenario(m.scenario);
      $('desc').textContent = DESC[m.scenario];
      send({ cmd: 'speed', value: +$('speed').value });
    } else if (m.type === 'frame') {
      simTime = m.t; traffic.onFrame(m);
      if (scen && m.tl) updateLights(scen.lights, m.tl);
      if (m.ego) egoInfo = m.ego;
    } else if (m.type === 'stats') {
      const mm = Math.floor(m.t / 60), ss = Math.floor(m.t % 60);
      $('sTime').textContent = `${mm}:${String(ss).padStart(2, '0')}`;
      $('sN').textContent = m.n; $('sPend').textContent = m.pending; $('sV').textContent = `${m.vmean} km/jam`;
      for (const [k, el, bar] of [['turun', 'qT', 'bT'], ['naik', 'qN', 'bN'], ['gerlong', 'qG', 'bG']]) {
        const v = m.q[k]; $(el).textContent = `${Math.round(v)} m`;
        $(bar).style.width = `${Math.min(100, v / 6)}%`;
        $(bar).style.background = v > 300 ? '#e34948' : v > 120 ? '#eda100' : '#2fb67c';
      }
    } else if (m.type === 'ego_spawned') {
      driver.start(m.vtype, m.pose, [...scen.drivable, ...scene.children.filter(o => o.name === 'common').flatMap(g => g.children.filter(c => c.name === 'terrain' || c.name === 'ctxroads'))]);
      controls.enabled = false; $('hud').style.display = 'block';
    } else if (m.type === 'error') {
      flash('Simulator: ' + m.msg);
    } else if (m.type === 'ego_gone') {
      if (driver.active) flash(`Kendaraan Anda ${m.reason}.`);
      driver.stop(); controls.enabled = true; $('hud').style.display = 'none';
    }
  };
}
let egoInfo = null;

// ------------------------------------------------------------------ UI
$('scen').onchange = () => { $('desc').textContent = DESC[$('scen').value]; };
$('scale').oninput = () => { $('scaleVal').textContent = `${Math.round($('scale').value * 100)}%`; };
$('btnStart').onclick = () => send({ cmd: 'start', scenario: $('scen').value, scale: +$('scale').value, seed: Math.floor(Math.random() * 1000) });
let paused = false;
$('btnPause').onclick = () => { paused = !paused; send({ cmd: 'pause', value: paused }); $('btnPause').textContent = paused ? '▶ Lanjut' : '⏸ Jeda'; };
$('speed').onchange = () => send({ cmd: 'speed', value: +$('speed').value });
$('btnDrive').onclick = () => {
  if (!traffic.v.size && !simTime) { flash('Mulai simulasi dulu (▶ Mulai).'); return; }
  $('speed').value = '1'; send({ cmd: 'speed', value: 1 });
  send({ cmd: 'ego_spawn', vtype: $('egoType').value, at: $('egoAt').value });
};
$('btnStopDrive').onclick = () => { send({ cmd: 'ego_remove' }); driver.stop(); controls.enabled = true; $('hud').style.display = 'none'; };
let flashT = null;
function flash(t) { const a = $('alert'); a.textContent = t; a.style.display = 'block'; clearTimeout(flashT); flashT = setTimeout(() => a.style.display = 'none', 2200); }

const EDGE_NAME = (e) => {
  if (!e) return '';
  if (e.startsWith(':A')) return 'di bukaan A'; if (e.startsWith(':G')) return 'di mulut Gerlong'; if (e.startsWith(':B')) return 'di bukaan B';
  if (e === 'FO') return 'di atas U-turn layang'; if (e.startsWith('GER')) return 'Jl. Gegerkalong Girang';
  if (e.startsWith('KAH')) return 'Jl. Kapten Abdul Hamid';
  if (e.startsWith('SB')) return 'Setiabudi arah turun'; if (e.startsWith('NB')) return 'Setiabudi arah naik';
  return e;
};

// ------------------------------------------------------------------ loop
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
const clock = new THREE.Clock();
let sendAcc = 0;
function loop() {
  requestAnimationFrame(loop);
  const dt = Math.min(0.05, clock.getDelta());
  traffic.update();
  if (driver.active) {
    const pose = driver.update(dt, traffic.list);
    sendAcc += dt;
    if (pose && sendAcc > 0.05) { sendAcc = 0; send({ cmd: 'ego', ...pose }); }
    $('hudV').textContent = Math.round(Math.abs(driver.v) * 3.6);
    const g = (driver.grade || 0) * 100;
    $('hudInfo').innerHTML = `${EDGE_NAME(egoInfo?.edge)} · kemiringan ${g >= 0 ? '+' : ''}${g.toFixed(1)}%` +
      (egoInfo?.wait > 3 ? ` · menunggu ${Math.round(egoInfo.wait)} s` : '') +
      `<br>W/↑ gas · S/↓ rem · A D setir · Spasi rem tangan · C kamera`;
    dl.target.position.set(driver.x, driver.z || 0, -driver.y);
  } else {
    controls.update();
    dl.target.position.copy(controls.target);
  }
  dl.position.copy(dl.target.position).addScaledVector(sun, 300);
  renderer.render(scene, camera);
}
init().then(loop).catch(e => showErr(e.stack || e));
