// Pembangun dunia 3D statis dari JSON ekspor (common.json + scene_<S>.json).
// Koordinat data: x timur, y utara, z naik  →  Three.js: (x, z, -y).
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export const toV = (x, y, z) => new THREE.Vector3(x, z, -y);

// ------------------------------------------------------------------ material
const M = {
  asphalt: new THREE.MeshStandardMaterial({ color: 0x3a3c3f, roughness: 0.96, metalness: 0, side: THREE.DoubleSide }),
  asphaltJ: new THREE.MeshStandardMaterial({ color: 0x37393c, roughness: 0.96, side: THREE.DoubleSide,
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 }),
  ctxRoad: new THREE.MeshStandardMaterial({ color: 0x5a5c5f, roughness: 0.95, side: THREE.DoubleSide }),
  white: new THREE.MeshBasicMaterial({ color: 0xe9e9e4, side: THREE.DoubleSide }),
  yellow: new THREE.MeshBasicMaterial({ color: 0xe8b81c, side: THREE.DoubleSide }),
  sidewalk: new THREE.MeshStandardMaterial({ color: 0xa8a399, roughness: 0.9, side: THREE.DoubleSide }),
  terrain: new THREE.MeshLambertMaterial({ vertexColors: true }),
  building: new THREE.MeshLambertMaterial({ vertexColors: true }),
  grass: new THREE.MeshLambertMaterial({ color: 0x7f9a55, side: THREE.DoubleSide }),
  wood: new THREE.MeshLambertMaterial({ color: 0x5f7f3e, side: THREE.DoubleSide }),
  trunk: new THREE.MeshLambertMaterial({ color: 0x5b4632 }),
  crown: new THREE.MeshLambertMaterial({ color: 0x4f7a35 }),
  steel: new THREE.MeshStandardMaterial({ color: 0xd9dde0, metalness: 0.85, roughness: 0.28 }),
  pole: new THREE.MeshStandardMaterial({ color: 0x8e9398, metalness: 0.6, roughness: 0.4 }),
  concrete: new THREE.MeshStandardMaterial({ color: 0xb9b6ae, roughness: 0.85 }),
  concreteDark: new THREE.MeshStandardMaterial({ color: 0x9c9890, roughness: 0.9 }),
  yellowPaint: new THREE.MeshStandardMaterial({ color: 0xe9c11e, roughness: 0.7 }),
};

// ------------------------------------------------------------------ geometri bantu
function dir2(p, q) { const dx = q[0] - p[0], dy = q[1] - p[1]; const L = Math.hypot(dx, dy) || 1; return [dx / L, dy / L]; }

/** Pita (ribbon) sepanjang polyline. off>0 = geser ke KIRI arah gerak. */
export function ribbon(pts, w, off = 0, dz = 0) {
  const n = pts.length, pos = [], uv = [], idx = [];
  let acc = 0;
  for (let i = 0; i < n; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
    const [dx, dy] = dir2(a, b);
    const lx = -dy, ly = dx;
    const p = pts[i];
    if (i > 0) acc += Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]);
    const cx = p[0] + lx * off, cy = p[1] + ly * off, z = (p[2] || 0) + dz;
    pos.push(cx + lx * w / 2, z, -(cy + ly * w / 2), cx - lx * w / 2, z, -(cy - ly * w / 2));
    uv.push(0, acc, 1, acc);
  }
  for (let i = 0; i < n - 1; i++) { const k = 2 * i; idx.push(k, k + 1, k + 2, k + 1, k + 3, k + 2); }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

/** Sapuan penampang persegi (lebar w, z dari zb..zt relatif polyline) — untuk kanstin, gelagar, dinding. */
function sweepBox(pts, w, zb, zt, off = 0) {
  const n = pts.length, pos = [], idx = [], uv = [];
  let acc = 0;
  for (let i = 0; i < n; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
    const [dx, dy] = dir2(a, b);
    const lx = -dy, ly = dx, p = pts[i];
    if (i > 0) acc += Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]);
    const cx = p[0] + lx * off, cy = p[1] + ly * off, z = p[2] || 0;
    const L = [cx + lx * w / 2, cy + ly * w / 2], R = [cx - lx * w / 2, cy - ly * w / 2];
    const zb_ = Array.isArray(zb) ? zb[i] : z + zb, zt_ = z + zt;
    // 4 sudut: Lb, Lt, Rt, Rb
    pos.push(L[0], zb_, -L[1], L[0], zt_, -L[1], R[0], zt_, -R[1], R[0], zb_, -R[1]);
    uv.push(0, acc, 0.33, acc, 0.66, acc, 1, acc);
  }
  for (let i = 0; i < n - 1; i++) {
    const k = 4 * i, m = k + 4;
    // sisi kiri, atas, kanan
    idx.push(k, m, k + 1, k + 1, m, m + 1);
    idx.push(k + 1, m + 1, k + 2, k + 2, m + 1, m + 2);
    idx.push(k + 2, m + 2, k + 3, k + 3, m + 2, m + 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

function pointAt(pts, s) {
  let acc = 0;
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i], b = pts[i + 1], d = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (acc + d >= s) {
      const t = d ? (s - acc) / d : 0;
      return [a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), (a[2] || 0) + t * ((b[2] || 0) - (a[2] || 0))];
    }
    acc += d;
  }
  return pts[pts.length - 1];
}
function plLength(pts) { let L = 0; for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return L; }
function subPl(pts, s0, s1, step = 1.5) {
  const out = []; for (let s = s0; s < s1; s += step) out.push(pointAt(pts, s)); out.push(pointAt(pts, s1)); return out;
}

/** Garis putus-putus (dash 3 m, celah 5 m — marka lajur Indonesia). */
function dashed(pts, w, off, dz, dash = 3, gap = 5) {
  const L = plLength(pts), geos = [];
  for (let s = 1; s + 0.5 < L; s += dash + gap) geos.push(ribbon(subPl(pts, s, Math.min(L, s + dash), 1.0), w, off, dz));
  return geos.length ? mergeGeometries(geos) : null;
}

function polygonGeo(pts3, dz = 0) {
  const contour = pts3.map(p => new THREE.Vector2(p[0], p[1]));
  if (THREE.ShapeUtils.isClockWise(contour)) { contour.reverse(); pts3 = [...pts3].reverse(); }
  const tris = THREE.ShapeUtils.triangulateShape(contour, []);
  const pos = [];
  for (const p of pts3) pos.push(p[0], (p[2] || 0) + dz, -p[1]);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(tris.flat());
  g.computeVertexNormals();
  return g;
}

export function textTexture(text, { w = 512, h = 256, bg = '#1f6b4a', fg = '#ffffff', font = 'bold 64px system-ui', border = null } = {}) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d');
  g.fillStyle = bg; g.fillRect(0, 0, w, h);
  if (border) { g.strokeStyle = border; g.lineWidth = 10; g.strokeRect(8, 8, w - 16, h - 16); }
  g.fillStyle = fg; g.font = font; g.textAlign = 'center'; g.textBaseline = 'middle';
  const lines = String(text).split('\n');
  const lh = parseInt(font.match(/(\d+)px/)[1]) * 1.15;
  lines.forEach((ln, i) => g.fillText(ln, w / 2, h / 2 + (i - (lines.length - 1) / 2) * lh, w - 30));
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return t;
}

function stripeTexture() {
  const c = document.createElement('canvas'); c.width = 64; c.height = 64;
  const g = c.getContext('2d');
  g.fillStyle = '#f2f2f0'; g.fillRect(0, 0, 64, 32); g.fillStyle = '#1b1b1b'; g.fillRect(0, 32, 64, 32);
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function uturnTexture(kind) {
  const c = document.createElement('canvas'); c.width = 256; c.height = 256;
  const g = c.getContext('2d');
  if (kind === 'uturn' || kind === 'keep' || kind === 'flyover') {
    g.fillStyle = '#1452a8'; g.fillRect(0, 0, 256, 256);
    g.strokeStyle = '#fff'; g.lineWidth = 26; g.lineCap = 'round';
    if (kind === 'uturn') {
      g.beginPath(); g.moveTo(80, 215); g.lineTo(80, 110); g.arc(128, 110, 48, Math.PI, 0); g.lineTo(176, 160); g.stroke();
      g.fillStyle = '#fff'; g.beginPath(); g.moveTo(140, 150); g.lineTo(212, 150); g.lineTo(176, 210); g.fill();
    } else if (kind === 'keep') {
      g.beginPath(); g.moveTo(170, 60); g.lineTo(90, 200); g.stroke();
      g.fillStyle = '#fff'; g.beginPath(); g.moveTo(60, 200); g.lineTo(120, 210); g.lineTo(80, 150); g.fill();
    } else {
      g.fillStyle = '#1b7a3a'; g.fillRect(0, 0, 256, 256);
      g.fillStyle = '#fff'; g.font = 'bold 34px system-ui'; g.textAlign = 'center';
      g.fillText('PUTAR BALIK', 128, 80); g.fillText('& GERLONG', 128, 122); g.font = 'bold 70px system-ui'; g.fillText('↗', 128, 200);
    }
  } else { // nouturn
    g.fillStyle = '#fff'; g.fillRect(0, 0, 256, 256);
    g.strokeStyle = '#d0202a'; g.lineWidth = 24; g.beginPath(); g.arc(128, 128, 100, 0, Math.PI * 2); g.stroke();
    g.strokeStyle = '#111'; g.lineWidth = 18; g.beginPath(); g.moveTo(100, 190); g.lineTo(100, 120); g.arc(128, 120, 28, Math.PI, 0); g.lineTo(156, 150); g.stroke();
    g.strokeStyle = '#d0202a'; g.lineWidth = 22; g.beginPath(); g.moveTo(58, 58); g.lineTo(198, 198); g.stroke();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

function arrowTexture() {
  const c = document.createElement('canvas'); c.width = 128; c.height = 256;
  const g = c.getContext('2d');
  g.clearRect(0, 0, 128, 256); g.strokeStyle = '#eee'; g.fillStyle = '#eee'; g.lineWidth = 16;
  g.beginPath(); g.moveTo(40, 250); g.lineTo(40, 110); g.quadraticCurveTo(40, 70, 80, 70); g.stroke();
  g.beginPath(); g.moveTo(78, 40); g.lineTo(120, 70); g.lineTo(78, 100); g.fill();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

// ------------------------------------------------------------------ dunia bersama
export function buildCommon(data, scene) {
  const grp = new THREE.Group(); grp.name = 'common';
  // tanah
  const T = data.terrain, pos = [], col = [], idx = [];
  const base = new THREE.Color(0x98a377), alt = new THREE.Color(0x8c9a6c);
  for (let j = 0; j < T.ny; j++) for (let i = 0; i < T.nx; i++) {
    const x = T.x0 + i * T.step, y = T.y0 + j * T.step;
    pos.push(x, T.z[j][i], -y);
    const c = base.clone().lerp(alt, (Math.sin(x * 0.07) + Math.cos(y * 0.05)) * 0.25 + 0.5);
    col.push(c.r, c.g, c.b);
  }
  for (let j = 0; j < T.ny - 1; j++) for (let i = 0; i < T.nx - 1; i++) {
    const a = j * T.nx + i, b = a + 1, c = a + T.nx, d = c + 1;
    idx.push(a, b, c, b, d, c);
  }
  const tg = new THREE.BufferGeometry();
  tg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  tg.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  tg.setIndex(idx); tg.computeVertexNormals();
  const terrain = new THREE.Mesh(tg, M.terrain); terrain.receiveShadow = true; terrain.name = 'terrain';
  grp.add(terrain);

  // area hijau
  const gg = [], gw = [];
  for (const g of data.greens) { try { (g.k === 'wood' ? gw : gg).push(polygonGeo(g.p, 0.1)); } catch (e) { /* poligon rusak */ } }
  if (gg.length) grp.add(new THREE.Mesh(mergeGeometries(gg), M.grass));
  if (gw.length) grp.add(new THREE.Mesh(mergeGeometries(gw), M.wood));

  // jalan konteks
  const rg = data.roads.map(r => ribbon(r.p, r.w, 0, 0));
  if (rg.length) { const m = new THREE.Mesh(mergeGeometries(rg), M.ctxRoad); m.receiveShadow = true; m.name = 'ctxroads'; grp.add(m); }

  // gedung
  const bgeos = [];
  const cW = new THREE.Color(), cR = new THREE.Color();
  for (const b of data.buildings) {
    const shape = new THREE.Shape(b.p.map(p => new THREE.Vector2(p[0], p[1])));
    let g;
    try { g = new THREE.ExtrudeGeometry(shape, { depth: b.h, bevelEnabled: false }); } catch (e) { continue; }
    g.rotateX(-Math.PI / 2);
    g.translate(0, b.z, 0);
    cW.set(b.c); cR.set(b.r);
    const n = g.attributes.position.count, cols = new Float32Array(n * 3);
    const groups = g.groups;
    for (const gr of groups) {
      const c = gr.materialIndex === 0 ? cR : cW;
      const ix = g.index;
      for (let k = gr.start; k < gr.start + gr.count; k++) { const v = ix ? ix.getX(k) : k; cols[3 * v] = c.r; cols[3 * v + 1] = c.g; cols[3 * v + 2] = c.b; }
    }
    g.setAttribute('color', new THREE.BufferAttribute(cols, 3));
    g.clearGroups();
    bgeos.push(g.toNonIndexed ? g : g);
  }
  if (bgeos.length) {
    const bm = new THREE.Mesh(mergeGeometries(bgeos.map(g => g.index ? g.toNonIndexed() : g)), M.building);
    bm.castShadow = true; bm.receiveShadow = true; bm.name = 'buildings'; grp.add(bm);
  }

  // pohon
  const nT = data.trees.length;
  const trunkG = new THREE.CylinderGeometry(0.22, 0.32, 3.2, 6); trunkG.translate(0, 1.6, 0);
  const crownG = new THREE.IcosahedronGeometry(2.8, 1); crownG.translate(0, 4.6, 0);
  const trunks = new THREE.InstancedMesh(trunkG, M.trunk, nT), crowns = new THREE.InstancedMesh(crownG, M.crown, nT);
  const mtx = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), c = new THREE.Color();
  data.trees.forEach((t, i) => {
    s.set(t[3], t[3] * (0.9 + (i % 5) * 0.06), t[3]);
    mtx.compose(toV(t[0], t[1], t[2] - 0.2), q, s);
    trunks.setMatrixAt(i, mtx); crowns.setMatrixAt(i, mtx);
    crowns.setColorAt(i, c.setHSL(0.26 + (i % 7) * 0.012, 0.42, 0.28 + (i % 4) * 0.03));
  });
  crowns.castShadow = true; trunks.castShadow = true;
  grp.add(trunks, crowns);

  // landmark
  for (const lm of data.landmarks) grp.add(landmark(lm));
  scene.add(grp);
  return grp;
}

function facing(x) { return x < 0 ? Math.PI / 2 : -Math.PI / 2; } // sisi barat menghadap timur (ke jalan)

function landmark(lm) {
  const g = new THREE.Group();
  g.position.copy(toV(lm.x, lm.y, lm.z));
  g.rotation.y = facing(lm.x);
  const plate = (w, h, tex, y, z = 0.06) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.6, side: THREE.DoubleSide }));
    m.position.set(0, y, z); return m;
  };
  const poleM = (h, r = 0.12, x = 0) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 8), M.pole); m.position.set(x, h / 2, 0); m.castShadow = true; return m; };
  switch (lm.type) {
    case 'billboard': {
      g.add(poleM(lm.h, 0.35));
      const t = lm.text ? textTexture(lm.text, { bg: lm.color, font: 'bold 80px system-ui', w: 768, h: 384 }) : null;
      const m = new THREE.Mesh(new THREE.BoxGeometry(lm.w, lm.hh, 0.4),
        new THREE.MeshStandardMaterial({ color: lm.text ? 0xffffff : 0xd5d5d5, map: t, roughness: 0.7 }));
      m.position.set(0, lm.h + lm.hh / 2 - 0.5, 0); m.castShadow = true; g.add(m);
      break;
    }
    case 'sign_green':
      g.add(poleM(lm.h, 0.08, -0.9), poleM(lm.h, 0.08, 0.9));
      g.add(plate(2.4, 1.3, textTexture(lm.text, { bg: '#1d6e43', font: 'bold 44px system-ui', border: '#ffffff' }), lm.h - 0.2));
      break;
    case 'round_sign': {
      g.add(poleM(lm.h, 0.1));
      const m = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 1.1, 0.2, 24),
        new THREE.MeshStandardMaterial({ map: textTexture(lm.text, { bg: lm.color, w: 256, h: 256, font: 'bold 48px serif' }) }));
      m.rotation.x = Math.PI / 2; m.position.set(0, lm.h + 0.9, 0); g.add(m);
      break;
    }
    case 'booth': {
      const b = new THREE.Mesh(new THREE.BoxGeometry(2.6, 2.7, 2.4), new THREE.MeshStandardMaterial({ color: 0xf2f2f2 }));
      b.position.y = 1.35; b.castShadow = true; g.add(b);
      const r = new THREE.Mesh(new THREE.BoxGeometry(3, 0.25, 2.8), new THREE.MeshStandardMaterial({ color: 0x1e4f9a }));
      r.position.y = 2.8; g.add(r);
      g.add(plate(3.4, 0.9, textTexture(lm.text, { bg: '#1e4f9a', font: 'bold 46px system-ui', w: 768, h: 192 }), 3.4, 1.25));
      break;
    }
    case 'shop_sign':
      g.add(poleM(3.2, 0.06, -1.2), poleM(3.2, 0.06, 1.2));
      g.add(plate(3, 0.9, textTexture(lm.text, { bg: lm.color, font: 'bold 60px system-ui', w: 512, h: 160 }), 3.4));
      break;
    case 'halte':
      g.add(poleM(2.6, 0.08));
      g.add(plate(0.9, 1.4, textTexture('HALTE\n' + lm.text, { bg: '#1b55a3', font: 'bold 30px system-ui', w: 192, h: 300 }), 2.2));
      break;
    case 'gate': {
      for (const x of [-4, 4]) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.8, 4, 0.8), M.concrete); p.position.set(x, 2, 0); g.add(p); }
      g.add(plate(5, 1.4, textTexture(lm.text, { bg: '#ffffff', fg: '#d0202a', font: 'bold 120px system-ui', w: 512, h: 160 }), 3.3, 0.45));
      break;
    }
    case 'label': {
      const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: textTexture(lm.text, { bg: 'rgba(15,18,22,0.78)', font: 'bold 40px system-ui', w: 768, h: 96 }), depthTest: false }));
      sp.scale.set(26, 3.3, 1); sp.position.y = 9; sp.renderOrder = 10; g.add(sp);
      g.rotation.y = 0;
      break;
    }
  }
  return g;
}

// ------------------------------------------------------------------ adegan skenario
export function buildScenario(sc, scene) {
  const grp = new THREE.Group(); grp.name = 'scenario';
  const drivable = [];
  const laneGeos = [], internalGeos = [], whiteG = [], yellowG = [], sideG = [];
  for (const ln of sc.lanes) {
    const g = ribbon(ln.s, ln.w + 0.02, 0, 0.03);
    const m = new THREE.Mesh(g, M.asphalt); m.receiveShadow = true;
    m.userData.edge = ln.e; m.userData.lane = ln.i; grp.add(m); drivable.push(m);
    const isMain = ln.e.startsWith('NB_') || ln.e.startsWith('SB_');
    const isFO = ln.e === 'FO';
    // marka
    if (ln.i === 0) whiteG.push(ribbon(ln.s, 0.12, ln.w / 2 - 0.18, 0.05));            // garis tepi luar
    if (ln.n === 2 && ln.i === 0) { const d = dashed(ln.s, 0.12, -ln.w / 2, 0.05); if (d) whiteG.push(d); }
    if (isMain && ln.i === ln.n - 1) yellowG.push(ribbon(ln.s, 0.13, -ln.w / 2 + 0.2, 0.05)); // garis kuning sisi median
    if (isFO) { whiteG.push(ribbon(ln.s, 0.12, -ln.w / 2 + 0.25, 0.05)); }
    if (ln.e === 'GER_in' || ln.e === 'KAH_in') { const d = dashed(ln.s, 0.12, -ln.w / 2, 0.05, 2, 3); if (d) whiteG.push(d); }
    // isi celah median 0,8 m dengan aspal (pagar/kanstin digambar terpisah di atasnya)
    if (isMain && ln.e.startsWith('SB_') && ln.i === ln.n - 1) laneGeos.push(ribbon(ln.s, 0.9, -ln.w / 2 - 0.42, 0.028));
    // trotoar
    if (ln.i === 0 && !isFO) sideG.push(ribbon(ln.s, isMain ? 2.4 : 1.4, ln.w / 2 + (isMain ? 1.25 : 0.75), 0.18));
  }
  for (const ln of sc.internal) internalGeos.push(ribbon(ln.s, ln.w, 0, 0.025));
  const jg = [];
  for (const j of sc.junctions) { try { jg.push(polygonGeo(j.s, 0.022)); } catch (e) { /* */ } }
  if (laneGeos.length) { const m = new THREE.Mesh(mergeGeometries(laneGeos), M.asphalt); m.receiveShadow = true; grp.add(m); drivable.push(m); }
  if (internalGeos.length) { const m = new THREE.Mesh(mergeGeometries(internalGeos), M.asphaltJ); m.receiveShadow = true; grp.add(m); drivable.push(m); }
  if (jg.length) { const m = new THREE.Mesh(mergeGeometries(jg), M.asphaltJ); m.receiveShadow = true; grp.add(m); drivable.push(m); }
  if (whiteG.length) grp.add(new THREE.Mesh(mergeGeometries(whiteG), M.white));
  if (yellowG.length) grp.add(new THREE.Mesh(mergeGeometries(yellowG), M.yellow));
  if (sideG.length) { const m = new THREE.Mesh(mergeGeometries(sideG), M.sidewalk); m.receiveShadow = true; grp.add(m); }

  // median: kanstin hitam-putih + pagar stainless berjeruji
  const stripe = stripeTexture(); stripe.repeat.set(1, 1);
  const curbMat = new THREE.MeshStandardMaterial({ map: stripe, roughness: 0.8 });
  const fence = { posts: [], bars: [], rails: [] };
  for (const pl of sc.median) {
    const cg = sweepBox(pl, 0.8, -0.05, 0.25);
    const m = new THREE.Mesh(cg, curbMat); m.castShadow = true; m.receiveShadow = true; grp.add(m);
    // ujung kuning (nose)
    for (const end of [pl[0], pl[pl.length - 1]]) {
      const n = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.3, 14), M.yellowPaint);
      n.position.copy(toV(end[0], end[1], end[2] + 0.12)); grp.add(n);
    }
    const L = plLength(pl);
    for (let s = 0.3; s < L - 0.3; s += 0.14) {
      const p = pointAt(pl, s), q = pointAt(pl, Math.min(L, s + 0.5));
      const ang = Math.atan2(q[1] - p[1], q[0] - p[0]);
      (Math.abs((s % 2.5)) < 0.14 ? fence.posts : fence.bars).push([p, ang]);
    }
    for (let s = 0; s < L - 0.1; s += 2.5) {
      const p = pointAt(pl, s), q = pointAt(pl, Math.min(L, s + 2.5));
      fence.rails.push([p, q]);
    }
  }
  const mk = (geo, list, yoff) => {
    const im = new THREE.InstancedMesh(geo, M.steel, Math.max(1, list.length));
    const mtx = new THREE.Matrix4(), qq = new THREE.Quaternion(), one = new THREE.Vector3(1, 1, 1);
    list.forEach(([p, ang], i) => { qq.setFromAxisAngle(new THREE.Vector3(0, 1, 0), ang); mtx.compose(toV(p[0], p[1], p[2] + yoff), qq, one); im.setMatrixAt(i, mtx); });
    im.count = list.length; im.castShadow = true; return im;
  };
  const postG = new THREE.BoxGeometry(0.07, 1.25, 0.07); postG.translate(0, 0.62, 0);
  const barG = new THREE.CylinderGeometry(0.014, 0.014, 1.0, 5); barG.translate(0, 0.62, 0);
  grp.add(mk(postG, fence.posts, 0.25), mk(barG, fence.bars, 0.25));
  const railGeos = [];
  for (const [p, q] of fence.rails) for (const h of [0.35, 1.15, 1.22]) {
    const a = toV(p[0], p[1], p[2] + 0.25 + h), b = toV(q[0], q[1], q[2] + 0.25 + h);
    const len = a.distanceTo(b); if (len < 0.05) continue;
    const g = new THREE.CylinderGeometry(0.025, 0.025, len, 6);
    g.rotateZ(Math.PI / 2);
    const ang = Math.atan2(-(b.z - a.z), b.x - a.x);
    g.rotateY(ang);
    const mid = a.clone().add(b).multiplyScalar(0.5); g.translate(mid.x, mid.y, mid.z);
    railGeos.push(g);
  }
  if (railGeos.length) grp.add(new THREE.Mesh(mergeGeometries(railGeos), M.steel));

  // rambu
  for (const s of sc.signs) {
    const g = new THREE.Group();
    g.position.copy(toV(s.x, s.y, s.z + 0.25));
    const a = s.a * Math.PI / 180;
    const nx = Math.cos(a) * s.f, ny = Math.sin(a) * s.f;   // normal pelat (arah datang pengemudi, dunia)
    g.rotation.y = Math.atan2(nx, -ny);
    const h = s.k === 'flyover' ? 5.5 : 2.6;
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, h, 8), new THREE.MeshStandardMaterial({ color: 0x333333 }));
    pole.position.y = h / 2; g.add(pole);
    // pita kuning-hitam pada tiang (seperti foto)
    for (let k = 0; k < 4; k++) { const b = new THREE.Mesh(new THREE.CylinderGeometry(0.056, 0.056, 0.18, 8), M.yellowPaint); b.position.y = 0.3 + k * 0.4; g.add(b); }
    const size = s.k === 'flyover' ? 2.2 : 0.75;
    const pl = new THREE.Mesh(new THREE.PlaneGeometry(size, size), new THREE.MeshStandardMaterial({ map: uturnTexture(s.k), side: THREE.DoubleSide }));
    pl.position.set(0, h + size / 2 - 0.1, 0.06); g.add(pl);
    grp.add(g);
  }

  // marka panah (S1)
  if (sc.arrows) {
    const tex = arrowTexture();
    for (const a of sc.arrows) {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 4.5), new THREE.MeshBasicMaterial({ map: tex, transparent: true }));
      m.rotation.x = -Math.PI / 2; m.rotation.z = (a.a - 90) * Math.PI / 180;
      m.position.copy(toV(a.x, a.y, a.z + 0.02)); grp.add(m);
    }
  }

  // APILL (S1)
  const lights = [];
  if (sc.tls) {
    const groups = {};
    for (const l of sc.tls.links) {
      const fe = l.from.replace(/_\d+$/, ''), te = l.to.replace(/_\d+$/, '');
      let cls;
      if (fe.startsWith('NB')) cls = te === 'GER_out' ? 'NB_left' : te.startsWith('SB') ? 'NB_uturn' : 'NB_thru';
      else if (fe.startsWith('SB')) cls = te === 'GER_out' ? 'SB_right' : te.startsWith('NB') ? 'SB_uturn' : 'SB_thru';
      else cls = te.startsWith('NB') ? 'GER_left' : 'GER_right';
      (groups[cls] = groups[cls] || []).push(l);
    }
    const heads = [['SB_right', 1.5], ['SB_thru', -1.5], ['NB_thru', 1.5], ['GER_left', 1.2]];
    for (const [cls, side] of heads) {
      const ls = groups[cls]; if (!ls) continue;
      const l = ls[0];
      const g = new THREE.Group();
      const p = toV(l.x, l.y, 0);
      // z dari lajur terdekat
      const ln = sc.lanes.find(x => l.from.startsWith(x.e)) || sc.lanes[0];
      const zEnd = ln.s[ln.s.length - 1][2];
      g.position.set(p.x, zEnd, p.z);
      const s0 = ln.s[ln.s.length - 2], s1 = ln.s[ln.s.length - 1];
      const hd = Math.atan2(s1[1] - s0[1], s1[0] - s0[0]);
      g.rotation.y = Math.atan2(-Math.cos(hd), Math.sin(hd));  // menghadap pengemudi yang datang
      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 4.2, 8), new THREE.MeshStandardMaterial({ color: 0x2a2a2a }));
      pole.position.set(side, 2.1, 0); g.add(pole);
      const box = new THREE.Mesh(new THREE.BoxGeometry(0.42, 1.2, 0.3), new THREE.MeshStandardMaterial({ color: 0x151515 }));
      box.position.set(side, 3.8, 0); g.add(box);
      const lamps = {};
      [['r', 4.18, 0xff2a2a], ['y', 3.8, 0xffb000], ['g', 3.42, 0x22e070]].forEach(([k, y, col]) => {
        const mat = new THREE.MeshStandardMaterial({ color: 0x222222, emissive: col, emissiveIntensity: 0 });
        const lamp = new THREE.Mesh(new THREE.CircleGeometry(0.15, 16), mat);
        lamp.position.set(side, y, 0.16); g.add(lamp); lamps[k] = mat;
      });
      grp.add(g);
      lights.push({ idx: ls.map(x => x.i), lamps, cls });
    }
  }

  // Flyover (S2): gelagar + pilar di bagian tinggi, dinding penahan di oprit, parapet beton
  if (sc.flyover) {
    const F = sc.flyover, s = F.s, w = F.w;
    const parapetL = sweepBox(s, 0.3, 0.0, 1.05, w / 2 + 0.15), parapetR = sweepBox(s, 0.3, 0.0, 1.05, -w / 2 - 0.15);
    grp.add(new THREE.Mesh(mergeGeometries([parapetL, parapetR]), M.concrete));
    // bagian bawah: per segmen pilih gelagar (tinggi) atau dinding penahan (rendah)
    const highSeg = [], lowSeg = [];
    const groundAt = (p) => sampleTerrain(p[0], p[1]);
    let cur = null, curType = null;
    for (const p of s) {
      const h = p[2] - groundAt(p);
      const type = h > 4.6 ? 'high' : 'low';
      if (type !== curType) { if (cur && cur.length > 1) (curType === 'high' ? highSeg : lowSeg).push(cur); cur = cur ? [cur[cur.length - 1]] : []; curType = type; }
      cur.push(p);
    }
    if (cur && cur.length > 1) (curType === 'high' ? highSeg : lowSeg).push(cur);
    const gg = [];
    for (const seg of highSeg) gg.push(sweepBox(seg, w + 0.8, -1.7, -0.02));
    for (const seg of lowSeg) gg.push(sweepBox(seg, w + 0.8, seg.map(p => groundAt(p) - 0.4), -0.02));
    if (gg.length) { const m = new THREE.Mesh(mergeGeometries(gg), M.concreteDark); m.castShadow = true; m.receiveShadow = true; grp.add(m); }
    for (const pr of F.piers) {
      const h = pr[3] - 1.7 - pr[2];
      const col = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.85, h, 16), M.concrete);
      col.position.copy(toV(pr[0], pr[1], pr[2] + h / 2)); col.castShadow = true; grp.add(col);
      const cap = new THREE.Mesh(new THREE.BoxGeometry(w + 1.4, 0.9, 2.0), M.concrete);
      cap.position.copy(toV(pr[0], pr[1], pr[3] - 1.7 - 0.45)); grp.add(cap);
    }
  }
  scene.add(grp);
  return { group: grp, drivable, lights };
}

// sampel tanah (diisi dari common.json)
let TERR = null;
export function setTerrain(t) { TERR = t; }
export function sampleTerrain(x, y) {
  if (!TERR) return 0;
  const fx = (x - TERR.x0) / TERR.step, fy = (y - TERR.y0) / TERR.step;
  const i = Math.max(0, Math.min(TERR.nx - 2, Math.floor(fx))), j = Math.max(0, Math.min(TERR.ny - 2, Math.floor(fy)));
  const tx = Math.min(1, Math.max(0, fx - i)), ty = Math.min(1, Math.max(0, fy - j));
  const z = TERR.z;
  return (z[j][i] * (1 - tx) + z[j][i + 1] * tx) * (1 - ty) + (z[j + 1][i] * (1 - tx) + z[j + 1][i + 1] * tx) * ty + 0.25;
}

export function updateLights(lights, state) {
  if (!state) return;
  for (const L of lights) {
    const ch = state[L.idx[0]] || 'r';
    const on = ch === 'G' || ch === 'g' ? 'g' : ch === 'y' || ch === 'Y' ? 'y' : 'r';
    for (const k of ['r', 'y', 'g']) L.lamps[k].emissiveIntensity = k === on ? 2.2 : 0.0;
  }
}
