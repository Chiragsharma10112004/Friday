import * as THREE from "three";

/**
 * Refined 3D Particle Universe (Atmospheric depth, balanced density, ~3800 points)
 * Transforms seamlessly across Scene 1 (Boot), Scene 2 (Awaken), and Scene 3 (Repository Universe).
 * Subdued background depth ensures high legibility for core, repository graph, and HUD.
 */
export class ParticleSystem3D {
  public points: THREE.Points;
  private count: number;

  private geometry: THREE.BufferGeometry;
  private material: THREE.PointsMaterial;

  // Coordinate buffers for the 3 distinct scenes
  private bootPos: Float32Array;
  private awakenPos: Float32Array;
  private repoPos: Float32Array;
  private currentPos: Float32Array;
  private colors: Float32Array;
  private baseVelocities: Float32Array;

  constructor(count: number = 3800) {
    this.count = count;

    this.bootPos = new Float32Array(count * 3);
    this.awakenPos = new Float32Array(count * 3);
    this.repoPos = new Float32Array(count * 3);
    this.currentPos = new Float32Array(count * 3);
    this.colors = new Float32Array(count * 3);
    this.baseVelocities = new Float32Array(count * 3);

    this.generateTargetBuffers();

    this.geometry = new THREE.BufferGeometry();
    this.geometry.setAttribute("position", new THREE.BufferAttribute(this.currentPos, 3));
    this.geometry.setAttribute("color", new THREE.BufferAttribute(this.colors, 3));

    // Custom circular particle texture with soft falloff for atmospheric depth
    const canvas = document.createElement("canvas");
    canvas.width = 64;
    canvas.height = 64;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
      gradient.addColorStop(0, "rgba(255, 255, 255, 0.85)");
      gradient.addColorStop(0.2, "rgba(0, 240, 255, 0.45)");
      gradient.addColorStop(0.6, "rgba(139, 92, 246, 0.15)");
      gradient.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, 64, 64);
    }
    const texture = new THREE.CanvasTexture(canvas);

    this.material = new THREE.PointsMaterial({
      size: 0.11,
      map: texture,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending,
      vertexColors: true,
      depthWrite: false,
    });

    this.points = new THREE.Points(this.geometry, this.material);
  }

  private generateTargetBuffers() {
    const colorCyan = new THREE.Color(0x00f0ff);
    const colorViolet = new THREE.Color(0x8b5cf6);
    const colorWhite = new THREE.Color(0xd0e8f5);
    const colorDeepBlue = new THREE.Color(0x1e3a8a);
    const colorIndigo = new THREE.Color(0x4338ca);

    for (let i = 0; i < this.count; i++) {
      const i3 = i * 3;

      // 1. BOOT STATE: Expansive organic spherical dust cloud around distant core
      const radiusBoot = 5.0 + Math.pow(Math.random(), 1.6) * 38.0;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      this.bootPos[i3] = radiusBoot * Math.sin(phi) * Math.cos(theta);
      this.bootPos[i3 + 1] = radiusBoot * Math.sin(phi) * Math.sin(theta) * 0.65;
      this.bootPos[i3 + 2] = radiusBoot * Math.cos(phi);

      // Start current at boot positions
      this.currentPos[i3] = this.bootPos[i3];
      this.currentPos[i3 + 1] = this.bootPos[i3 + 1];
      this.currentPos[i3 + 2] = this.bootPos[i3 + 2];

      // 2. AWAKEN STATE: Vortex spirals & filament streams collapsing towards core
      const spiralArm = i % 4;
      const angle = (i / this.count) * Math.PI * 18 + (spiralArm * Math.PI) / 2;
      const radiusAwaken = 2.0 + Math.pow(i / this.count, 1.2) * 17.0;
      const zHeight = (Math.random() - 0.5) * 12.0;

      this.awakenPos[i3] = Math.cos(angle) * radiusAwaken + (Math.random() - 0.5) * 1.5;
      this.awakenPos[i3 + 1] = Math.sin(angle) * radiusAwaken * 0.4 + (Math.random() - 0.5) * 1.5;
      this.awakenPos[i3 + 2] = zHeight;

      // 3. REPOSITORY UNIVERSE STATE: Layered 3D constellation clusters (Code Modules, AST networks)
      const clusterId = i % 5;
      const clusterCenters = [
        [4.5, 2.0, -1.0],   // Brain/Intelligence cluster
        [-3.0, 3.5, 2.0],   // Ingestion & File Pipeline
        [2.0, -3.5, 3.0],   // Self-Healing & AST
        [-5.0, -2.5, -2.0], // Tests & Verification
        [0.0, 0.0, -6.0],   // Global Backbone Network
      ];
      const center = clusterCenters[clusterId];
      const clusterRadius = Math.random() * 4.8;
      const cTheta = Math.random() * Math.PI * 2;
      const cPhi = Math.acos(Math.random() * 2 - 1);

      this.repoPos[i3] = center[0] + clusterRadius * Math.sin(cPhi) * Math.cos(cTheta);
      this.repoPos[i3 + 1] = center[1] + clusterRadius * Math.sin(cPhi) * Math.sin(cTheta);
      this.repoPos[i3 + 2] = center[2] + clusterRadius * Math.cos(cPhi);

      // Hierarchical Particle Shading (Atmospheric background vs active sparks)
      const randType = Math.random();
      let c: THREE.Color;
      let intensity: number;

      if (randType < 0.40) {
        // Atmospheric deep background dust (dim, non-intrusive)
        c = randType < 0.20 ? colorDeepBlue : colorIndigo;
        intensity = 0.35 + Math.random() * 0.25;
      } else if (randType < 0.75) {
        // Soft cyan intelligence aura
        c = colorCyan;
        intensity = 0.55 + Math.random() * 0.3;
      } else if (randType < 0.92) {
        // Violet neural energy
        c = colorViolet;
        intensity = 0.5 + Math.random() * 0.35;
      } else {
        // Crisp focal point stars
        c = colorWhite;
        intensity = 0.85 + Math.random() * 0.15;
      }

      this.colors[i3] = c.r * intensity;
      this.colors[i3 + 1] = c.g * intensity;
      this.colors[i3 + 2] = c.b * intensity;

      // Drift velocities
      this.baseVelocities[i3] = (Math.random() - 0.5) * 0.08;
      this.baseVelocities[i3 + 1] = (Math.random() - 0.5) * 0.08;
      this.baseVelocities[i3 + 2] = (Math.random() - 0.5) * 0.08;
    }
  }

  public update(time: number, delta: number, scrollProgress: number, mouse: { x: number; y: number }) {
    const posAttr = this.geometry.attributes.position as THREE.BufferAttribute;
    const array = posAttr.array as Float32Array;

    for (let i = 0; i < this.count; i++) {
      const i3 = i * 3;

      let targetX = 0;
      let targetY = 0;
      let targetZ = 0;

      if (scrollProgress <= 0.45) {
        const t = Math.max(0, scrollProgress / 0.45);
        targetX = THREE.MathUtils.lerp(this.bootPos[i3], this.awakenPos[i3], t);
        targetY = THREE.MathUtils.lerp(this.bootPos[i3 + 1], this.awakenPos[i3 + 1], t);
        targetZ = THREE.MathUtils.lerp(this.bootPos[i3 + 2], this.awakenPos[i3 + 2], t);
      } else {
        const t = Math.min(1, (scrollProgress - 0.45) / 0.55);
        targetX = THREE.MathUtils.lerp(this.awakenPos[i3], this.repoPos[i3], t);
        targetY = THREE.MathUtils.lerp(this.awakenPos[i3 + 1], this.repoPos[i3 + 1], t);
        targetZ = THREE.MathUtils.lerp(this.awakenPos[i3 + 2], this.repoPos[i3 + 2], t);
      }

      // Organic cosmic wave noise
      const noise = Math.sin(time * 1.2 + this.bootPos[i3] * 0.25) * 0.12;
      const noiseY = Math.cos(time * 1.5 + this.bootPos[i3 + 1] * 0.25) * 0.12;

      // Mouse subtle gravitational interaction
      const dx = array[i3] - mouse.x * 5;
      const dy = array[i3 + 1] - mouse.y * 5;
      const dist = Math.sqrt(dx * dx + dy * dy);
      let mouseForceX = 0;
      let mouseForceY = 0;
      if (dist < 4.0 && dist > 0.1) {
        const force = (1.0 - dist / 4.0) * 0.3;
        mouseForceX = (dx / dist) * force;
        mouseForceY = (dy / dist) * force;
      }

      // Smooth lerp to target
      array[i3] += (targetX + noise + mouseForceX - array[i3]) * 0.06;
      array[i3 + 1] += (targetY + noiseY + mouseForceY - array[i3 + 1]) * 0.06;
      array[i3 + 2] += (targetZ - array[i3 + 2]) * 0.06;
    }

    posAttr.needsUpdate = true;

    // Slow ambient rotation of the particle field
    this.points.rotation.y = time * 0.025 + mouse.x * 0.08;
    this.points.rotation.x = Math.sin(time * 0.018) * 0.04 + mouse.y * 0.08;
  }

  public dispose() {
    this.geometry.dispose();
    this.material.dispose();
  }
}
