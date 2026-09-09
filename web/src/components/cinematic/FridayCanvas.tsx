"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { FridayCore3D } from "./FridayCore3D";
import { ParticleSystem3D } from "./ParticleSystem3D";
import { RepositoryGraph3D } from "./RepositoryGraph3D";
import { fridayAudio } from "./FridayAudio";

interface FridayCanvasProps {
  scrollProgress: number; // 0.0 to 1.0
  onNodeHover?: (nodeData: any | null) => void;
}

export function FridayCanvas({ scrollProgress, onNodeHover }: FridayCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef(scrollProgress);
  scrollRef.current = scrollProgress;

  useEffect(() => {
    if (!containerRef.current) return;

    // 1. Setup Three.js Scene, Camera & WebGL Renderer
    const width = window.innerWidth;
    const height = window.innerHeight;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x02040a, 0.025);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 18);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;

    containerRef.current.appendChild(renderer.domElement);

    // 2. Global Lights
    const ambientLight = new THREE.AmbientLight(0x0a192f, 1.2);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x00f0ff, 1.5);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    const rimLight = new THREE.DirectionalLight(0x8b5cf6, 1.8);
    rimLight.position.set(-5, -5, -5);
    scene.add(rimLight);

    // 3. Mount 3D Constructs
    const core = new FridayCore3D();
    scene.add(core.group);

    const particles = new ParticleSystem3D(3800);
    scene.add(particles.points);

    const repoGraph = new RepositoryGraph3D();
    scene.add(repoGraph.group);

    // 4. Mouse Tracking & Raycasting
    const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    const raycaster = new THREE.Raycaster();
    const mouseVector = new THREE.Vector2(-999, -999);

    const handleMouseMove = (e: MouseEvent) => {
      mouse.targetX = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.targetY = -(e.clientY / window.innerHeight) * 2 + 1;

      mouseVector.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouseVector.y = -(e.clientY / window.innerHeight) * 2 + 1;
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });

    // 5. Window Resize
    const handleResize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener("resize", handleResize);

    // 6. Render Animation Loop
    let animationId: number;
    const clock = new THREE.Clock();
    let currentCamPos = new THREE.Vector3(0, 0, 18);
    let targetLookAt = new THREE.Vector3(0, 0, 0);

    const animate = () => {
      animationId = requestAnimationFrame(animate);

      const delta = Math.min(clock.getDelta(), 0.1);
      const time = clock.getElapsedTime();
      const progress = scrollRef.current;

      // Mouse Lerp Damping for silky parallax
      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;

      // Update Subsystems
      core.update(time, delta, progress, mouse);
      particles.update(time, delta, progress, mouse);
      repoGraph.update(time, delta, progress, mouse);

      // Camera Choreography across the 3 Scenes
      // Scene 1 (Boot 0.0 - 0.3): Distance (0, 0, 18)
      // Scene 2 (Awaken 0.3 - 0.6): Approach (0, 1.0, 9.0)
      // Scene 3 (Repo 0.6 - 1.0): Orbit vantage (2.5, 3.5, 12.5)
      let desiredCamX = 0;
      let desiredCamY = 0;
      let desiredCamZ = 18;

      if (progress <= 0.45) {
        const t = Math.max(0, progress / 0.45);
        desiredCamX = THREE.MathUtils.lerp(0, 0, t);
        desiredCamY = THREE.MathUtils.lerp(0, 1.2, t);
        desiredCamZ = THREE.MathUtils.lerp(18, 9.2, t);
      } else {
        const t = Math.min(1.0, (progress - 0.45) / 0.55);
        desiredCamX = THREE.MathUtils.lerp(0, 2.5, t);
        desiredCamY = THREE.MathUtils.lerp(1.2, 3.2, t);
        desiredCamZ = THREE.MathUtils.lerp(9.2, 12.8, t);
      }

      // Add mouse parallax + subtle breathing float
      const breathFloatX = Math.sin(time * 0.4) * 0.15;
      const breathFloatY = Math.cos(time * 0.5) * 0.15;

      currentCamPos.x += (desiredCamX + mouse.x * 1.5 + breathFloatX - currentCamPos.x) * 0.06;
      currentCamPos.y += (desiredCamY + mouse.y * 1.2 + breathFloatY - currentCamPos.y) * 0.06;
      currentCamPos.z += (desiredCamZ - currentCamPos.z) * 0.06;

      camera.position.copy(currentCamPos);

      // Target lookAt lerp
      let lookTargetX = 0;
      let lookTargetY = 0;
      let lookTargetZ = 0;
      if (progress > 0.5) {
        lookTargetX = THREE.MathUtils.lerp(0, 0.5, (progress - 0.5) * 2);
        lookTargetY = THREE.MathUtils.lerp(0, 0.8, (progress - 0.5) * 2);
      }
      targetLookAt.x += (lookTargetX - targetLookAt.x) * 0.05;
      targetLookAt.y += (lookTargetY - targetLookAt.y) * 0.05;
      targetLookAt.z += (lookTargetZ - targetLookAt.z) * 0.05;

      camera.lookAt(targetLookAt);

      // Raycast on Repo Nodes when in Scene 3
      if (progress > 0.45) {
        raycaster.setFromCamera(mouseVector, camera);
        const nodeGroups = repoGraph.getNodes();
        const meshes: THREE.Mesh[] = [];
        nodeGroups.forEach((g) => {
          if (g.children[0] instanceof THREE.Mesh) {
            meshes.push(g.children[0]);
          }
        });

        const intersects = raycaster.intersectObjects(meshes, false);
        if (intersects.length > 0) {
          const hitMesh = intersects[0].object;
          const parentGroup = hitMesh.parent;
          if (parentGroup && parentGroup.userData) {
            repoGraph.hoveredNodeId = parentGroup.userData.id;
            if (onNodeHover) onNodeHover(parentGroup.userData);
          }
        } else {
          repoGraph.hoveredNodeId = null;
          if (onNodeHover) onNodeHover(null);
        }
      }

      renderer.render(scene, camera);
    };

    animate();

    // 7. Cleanup on Unmount
    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);

      core.dispose();
      particles.dispose();
      repoGraph.dispose();
      renderer.dispose();

      if (containerRef.current && renderer.domElement) {
        containerRef.current.removeChild(renderer.domElement);
      }
    };
  }, [onNodeHover]);

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 pointer-events-none z-0 overflow-hidden"
      style={{
        background: "radial-gradient(circle at 50% 50%, #030a1a 0%, #010308 70%, #000000 100%)",
      }}
    />
  );
}

