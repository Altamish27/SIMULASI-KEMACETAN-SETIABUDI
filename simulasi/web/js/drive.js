// Mode kemudi: fisika kinematik (model sepeda), efek tanjakan, raycast permukaan jalan, deteksi tabrakan.
import * as THREE from 'three';
import { makeGeometries, DIM } from './vehicles.js';

const CODE = { motor: 0, mobil: 1, angkot: 2, truk: 3, bus: 4 };
// vmax (m/s), akselerasi, rem, jarak sumbu roda, sudut setir maks (rad)
const PHYS = {
  motor: { vmax: 16.5, acc: 3.0, brk: 7.5, wb: 1.3, steer: 0.62 },
  mobil: { vmax: 22, acc: 2.6, brk: 7.0, wb: 2.6, steer: 0.58 },
  angkot: { vmax: 16, acc: 1.9, brk: 6.0, wb: 2.3, steer: 0.58 },
  truk: { vmax: 14, acc: 0.9, brk: 5.0, wb: 3.8, steer: 0.52 },   // radius putar ±8 m (truk engkel)
  bus: { vmax: 13, acc: 0.8, brk: 5.0, wb: 5.5, steer: 0.55 },    // radius putar ±10 m
};

export class Driver {
  constructor(scene, camera) {
    this.scene = scene; this.camera = camera;
    this.active = false; this.keys = {};
    this.geo = makeGeometries();
    this.mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.5, metalness: 0.2, color: 0xffffff });
    this.mesh = null; this.ray = new THREE.Raycaster(); this.down = new THREE.Vector3(0, -1, 0);
    this.camMode = 0; this.surfaces = []; this.lastSend = 0; this.hint = '';
    window.addEventListener('keydown', e => {
      if (!this.active) return;
      this.keys[e.code] = true;
      if (e.code === 'KeyC') this.camMode = (this.camMode + 1) % 3;
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) e.preventDefault();
    });
    window.addEventListener('keyup', e => { this.keys[e.code] = false; });
  }

  start(vtype, pose, surfaces) {
    this.stop();
    this.vtype = vtype; this.P = PHYS[vtype]; this.dim = DIM[CODE[vtype]];
    this.surfaces = surfaces;
    const geo = this.geo[CODE[vtype]].clone();
    this.mesh = new THREE.Mesh(geo, this.mat.clone());
    this.mesh.material.color.set(vtype === 'angkot' || vtype === 'bus' || vtype === 'truk' ? 0xffb0b8 : 0xe3263f);
    this.mesh.castShadow = true;
    this.scene.add(this.mesh);
    // pose dari server = posisi depan kendaraan pada lajur
    const a = pose.a * Math.PI / 180;
    this.h = a;                                    // heading (rad, matematis: 0 = timur)
    this.x = pose.x - Math.cos(a) * this.dim.L / 2; this.y = pose.y - Math.sin(a) * this.dim.L / 2;
    this.z = null; this.v = 0; this.st = 0; this.active = true; this.crash = 0;
    this.groundZ();
  }

  stop() {
    if (this.mesh) { this.scene.remove(this.mesh); this.mesh = null; }
    this.active = false;
  }

  groundZ() {
    const from = this.z === null ? 60 : this.z + 1.6;
    this.ray.set(new THREE.Vector3(this.x, from, -this.y), this.down);
    this.ray.far = this.z === null ? 200 : 6;
    const hits = this.ray.intersectObjects(this.surfaces, false);
    if (hits.length) {
      this.z = hits[0].point.y;
      this.hint = hits[0].object.userData.edge === 'FO' ? 'FO' : '';
      this.onRoad = !!hits[0].object.userData.edge || hits[0].object.name !== 'terrain';
    }
    return this.z ?? 0;
  }

  update(dt, others) {
    if (!this.active) return null;
    const K = this.keys, P = this.P;
    const gas = K.KeyW || K.ArrowUp, brake = K.KeyS || K.ArrowDown;
    const left = K.KeyA || K.ArrowLeft, right = K.KeyD || K.ArrowRight, hand = K.Space;
    // setir halus (lebih sensitif pada kecepatan rendah)
    const target = (left ? 1 : 0) - (right ? 1 : 0);
    this.st += (target * P.steer - this.st) * Math.min(1, dt * 4);
    // tanjakan: komponen gravitasi
    const z0 = this.z ?? 0;
    let a = 0;
    if (gas) a = this.v >= -0.1 ? P.acc * (1 - Math.max(0, this.v) / P.vmax) : P.brk;
    if (brake) a = this.v > 0.2 ? -P.brk : -1.5;          // rem, lalu mundur pelan
    if (hand) a = -Math.sign(this.v) * P.brk * 1.2;
    if (!gas && !brake && !hand) a = -Math.sign(this.v) * 0.4;  // gesekan
    a -= 9.81 * (this.grade || 0);
    this.v += a * dt;
    if (!gas && Math.abs(this.v) < 0.15 && !brake) this.v = 0;
    this.v = Math.max(-3, Math.min(P.vmax, this.v));
    if (this.crash > 0) { this.crash -= dt; this.v = Math.min(this.v, 0); }
    // model sepeda
    this.h += (this.v / P.wb) * Math.tan(this.st) * dt;
    const nx = this.x + Math.cos(this.h) * this.v * dt, ny = this.y + Math.sin(this.h) * this.v * dt;
    // tabrakan sederhana (kotak berorientasi, diperkecil sedikit)
    let hit = false;
    for (const o of others) {
      const dx = o.x - nx, dy = o.y - ny;
      if (dx * dx + dy * dy > 144) continue;
      const lx = dx * Math.cos(this.h) + dy * Math.sin(this.h), ly = -dx * Math.sin(this.h) + dy * Math.cos(this.h);
      const rel = Math.abs(Math.sin(o.a - (Math.PI / 2 - this.h)));
      const ex = this.dim.L / 2 + (o.L / 2) * (1 - rel) + (o.W / 2) * rel - 0.15;
      const ey = this.dim.W / 2 + (o.W / 2) * (1 - rel) + (o.L / 2) * rel - 0.15;
      if (Math.abs(lx) < ex && Math.abs(ly) < ey && Math.abs(o.z - (this.z ?? 0)) < 2.5) { hit = true; break; }
    }
    if (hit) { this.v = -0.5; this.crash = 0.6; this.onCrash && this.onCrash(); }
    else { this.x = nx; this.y = ny; }
    const z1 = this.groundZ();
    const ds = Math.abs(this.v * dt);
    if (ds > 0.01) this.grade = Math.max(-0.12, Math.min(0.12, (z1 - z0) / ds * Math.sign(this.v || 1)));
    // render
    this.mesh.position.set(this.x, z1, -this.y);
    this.mesh.rotation.set(0, this.h, 0);
    this.mesh.rotateZ(Math.atan(this.grade || 0));
    this.followCam(dt);
    // posisi depan (untuk SUMO)
    const fx = this.x + Math.cos(this.h) * this.dim.L / 2, fy = this.y + Math.sin(this.h) * this.dim.L / 2;
    return { x: fx, y: fy, a: this.h * 180 / Math.PI, v: Math.max(0, this.v), edge: this.hint };
  }

  followCam(dt) {
    const c = this.camera, z = this.z ?? 0;
    const fwd = new THREE.Vector3(Math.cos(this.h), 0, -Math.sin(this.h));
    let pos, look;
    if (this.camMode === 0) {          // belakang
      const back = this.vtype === 'bus' ? 16 : this.vtype === 'truk' ? 13 : 9;
      pos = new THREE.Vector3(this.x, z + (this.vtype === 'motor' ? 2.6 : 3.6), -this.y).addScaledVector(fwd, -back);
      look = new THREE.Vector3(this.x, z + 1.2, -this.y).addScaledVector(fwd, 8);
      c.position.lerp(pos, Math.min(1, dt * 5));
    } else if (this.camMode === 1) {   // kabin pengemudi
      const eye = this.vtype === 'bus' || this.vtype === 'truk' ? 2.6 : this.vtype === 'motor' ? 1.7 : 1.25;
      pos = new THREE.Vector3(this.x, z + eye, -this.y).addScaledVector(fwd, this.vtype === 'motor' ? -0.1 : 0.4);
      look = pos.clone().addScaledVector(fwd, 20); look.y -= 0.6;
      c.position.copy(pos);
    } else {                           // atas
      pos = new THREE.Vector3(this.x, z + 55, -this.y).addScaledVector(fwd, -10);
      look = new THREE.Vector3(this.x, z, -this.y);
      c.position.lerp(pos, Math.min(1, dt * 4));
    }
    c.lookAt(look);
  }
}
