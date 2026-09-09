import * as THREE from "three";

export interface RepoNodeData {
  id: string;
  name: string;
  type: "brain" | "orchestrator" | "healing" | "memory" | "test" | "api" | "provider" | "ast";
  pos: [number, number, number];
  color: number;
  filesCount: number;
  status: string;
}

const REPO_NODES: RepoNodeData[] = [
  {
    id: "brain",
    name: "core/brain/manager.py",
    type: "brain",
    pos: [2.5, 1.8, 1.0],
    color: 0x00f0ff,
    filesCount: 42,
    status: "ACTIVE • MULTI-PROVIDER",
  },
  {
    id: "orchestrator",
    name: "services/ai_service.py",
    type: "orchestrator",
    pos: [0.0, 3.2, -0.5],
    color: 0x38bdf8,
    filesCount: 18,
    status: "ACTIVE • TOOL ROUTER",
  },
  {
    id: "healing",
    name: "self_healing/executor.py",
    type: "healing",
    pos: [-3.5, 0.8, 1.5],
    color: 0xf43f5e,
    filesCount: 14,
    status: "READY • AST GUARD",
  },
  {
    id: "memory",
    name: "memory/memory_manager.py",
    type: "memory",
    pos: [3.8, -1.8, 0.0],
    color: 0xf59e0b,
    filesCount: 22,
    status: "SYNCED • PERSISTED",
  },
  {
    id: "test",
    name: "tests/regression_suite.py",
    type: "test",
    pos: [-2.8, -2.5, 0.5],
    color: 0x10b981,
    filesCount: 24,
    status: "138/138 PASSING",
  },
  {
    id: "api",
    name: "api/fastapi_gateway.py",
    type: "api",
    pos: [-0.5, -3.2, -1.0],
    color: 0x8b5cf6,
    filesCount: 16,
    status: "RUNNING • PORT 8000",
  },
  {
    id: "provider",
    name: "providers/openrouter.py",
    type: "provider",
    pos: [4.2, 3.0, -1.5],
    color: 0x06b6d4,
    filesCount: 6,
    status: "ONLINE • LLAMA-3.3-70B",
  },
  {
    id: "ast",
    name: "intelligence/ast_inspector.py",
    type: "ast",
    pos: [-4.5, 2.5, -0.5],
    color: 0xa855f7,
    filesCount: 12,
    status: "PARSED • 124 SYMBOLS",
  },
];

const CONNECTIONS: [string, string][] = [
  ["brain", "orchestrator"],
  ["orchestrator", "provider"],
  ["orchestrator", "memory"],
  ["orchestrator", "api"],
  ["healing", "ast"],
  ["healing", "test"],
  ["healing", "orchestrator"],
  ["api", "brain"],
  ["ast", "brain"],
];

/**
 * 3D Spatial Repository Graph
 * Living constellation of code files, modules, dependencies, and streaming data pulses.
 */
export class RepositoryGraph3D {
  public group: THREE.Group;
  private nodeMeshes: Map<string, THREE.Group> = new Map();
  private splineCurves: { curve: THREE.QuadraticBezierCurve3; points: THREE.Vector3[]; line: THREE.Line }[] = [];
  private photonPackets: { mesh: THREE.Mesh; curveIndex: number; progress: number; speed: number }[] = [];

  public hoveredNodeId: string | null = null;

  constructor() {
    this.group = new THREE.Group();
    this.group.visible = false; // Becomes visible in Scene 3

    this.createNodes();
    this.createSplineConnections();
    this.createPhotonPackets();
  }

  private createNodes() {
    REPO_NODES.forEach((data) => {
      const nodeGroup = new THREE.Group();
      nodeGroup.position.set(...data.pos);

      // Core Node Geometry (Faceted crystalline diamond)
      const geo = new THREE.OctahedronGeometry(0.35, 0);
      const mat = new THREE.MeshStandardMaterial({
        color: data.color,
        emissive: data.color,
        emissiveIntensity: 0.8,
        roughness: 0.1,
        metalness: 0.9,
      });
      const mesh = new THREE.Mesh(geo, mat);
      nodeGroup.add(mesh);

      // Outer Pulsing Orbit Ring
      const ringGeo = new THREE.RingGeometry(0.55, 0.62, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: data.color,
        transparent: true,
        opacity: 0.4,
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      nodeGroup.add(ring);

      // Node Point Light
      const light = new THREE.PointLight(data.color, 1.5, 6.0);
      nodeGroup.add(light);

      nodeGroup.userData = data;
      this.nodeMeshes.set(data.id, nodeGroup);
      this.group.add(nodeGroup);
    });
  }

  private createSplineConnections() {
    const lineMat = new THREE.LineBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.25,
      blending: THREE.AdditiveBlending,
    });

    CONNECTIONS.forEach(([sourceId, targetId]) => {
      const source = REPO_NODES.find((n) => n.id === sourceId);
      const target = REPO_NODES.find((n) => n.id === targetId);
      if (!source || !target) return;

      const vSource = new THREE.Vector3(...source.pos);
      const vTarget = new THREE.Vector3(...target.pos);

      // Quadratic curve with an arched midpoint
      const mid = new THREE.Vector3()
        .addVectors(vSource, vTarget)
        .multiplyScalar(0.5)
        .add(new THREE.Vector3(0, 0.8, 0.5));

      const curve = new THREE.QuadraticBezierCurve3(vSource, mid, vTarget);
      const points = curve.getPoints(32);
      const geo = new THREE.BufferGeometry().setFromPoints(points);
      const line = new THREE.Line(geo, lineMat.clone());

      this.splineCurves.push({ curve, points, line });
      this.group.add(line);
    });
  }

  private createPhotonPackets() {
    const photonGeo = new THREE.SphereGeometry(0.06, 12, 12);
    const photonMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      blending: THREE.AdditiveBlending,
    });

    // 2-3 photons per connection spline
    this.splineCurves.forEach((_, idx) => {
      for (let p = 0; p < 2; p++) {
        const mesh = new THREE.Mesh(photonGeo, photonMat);
        this.photonPackets.push({
          mesh,
          curveIndex: idx,
          progress: Math.random(),
          speed: 0.15 + Math.random() * 0.2,
        });
        this.group.add(mesh);
      }
    });
  }

  public update(time: number, delta: number, scrollProgress: number, mouse: { x: number; y: number }) {
    // Visibility threshold: Scene 3 (0.45 to 1.0)
    if (scrollProgress < 0.4) {
      this.group.visible = false;
      return;
    }
    this.group.visible = true;

    // Fade-in / scale-in transition
    const enterT = Math.min(1.0, (scrollProgress - 0.4) / 0.2);
    this.group.scale.set(enterT, enterT, enterT);
    this.group.position.x = mouse.x * 0.6;
    this.group.position.y = mouse.y * 0.6;

    // Animate Nodes
    this.nodeMeshes.forEach((nodeGroup, id) => {
      const mesh = nodeGroup.children[0] as THREE.Mesh;
      const ring = nodeGroup.children[1] as THREE.Mesh;

      mesh.rotation.y += delta * 0.8;
      mesh.rotation.x += delta * 0.5;

      const isHovered = this.hoveredNodeId === id;
      const hoverScale = isHovered ? 1.6 : 1.0;
      const pulse = Math.sin(time * 3.0 + nodeGroup.position.x) * 0.08 + hoverScale;
      mesh.scale.set(pulse, pulse, pulse);

      ring.rotation.z += delta * 0.4;
      ring.lookAt(new THREE.Vector3(0, 0, 10)); // billboard toward camera
    });

    // Animate Data Photons traveling along connection curves
    this.photonPackets.forEach((packet) => {
      packet.progress += delta * packet.speed;
      if (packet.progress > 1.0) packet.progress = 0;

      const curve = this.splineCurves[packet.curveIndex].curve;
      const pos = curve.getPoint(packet.progress);
      packet.mesh.position.copy(pos);
    });

    // Subtly rotate entire software universe
    this.group.rotation.y = Math.sin(time * 0.1) * 0.06;
  }

  public getNodes(): THREE.Group[] {
    return Array.from(this.nodeMeshes.values());
  }

  public dispose() {
    this.nodeMeshes.forEach((group) => {
      group.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          child.geometry.dispose();
          if (Array.isArray(child.material)) {
            child.material.forEach((m) => m.dispose());
          } else {
            child.material.dispose();
          }
        }
      });
    });
  }
}

