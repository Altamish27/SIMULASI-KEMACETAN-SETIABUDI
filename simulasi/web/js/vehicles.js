// Kendaraan SUMO → InstancedMesh per jenis, dengan interpolasi antar-frame & lampu rem.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// kode jenis dari server: 0 motor, 1 mobil, 2 angkot, 3 truk, 4 bus, 9 ego
export const DIM = {
  0: { L: 1.95, W: 0.75 }, 1: { L: 4.3, W: 1.75 }, 2: { L: 3.95, W: 1.6 }, 3: { L: 6.8, W: 2.4 }, 4: { L: 9.5, W: 2.5 },
};

function box(w, h, l, x, y, z, color) {
  // panjang sepanjang +X lokal, lebar Z, tinggi Y
  const g = new THREE.BoxGeometry(l, h, w); g.translate(x, y, z);
  const c = new THREE.Color(color), n = g.attributes.position.count, a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { a[3 * i] = c.r; a[3 * i + 1] = c.g; a[3 * i + 2] = c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(a, 3));
  return g;
}
function wheels(L, W, r, xs, color = 0x161616) {
  const out = [];
  for (const x of xs) for (const z of [-W / 2 + 0.12, W / 2 - 0.12]) {
    const g = new THREE.CylinderGeometry(r, r, 0.22, 10); g.rotateX(Math.PI / 2); g.translate(x, r, z);
    const c = new THREE.Color(color), n = g.attributes.position.count, a = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) { a[3 * i] = c.r; a[3 * i + 1] = c.g; a[3 * i + 2] = c.b; }
    g.setAttribute('color', new THREE.BufferAttribute(a, 3)); g.deleteAttribute('uv');
    out.push(g);
  }
  return out;
}
const clean = gs => gs.map(g => { if (g.attributes.uv) g.deleteAttribute('uv'); return g.index ? g.toNonIndexed() : g; });

export function makeGeometries() {
  const G = {};
  // Motor + pengendara (warna jaket di-tint per instance)
  G[0] = mergeGeometries(clean([
    box(0.32, 0.45, 1.7, 0, 0.55, 0, 0x2b2b2b), box(0.36, 0.25, 0.7, -0.15, 0.85, 0, 0x3a3a3a),
    box(0.42, 0.62, 0.42, -0.2, 1.25, 0, 0xffffff), box(0.3, 0.3, 0.3, -0.12, 1.72, 0, 0x202020),
    ...wheels(1.95, 0.4, 0.3, [-0.62, 0.62]),
  ]));
  // Mobil (badan di-tint warna acak)
  G[1] = mergeGeometries(clean([
    box(1.75, 0.72, 4.3, 0, 0.62, 0, 0xffffff),
    box(1.58, 0.55, 2.3, -0.25, 1.25, 0, 0x2a3440),
    box(1.6, 0.06, 2.2, -0.25, 1.55, 0, 0xffffff),
    box(1.5, 0.16, 0.06, 2.15, 0.78, 0, 0xfff4c0),
    ...wheels(4.3, 1.75, 0.33, [-1.35, 1.35]),
  ]));
  // Angkot hijau Bandung (Suzuki Carry)
  G[2] = mergeGeometries(clean([
    box(1.6, 1.25, 3.95, 0, 1.0, 0, 0x1f9a4f),
    box(1.62, 0.42, 2.7, -0.4, 1.32, 0, 0x22303a),
    box(1.62, 0.12, 3.95, 0, 0.72, 0, 0xf2f2f2),
    box(1.5, 0.45, 0.06, 1.98, 1.35, 0, 0x22303a),
    ...wheels(3.95, 1.6, 0.3, [-1.25, 1.3]),
  ]));
  // Dump truck engkel (kabin + bak kuning-hijau)
  G[3] = mergeGeometries(clean([
    box(2.3, 1.9, 1.7, 2.45, 1.45, 0, 0xe8c21c),
    box(2.1, 0.7, 0.06, 3.3, 1.9, 0, 0x22303a),
    box(2.4, 1.35, 4.6, -0.95, 1.65, 0, 0xd8b81a),
    box(2.42, 0.5, 4.62, -0.95, 1.2, 0, 0x2f9a3a),
    box(2.2, 0.35, 6.6, -0.1, 0.7, 0, 0x2a2a2a),
    ...wheels(6.8, 2.4, 0.48, [-2.3, -1.2, 2.3]),
  ]));
  // Bus sedang
  G[4] = mergeGeometries(clean([
    box(2.5, 2.4, 9.5, 0, 1.75, 0, 0x2f7d43),
    box(2.52, 0.8, 8.6, -0.2, 2.15, 0, 0x26323c),
    box(2.4, 0.12, 9.3, 0, 3.0, 0, 0xf2f2f2),
    box(2.3, 1.0, 0.06, 4.76, 2.0, 0, 0x26323c),
    ...wheels(9.5, 2.5, 0.5, [-3.2, 3.0]),
  ]));
  return G;
}

const MOTOR_JACKETS = [0x2d5aa8, 0x1f1f1f, 0xb93a32, 0x2f7d43, 0x6b4e9b, 0x8a8f96, 0xe08a1e, 0x14824f];
const CAR_COLORS = [0xf3f3f3, 0xf3f3f3, 0xe8e8e8, 0x1e1e1e, 0x9aa1a8, 0xc8ccd0, 0x7a1f24, 0x1d3f74, 0x2b2b2b, 0xd8c7a0, 0xeae0c8];

export class Traffic {
  constructor(scene) {
    this.scene = scene;
    this.geo = makeGeometries();
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.55, metalness: 0.15 });
    const cap = { 0: 2500, 1: 1600, 2: 300, 3: 250, 4: 200 };
    this.mesh = {};
    for (const k of [0, 1, 2, 3, 4]) {
      const m = new THREE.InstancedMesh(this.geo[k], mat, cap[k]);
      m.count = 0; m.castShadow = true; m.frustumCulled = false;
      m.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      scene.add(m); this.mesh[k] = m;
    }
    const bg = new THREE.PlaneGeometry(1, 0.22);
    this.brake = new THREE.InstancedMesh(bg, new THREE.MeshBasicMaterial({ color: 0xff2020, side: THREE.DoubleSide }), 3000);
    this.brake.count = 0; this.brake.frustumCulled = false; scene.add(this.brake);
    this.v = new Map();       // id → {k, p0, p1}
    this.tPrev = 0; this.tCur = 0; this.wallCur = 0; this.interval = 0.1;
    this._m = new THREE.Matrix4(); this._q = new THREE.Quaternion(); this._s = new THREE.Vector3(1, 1, 1); this._p = new THREE.Vector3();
    this._c = new THREE.Color(); this._up = new THREE.Vector3(0, 1, 0);
    this.list = [];           // posisi terbaru (untuk deteksi tabrakan ego)
  }

  clear() { this.v.clear(); for (const k in this.mesh) this.mesh[k].count = 0; this.brake.count = 0; }

  onFrame(f) {
    const now = performance.now() / 1000;
    if (this.wallCur) this.interval = Math.min(0.5, Math.max(0.03, 0.7 * this.interval + 0.3 * (now - this.wallCur)));
    this.wallCur = now;
    const seen = new Set();
    for (const r of f.v) {
      const [id, k, x, y, z, a, sp, sig] = r;
      if (k === 9) continue; // ego digambar sendiri
      seen.add(id);
      const cur = { x, y, z, a, sp, brake: (sig & 8) !== 0 };
      const e = this.v.get(id);
      if (e) { e.p0 = e.p1; e.p1 = cur; }
      else this.v.set(id, { k, p0: cur, p1: cur, h: id * 2654435761 % 1000 });
    }
    for (const id of this.v.keys()) if (!seen.has(id)) this.v.delete(id);
  }

  update() {
    const alpha = Math.min(1, (performance.now() / 1000 - this.wallCur) / this.interval);
    const counts = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0 };
    let nb = 0;
    this.list.length = 0;
    for (const e of this.v.values()) {
      const { p0, p1, k } = e;
      let da = p1.a - p0.a; if (da > 180) da -= 360; if (da < -180) da += 360;
      const a = (p0.a + da * alpha) * Math.PI / 180;
      const fx = p0.x + (p1.x - p0.x) * alpha, fy = p0.y + (p1.y - p0.y) * alpha, fz = p0.z + (p1.z - p0.z) * alpha;
      const d = DIM[k] || DIM[1];
      const dx = Math.sin(a), dy = Math.cos(a);          // arah (dunia)
      const cx = fx - dx * d.L / 2, cy = fy - dy * d.L / 2;
      this._p.set(cx, fz, -cy);
      this._q.setFromAxisAngle(this._up, Math.PI / 2 - a);
      this._m.compose(this._p, this._q, this._s);
      const m = this.mesh[k]; const i = counts[k]++;
      if (i >= m.instanceMatrix.count) continue;
      m.setMatrixAt(i, this._m);
      if (k === 0) m.setColorAt(i, this._c.setHex(MOTOR_JACKETS[e.h % MOTOR_JACKETS.length]));
      else if (k === 1) m.setColorAt(i, this._c.setHex(CAR_COLORS[e.h % CAR_COLORS.length]));
      else m.setColorAt(i, this._c.setHex(0xffffff));
      this.list.push({ x: cx, y: cy, z: fz, a, L: d.L, W: d.W });
      if (p1.brake && nb < 3000) {
        const rx = cx - dx * (d.L / 2 + 0.02), ry = cy - dy * (d.L / 2 + 0.02);
        this._p.set(rx, fz + (k >= 3 ? 1.0 : 0.75), -ry);
        this._s.set(d.W * 0.9, 1, 1);
        this._m.compose(this._p, this._q.setFromAxisAngle(this._up, Math.PI - a), this._s);
        this.brake.setMatrixAt(nb++, this._m);
        this._s.set(1, 1, 1);
      }
    }
    for (const k in this.mesh) {
      const m = this.mesh[k]; m.count = counts[k];
      m.instanceMatrix.needsUpdate = true; if (m.instanceColor) m.instanceColor.needsUpdate = true;
    }
    this.brake.count = nb; this.brake.instanceMatrix.needsUpdate = true;
  }
}
