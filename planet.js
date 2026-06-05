import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const host = document.getElementById("planet-viewport");

if (host) {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 50);
  camera.position.set(0, 0.2, 5.2);

  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false });
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  renderer.domElement.tabIndex = 0;
  host.appendChild(renderer.domElement);

  const world = new THREE.Group();
  world.rotation.z = -0.08;
  scene.add(world);

  scene.add(new THREE.HemisphereLight(0xcaffdf, 0x03120c, 1.6));

  const key = new THREE.DirectionalLight(0xdffff0, 3.2);
  key.position.set(-3, 3, 4);
  scene.add(key);

  const rim = new THREE.PointLight(0x35ff91, 18, 12, 2);
  rim.position.set(3, 0, -2.5);
  scene.add(rim);

  const pulseLight = new THREE.PointLight(0xaaffcf, 0, 8, 2);
  pulseLight.position.set(0, 0, 3);
  scene.add(pulseLight);

  function randomFactory(seed) {
    let value = seed;
    return () => {
      value = (value * 1664525 + 1013904223) % 4294967296;
      return value / 4294967296;
    };
  }

  function makePlanetTexture() {
    const random = randomFactory(27);
    const size = 128;
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    const palette = ["#062d1d", "#08472a", "#0d6737", "#148448", "#22a85b", "#3bd476", "#71f39d"];

    for (let y = 0; y < size; y += 2) {
      for (let x = 0; x < size; x += 2) {
        const a = x / size * Math.PI * 2;
        const b = y / size * Math.PI;
        const terrain = Math.sin(a * 2.2 + Math.sin(b * 3) * 2) * 0.42
          + Math.sin(a * 5 - b * 4) * 0.24
          + Math.cos(a * 9 + b * 2) * 0.13
          + (random() - 0.5) * 0.35
          + Math.sin(b) * 0.28;
        const index = Math.max(0, Math.min(palette.length - 1, Math.floor((terrain + 0.8) * 3.2)));
        ctx.fillStyle = palette[index];
        ctx.fillRect(x, y, 2, 2);
      }
    }

    ctx.globalAlpha = 0.28;
    ctx.fillStyle = "#c7ffdb";
    for (let i = 0; i < 70; i += 1) {
      ctx.fillRect(Math.floor(random() * 64) * 2, Math.floor(random() * 64) * 2, 2 + Math.floor(random() * 8), 2);
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.wrapS = THREE.RepeatWrapping;
    texture.magFilter = THREE.NearestFilter;
    texture.minFilter = THREE.NearestFilter;
    return texture;
  }

  const planetTexture = makePlanetTexture();
  const planet = new THREE.Mesh(
    new THREE.SphereGeometry(1.48, 56, 32),
    new THREE.MeshStandardMaterial({
      map: planetTexture,
      roughness: 0.9,
      metalness: 0.03,
      emissive: 0x06351f,
      emissiveIntensity: 0.35,
      flatShading: true
    })
  );
  world.add(planet);

  const clouds = new THREE.Mesh(
    new THREE.SphereGeometry(1.505, 48, 28),
    new THREE.MeshBasicMaterial({
      color: 0x90ffc0,
      transparent: true,
      opacity: 0.07,
      wireframe: true,
      depthWrite: false
    })
  );
  world.add(clouds);

  const atmosphere = new THREE.Mesh(
    new THREE.SphereGeometry(1.61, 48, 28),
    new THREE.MeshBasicMaterial({
      color: 0x40ff98,
      transparent: true,
      opacity: 0.09,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
  );
  world.add(atmosphere);

  const ring = new THREE.Mesh(
    new THREE.RingGeometry(1.86, 2.2, 128),
    new THREE.MeshBasicMaterial({
      color: 0x6dffc0,
      transparent: true,
      opacity: 0.32,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    })
  );
  ring.rotation.set(1.17, -0.22, 0.06);
  world.add(ring);

  const moon = new THREE.Mesh(
    new THREE.IcosahedronGeometry(0.16, 1),
    new THREE.MeshStandardMaterial({
      color: 0x82ffb3,
      emissive: 0x0a4a2c,
      emissiveIntensity: 0.8,
      roughness: 1,
      flatShading: true
    })
  );
  scene.add(moon);

  const hotspots = [];
  [
    [0.68, 0.72, 1.18, "SOURCE NODE"],
    [-0.94, 0.24, 1.02, "BOSS SIGNAL"],
    [0.34, -0.98, 1.0, "LAUNCH POINT"]
  ].forEach(([x, y, z, label], index) => {
    const marker = new THREE.Group();
    const core = new THREE.Mesh(
      new THREE.IcosahedronGeometry(0.055, 1),
      new THREE.MeshBasicMaterial({ color: index === 1 ? 0xffe77d : 0xc8ffe0 })
    );
    const halo = new THREE.Mesh(
      new THREE.RingGeometry(0.08, 0.12, 18),
      new THREE.MeshBasicMaterial({
        color: index === 1 ? 0xffe77d : 0x45f08d,
        transparent: true,
        opacity: 0.75,
        side: THREE.DoubleSide,
        depthWrite: false
      })
    );
    marker.add(core, halo);
    marker.position.set(x, y, z).normalize().multiplyScalar(1.54);
    marker.userData.label = label;
    marker.userData.halo = halo;
    world.add(marker);
    hotspots.push(marker);
  });

  const signal = document.createElement("div");
  signal.className = "planet-signal";
  signal.textContent = "SIGNAL ACQUIRED";
  host.appendChild(signal);
  let signalTimer;

  function showSignal(text) {
    signal.textContent = text;
    signal.classList.add("visible");
    clearTimeout(signalTimer);
    signalTimer = setTimeout(() => signal.classList.remove("visible"), 1200);
  }

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enablePan = false;
  controls.enableDamping = true;
  controls.dampingFactor = 0.055;
  controls.rotateSpeed = 0.62;
  controls.zoomSpeed = 0.7;
  controls.minDistance = 3.5;
  controls.maxDistance = 7;
  controls.autoRotate = !matchMedia("(prefers-reduced-motion: reduce)").matches;
  controls.autoRotateSpeed = 0.75;

  const spinButton = document.getElementById("toggleSpin");
  const pulseButton = document.getElementById("pulsePlanet");

  function updateSpinButton() {
    if (!spinButton) return;
    spinButton.textContent = `AUTO SPIN: ${controls.autoRotate ? "ON" : "OFF"}`;
    spinButton.classList.toggle("is-active", controls.autoRotate);
    spinButton.setAttribute("aria-pressed", String(controls.autoRotate));
  }

  updateSpinButton();
  spinButton?.addEventListener("click", () => {
    controls.autoRotate = !controls.autoRotate;
    updateSpinButton();
  });

  let pulseStart = -1;
  pulseButton?.addEventListener("click", () => {
    pulseStart = performance.now();
    showSignal("ENERGY PULSE SENT");
  });

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let down = null;

  function setPointer(event) {
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  }

  renderer.domElement.addEventListener("pointerdown", (event) => {
    down = [event.clientX, event.clientY];
  });

  renderer.domElement.addEventListener("pointermove", (event) => {
    setPointer(event);
    raycaster.setFromCamera(pointer, camera);
    renderer.domElement.style.cursor = raycaster.intersectObjects(hotspots, true).length ? "pointer" : "grab";
  });

  renderer.domElement.addEventListener("pointerup", (event) => {
    if (!down) return;
    const distance = Math.hypot(event.clientX - down[0], event.clientY - down[1]);
    down = null;
    if (distance > 7) return;
    setPointer(event);
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObjects(hotspots, true)[0];
    if (!hit) return;
    const marker = hit.object.parent;
    marker.userData.clickedAt = performance.now();
    showSignal(marker.userData.label);
  });

  renderer.domElement.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      controls.autoRotate = !controls.autoRotate;
      updateSpinButton();
    }
  });

  function resize() {
    const width = Math.max(host.clientWidth, 1);
    const height = Math.max(host.clientHeight, 1);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    const scale = width < 500 ? 0.72 : 0.62;
    renderer.setSize(Math.floor(width * scale), Math.floor(height * scale), false);
    renderer.domElement.style.width = `${width}px`;
    renderer.domElement.style.height = `${height}px`;
  }

  new ResizeObserver(resize).observe(host);
  resize();

  let previous = performance.now();

  function animate(time) {
    const delta = Math.min((time - previous) / 1000, 0.05);
    previous = time;
    const elapsed = time / 1000;

    planet.rotation.y += delta * 0.025;
    clouds.rotation.y += delta * 0.05;
    ring.rotation.z += delta * 0.015;

    moon.position.set(
      Math.cos(elapsed * 0.55) * 2.55,
      Math.sin(elapsed * 0.72) * 0.38,
      Math.sin(elapsed * 0.55) * 1.45
    );
    moon.rotation.x += delta * 0.4;
    moon.rotation.y += delta * 0.55;

    hotspots.forEach((marker, index) => {
      marker.lookAt(camera.position);
      marker.userData.halo.rotation.z -= delta * (0.8 + index * 0.12);
      const pulse = 1 + Math.sin(elapsed * 3.2 + index) * 0.12;
      const age = time - (marker.userData.clickedAt || -10000);
      const click = age < 550 ? Math.sin(age / 550 * Math.PI) * 0.7 : 0;
      marker.scale.setScalar(pulse + click);
    });

    if (pulseStart >= 0) {
      const age = (time - pulseStart) / 1000;
      if (age < 1.2) {
        const wave = Math.sin(age / 1.2 * Math.PI);
        world.scale.setScalar(1 + wave * 0.065);
        atmosphere.material.opacity = 0.09 + wave * 0.22;
        pulseLight.intensity = wave * 45;
        ring.material.opacity = 0.32 + wave * 0.32;
      } else {
        pulseStart = -1;
        world.scale.setScalar(1);
        atmosphere.material.opacity = 0.09;
        pulseLight.intensity = 0;
        ring.material.opacity = 0.32;
      }
    }

    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  }

  requestAnimationFrame(animate);
}
