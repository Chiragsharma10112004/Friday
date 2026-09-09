import * as THREE from "three";

/**
 * The FRIDAY Intelligence Core
 * Multi-layered, living geometric/energy construct.
 */
export class FridayCore3D {
  public group: THREE.Group;

  // Internal sub-components
  private singularity: THREE.Mesh;
  private singularityWire: THREE.LineSegments;
  private ring1: THREE.Mesh;
  private ring2: THREE.Mesh;
  private ring3: THREE.Mesh;
  private lattice: THREE.LineSegments;
  private coreLight: THREE.PointLight;
  private secondaryLight: THREE.PointLight;

  private baseRing1Scale: number = 1.0;
  private baseRing2Scale: number = 1.0;
  private baseRing3Scale: number = 1.0;

  constructor() {
    this.group = new THREE.Group();

    // 1. Quantum Singularity Core (Inner high-density energy polyhedron)
    const singularityGeo = new THREE.IcosahedronGeometry(1.2, 3);
    const singularityMat = new THREE.MeshStandardMaterial({
      color: 0x051329,
      emissive: 0x00d4ff,
      emissiveIntensity: 0.8,
      roughness: 0.1,
      metalness: 0.9,
      wireframe: false,
    });
    this.singularity = new THREE.Mesh(singularityGeo, singularityMat);
    this.group.add(this.singularity);

    // Wireframe overlay for the singularity
    const wireGeo = new THREE.WireframeGeometry(singularityGeo);
    const wireMat = new THREE.LineBasicMaterial({
      color: 0x70e4ff,
      transparent: true,
      opacity: 0.4,
      blending: THREE.AdditiveBlending,
    });
    this.singularityWire = new THREE.LineSegments(wireGeo, wireMat);
    this.group.add(this.singularityWire);

    // 2. Gimbal Gyroscopic Orbital Rings
    // Ring 1 (Inner Cyan)
    const ring1Geo = new THREE.TorusGeometry(2.2, 0.025, 16, 100);
    const ring1Mat = new THREE.MeshStandardMaterial({
      color: 0x00f0ff,
      emissive: 0x00f0ff,
      emissiveIntensity: 0.6,
      roughness: 0.2,
      metalness: 0.8,
    });
    this.ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
    this.group.add(this.ring1);

    // Ring 2 (Middle Electric Violet)
    const ring2Geo = new THREE.TorusGeometry(3.0, 0.03, 16, 120);
    const ring2Mat = new THREE.MeshStandardMaterial({
      color: 0x8b5cf6,
      emissive: 0x7c3aed,
      emissiveIntensity: 0.7,
      roughness: 0.2,
      metalness: 0.8,
    });
    this.ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
    this.group.add(this.ring2);

    // Ring 3 (Outer Data Perimeter)
    const ring3Geo = new THREE.TorusGeometry(3.8, 0.02, 16, 140);
    const ring3Mat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      emissive: 0x0284c7,
      emissiveIntensity: 0.5,
      roughness: 0.3,
      metalness: 0.7,
    });
    this.ring3 = new THREE.Mesh(ring3Geo, ring3Mat);
    this.group.add(this.ring3);

    // 3. Neural Lattice (Outer faceted geodesic shield)
    const latticeGeo = new THREE.DodecahedronGeometry(4.6, 1);
    const latticeWireGeo = new THREE.WireframeGeometry(latticeGeo);
    const latticeMat = new THREE.LineBasicMaterial({
      color: 0x06b6d4,
      transparent: true,
      opacity: 0.2,
      blending: THREE.AdditiveBlending,
    });
    this.lattice = new THREE.LineSegments(latticeWireGeo, latticeMat);
    this.group.add(this.lattice);

    // 4. Luminous Point Lights
    this.coreLight = new THREE.PointLight(0x00f0ff, 3.5, 30);
    this.group.add(this.coreLight);

    this.secondaryLight = new THREE.PointLight(0x9333ea, 2.5, 25);
    this.secondaryLight.position.set(2, 3, 2);
    this.group.add(this.secondaryLight);
  }

  public update(time: number, delta: number, scrollProgress: number, mouse: { x: number; y: number }) {
    // Respiration / Breathing pulse
    const breath = Math.sin(time * 2.2) * 0.08 + 1.0;
    const energyBurst = Math.sin(time * 4.0) * 0.15 + 1.0;

    // Singularity pulsating scale
    const coreScale = breath * (1.0 + Math.sin(scrollProgress * Math.PI) * 0.3);
    this.singularity.scale.set(coreScale, coreScale, coreScale);
    this.singularityWire.scale.copy(this.singularity.scale);

    // Singularity continuous rotation
    this.singularity.rotation.y += delta * 0.4;
    this.singularity.rotation.x += delta * 0.25;
    this.singularityWire.rotation.copy(this.singularity.rotation);

    // Ring rotations on gyroscopic offset axes
    const speedMult = 1.0 + scrollProgress * 2.5; // Rings accelerate as system awakens
    this.ring1.rotation.x += delta * 0.7 * speedMult;
    this.ring1.rotation.y += delta * 0.5 * speedMult;

    this.ring2.rotation.y += delta * 0.6 * speedMult;
    this.ring2.rotation.z += delta * 0.8 * speedMult;

    this.ring3.rotation.x -= delta * 0.4 * speedMult;
    this.ring3.rotation.z += delta * 0.6 * speedMult;

    // Outer lattice counter-rotation
    this.lattice.rotation.y -= delta * 0.15;
    this.lattice.rotation.x -= delta * 0.1;

    // Ring expansion during AWAKEN phase (Scene 2)
    const expansion = 1.0 + Math.max(0, Math.min(1.0, (scrollProgress - 0.2) / 0.4)) * 0.6;
    this.ring1.scale.set(expansion * breath, expansion * breath, expansion * breath);
    this.ring2.scale.set(expansion * 1.05, expansion * 1.05, expansion * 1.05);
    this.ring3.scale.set(expansion * 1.1, expansion * 1.1, expansion * 1.1);

    // Light modulation
    this.coreLight.intensity = 3.0 * energyBurst + (scrollProgress > 0.25 ? 2.0 : 0);
    this.secondaryLight.intensity = 2.0 * breath;

    // Mouse parallax reaction
    const targetRotX = mouse.y * 0.35;
    const targetRotY = mouse.x * 0.35;
    this.group.rotation.x += (targetRotX - this.group.rotation.x) * 0.05;
    this.group.rotation.y += (targetRotY - this.group.rotation.y) * 0.05;

    // Z-Position translation linked to scroll
    if (scrollProgress < 0.55) {
      // Moves closer then slightly drifts back
      this.group.position.z = THREE.MathUtils.lerp(0, 3.5, Math.min(1, scrollProgress * 2));
      this.group.position.x = THREE.MathUtils.lerp(0, -1.5, Math.max(0, (scrollProgress - 0.3) * 2));
      this.group.position.y = THREE.MathUtils.lerp(0, 0.5, Math.max(0, (scrollProgress - 0.3) * 2));
    } else {
      // Scene 3 Repository anchor position
      this.group.position.x = THREE.MathUtils.lerp(-1.5, -6.0, (scrollProgress - 0.55) / 0.45);
      this.group.position.y = THREE.MathUtils.lerp(0.5, 2.0, (scrollProgress - 0.55) / 0.45);
      this.group.position.z = THREE.MathUtils.lerp(3.5, -4.0, (scrollProgress - 0.55) / 0.45);
      const scaleDown = THREE.MathUtils.lerp(1.0, 0.55, (scrollProgress - 0.55) / 0.45);
      this.group.scale.set(scaleDown, scaleDown, scaleDown);
    }
  }

  public dispose() {
    this.singularity.geometry.dispose();
    (this.singularity.material as THREE.Material).dispose();
    this.singularityWire.geometry.dispose();
    (this.singularityWire.material as THREE.Material).dispose();
    this.ring1.geometry.dispose();
    (this.ring1.material as THREE.Material).dispose();
    this.ring2.geometry.dispose();
    (this.ring2.material as THREE.Material).dispose();
    this.ring3.geometry.dispose();
    (this.ring3.material as THREE.Material).dispose();
    this.lattice.geometry.dispose();
    (this.lattice.material as THREE.Material).dispose();
  }
}

