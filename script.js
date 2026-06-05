const canvas = document.getElementById("stars");
const ctx = canvas.getContext("2d");

let stars = [];
let w = 0;
let h = 0;

function resizeCanvas() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  w = window.innerWidth;
  h = window.innerHeight;

  canvas.width = Math.floor(w * dpr);
  canvas.height = Math.floor(h * dpr);
  canvas.style.width = `${w}px`;
  canvas.style.height = `${h}px`;

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const count = Math.floor((w * h) / 9000);
  stars = [];

  for (let i = 0; i < count; i++) {
    stars.push({
      x: Math.floor(Math.random() * w),
      y: Math.floor(Math.random() * h),
      size: Math.random() > 0.85 ? 4 : 2,
      speed: Math.random() > 0.85 ? 0.35 : 0.15
    });
  }
}

function draw() {
  ctx.clearRect(0, 0, w, h);

  for (const star of stars) {
    ctx.fillStyle = "#dce8ff";
    ctx.fillRect(Math.round(star.x), Math.round(star.y), star.size, star.size);

    star.y += star.speed;

    if (star.y > h) {
      star.y = -4;
      star.x = Math.floor(Math.random() * w);
    }
  }

  requestAnimationFrame(draw);
}

window.addEventListener("resize", resizeCanvas);

resizeCanvas();
draw();
