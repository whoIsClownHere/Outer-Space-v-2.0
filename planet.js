const host = document.getElementById("planet-viewport");

if (host) {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  canvas.tabIndex = 0;
  canvas.setAttribute("aria-label", "Interactive green pixel planet");
  host.appendChild(canvas);

  const signal = document.createElement("div");
  signal.className = "planet-signal";
  signal.textContent = "SIGNAL ACQUIRED";
  host.appendChild(signal);

  const spinButton = document.getElementById("toggleSpin");
  const pulseButton = document.getElementById("pulsePlanet");

  let width = 1;
  let height = 1;
  let rotationX = -0.12;
  let rotationY = 0.2;
  let zoom = 1;
  let autoSpin = true;
  let dragging = false;
  let previousPointer = null;
  let pulseStart = -1;
  let signalTimer;

  const palette = ["#05271a", "#073824", "#0a5030", "#0d6c3d", "#12884a", "#21aa5c", "#39d174", "#78f5a5"];
  const terrain = [];
  const markers = [
    { lat: 0.42, lon: 0.55, label: "SOURCE NODE", color: "#c9ffe0" },
    { lat: -0.12, lon: -1.15, label: "BOSS SIGNAL", color: "#ffe77d" },
    { lat: -0.72, lon: 1.7, label: "LAUNCH POINT", color: "#9dffc5" }
  ];

  function seeded(seed) {
    let value = seed >>> 0;
    return () => {
      value = (value * 1664525 + 1013904223) >>> 0;
      return value / 4294967296;
    };
  }

  const random = seeded(27);
  for (let lat = -Math.PI / 2; lat <= Math.PI / 2; lat += 0.075) {
    for (let lon = -Math.PI; lon < Math.PI; lon += 0.075) {
      const noise =
        Math.sin(lon * 2.5 + Math.sin(lat * 4) * 1.8) * 0.42 +
        Math.sin(lon * 5.2 - lat * 3.3) * 0.22 +
        Math.cos(lon * 8.4 + lat * 2.2) * 0.12 +
        (random() - 0.5) * 0.32 +
        Math.cos(lat) * 0.2;
      terrain.push({ lat, lon, value: noise });
    }
  }

  function showSignal(text) {
    signal.textContent = text;
    signal.classList.add("visible");
    clearTimeout(signalTimer);
    signalTimer = setTimeout(() => signal.classList.remove("visible"), 1200);
  }

  function updateSpinButton() {
    if (!spinButton) return;
    spinButton.textContent = `AUTO SPIN: ${autoSpin ? "ON" : "OFF"}`;
    spinButton.classList.toggle("is-active", autoSpin);
    spinButton.setAttribute("aria-pressed", String(autoSpin));
  }

  function rotatePoint(x, y, z) {
    const cosY = Math.cos(rotationY);
    const sinY = Math.sin(rotationY);
    let rx = x * cosY - z * sinY;
    let rz = x * sinY + z * cosY;

    const cosX = Math.cos(rotationX);
    const sinX = Math.sin(rotationX);
    const ry = y * cosX - rz * sinX;
    rz = y * sinX + rz * cosX;

    return { x: rx, y: ry, z: rz };
  }

  function spherePoint(lat, lon) {
    const cl = Math.cos(lat);
    return rotatePoint(cl * Math.cos(lon), Math.sin(lat), cl * Math.sin(lon));
  }

  function resize() {
    width = Math.max(host.clientWidth, 1);
    height = Math.max(host.clientHeight, 1);
    const scale = width < 500 ? 0.68 : 0.58;
    canvas.width = Math.floor(width * scale);
    canvas.height = Math.floor(height * scale);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.imageSmoothingEnabled = false;
  }

  function drawRing(cx, cy, radius, time, pulse) {
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(-0.28 + Math.sin(time * 0.00015) * 0.03);
    ctx.scale(1, 0.36);
    ctx.strokeStyle = `rgba(109,255,192,${0.36 + pulse * 0.35})`;
    ctx.lineWidth = Math.max(1, radius * 0.018);
    ctx.beginPath();
    ctx.arc(0, 0, radius * 1.42, 0, Math.PI * 2);
    ctx.stroke();
    ctx.strokeStyle = "rgba(78,220,152,0.18)";
    ctx.lineWidth = Math.max(1, radius * 0.008);
    ctx.beginPath();
    ctx.arc(0, 0, radius * 1.58, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }

  function draw(time) {
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    if (autoSpin && !dragging) rotationY += 0.0032;

    let pulse = 0;
    if (pulseStart >= 0) {
      const age = (time - pulseStart) / 1000;
      if (age < 1.2) pulse = Math.sin(age / 1.2 * Math.PI);
      else pulseStart = -1;
    }

    const cx = w * 0.52;
    const cy = h * 0.49;
    const radius = Math.min(w, h) * 0.255 * zoom * (1 + pulse * 0.05);

    const glow = ctx.createRadialGradient(cx, cy, radius * 0.55, cx, cy, radius * 1.65);
    glow.addColorStop(0, `rgba(69,240,141,${0.12 + pulse * 0.12})`);
    glow.addColorStop(0.5, `rgba(31,170,96,${0.08 + pulse * 0.08})`);
    glow.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 1.7, 0, Math.PI * 2);
    ctx.fill();

    drawRing(cx, cy, radius, time, pulse);

    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.clip();

    const base = ctx.createRadialGradient(cx - radius * 0.38, cy - radius * 0.42, radius * 0.08, cx, cy, radius * 1.05);
    base.addColorStop(0, "#8cffb8");
    base.addColorStop(0.28, "#2ac66b");
    base.addColorStop(0.66, "#0b6c3c");
    base.addColorStop(1, "#031c13");
    ctx.fillStyle = base;
    ctx.fillRect(cx - radius, cy - radius, radius * 2, radius * 2);

    const pixel = Math.max(2, Math.round(radius * 0.024));
    terrain
      .map((cell) => ({ ...cell, point: spherePoint(cell.lat, cell.lon) }))
      .filter((cell) => cell.point.z > 0)
      .sort((a, b) => a.point.z - b.point.z)
      .forEach((cell) => {
        const light = Math.max(0, cell.point.x * -0.48 + cell.point.y * 0.42 + cell.point.z * 0.65);
        let index = Math.floor((cell.value + 0.8) * 3.1 + light * 1.6);
        index = Math.max(0, Math.min(palette.length - 1, index));
        ctx.globalAlpha = 0.38 + cell.point.z * 0.62;
        ctx.fillStyle = palette[index];
        ctx.fillRect(
          Math.round((cx + cell.point.x * radius) / pixel) * pixel,
          Math.round((cy - cell.point.y * radius) / pixel) * pixel,
          pixel + 1,
          pixel + 1
        );
      });

    ctx.globalAlpha = 1;
    const shade = ctx.createRadialGradient(cx + radius * 0.58, cy + radius * 0.15, radius * 0.1, cx + radius * 0.38, cy, radius * 1.15);
    shade.addColorStop(0, "rgba(0,0,0,0.58)");
    shade.addColorStop(0.65, "rgba(0,0,0,0.08)");
    shade.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = shade;
    ctx.fillRect(cx - radius, cy - radius, radius * 2, radius * 2);
    ctx.restore();

    ctx.strokeStyle = `rgba(104,255,179,${0.62 + pulse * 0.28})`;
    ctx.lineWidth = Math.max(2, radius * 0.025);
    ctx.beginPath();
    ctx.arc(cx, cy, radius + 1, 0, Math.PI * 2);
    ctx.stroke();

    markers.forEach((marker, index) => {
      const point = spherePoint(marker.lat, marker.lon);
      marker.screen = null;
      if (point.z <= 0) return;
      const x = cx + point.x * radius;
      const y = cy - point.y * radius;
      const markerRadius = Math.max(4, radius * 0.035) * (1 + Math.sin(time * 0.004 + index) * 0.16);
      marker.screen = { x, y, r: markerRadius * 2 };
      ctx.strokeStyle = marker.color;
      ctx.fillStyle = marker.color;
      ctx.globalAlpha = 0.88;
      ctx.lineWidth = Math.max(1, radius * 0.008);
      ctx.beginPath();
      ctx.arc(x, y, markerRadius * 1.9, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillRect(x - markerRadius * 0.35, y - markerRadius * 0.35, markerRadius * 0.7, markerRadius * 0.7);
      ctx.globalAlpha = 1;
    });

    const moonAngle = time * 0.00045;
    const moonX = cx + Math.cos(moonAngle) * radius * 1.72;
    const moonY = cy + Math.sin(moonAngle * 1.35) * radius * 0.32;
    const moonRadius = Math.max(5, radius * 0.095);
    ctx.fillStyle = "#78ef9e";
    ctx.strokeStyle = "rgba(188,255,214,0.85)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(moonX, moonY, moonRadius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    requestAnimationFrame(draw);
  }

  function pointerPosition(event) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (event.clientX - rect.left) * scaleX,
      y: (event.clientY - rect.top) * scaleY
    };
  }

  canvas.addEventListener("pointerdown", (event) => {
    dragging = true;
    previousPointer = { x: event.clientX, y: event.clientY };
    canvas.setPointerCapture(event.pointerId);
  });

  canvas.addEventListener("pointermove", (event) => {
    if (dragging && previousPointer) {
      rotationY += (event.clientX - previousPointer.x) * 0.009;
      rotationX += (event.clientY - previousPointer.y) * 0.006;
      rotationX = Math.max(-1.1, Math.min(1.1, rotationX));
      previousPointer = { x: event.clientX, y: event.clientY };
      return;
    }

    const point = pointerPosition(event);
    const hovering = markers.some((marker) => marker.screen && Math.hypot(point.x - marker.screen.x, point.y - marker.screen.y) < marker.screen.r);
    canvas.style.cursor = hovering ? "pointer" : "grab";
  });

  canvas.addEventListener("pointerup", (event) => {
    const point = pointerPosition(event);
    const hit = markers.find((marker) => marker.screen && Math.hypot(point.x - marker.screen.x, point.y - marker.screen.y) < marker.screen.r);
    dragging = false;
    previousPointer = null;
    canvas.releasePointerCapture(event.pointerId);
    if (hit) showSignal(hit.label);
  });

  canvas.addEventListener("pointercancel", () => {
    dragging = false;
    previousPointer = null;
  });

  canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    zoom *= event.deltaY > 0 ? 0.92 : 1.08;
    zoom = Math.max(0.74, Math.min(1.34, zoom));
  }, { passive: false });

  canvas.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") rotationY -= 0.12;
    if (event.key === "ArrowRight") rotationY += 0.12;
    if (event.key === "ArrowUp") rotationX -= 0.1;
    if (event.key === "ArrowDown") rotationX += 0.1;
    if (event.key === " " || event.key === "Enter") {
      event.preventDefault();
      autoSpin = !autoSpin;
      updateSpinButton();
    }
  });

  spinButton?.addEventListener("click", () => {
    autoSpin = !autoSpin;
    updateSpinButton();
  });

  pulseButton?.addEventListener("click", () => {
    pulseStart = performance.now();
    showSignal("ENERGY PULSE SENT");
  });

  new ResizeObserver(resize).observe(host);
  resize();
  updateSpinButton();
  requestAnimationFrame(draw);
}
