const canvas = document.getElementById('stars');
const ctx = canvas.getContext('2d');
const menuToggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.nav');
const year = document.getElementById('year');

let stars = [];
let width = 0;
let height = 0;

function resizeCanvas() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  width = window.innerWidth;
  height = window.innerHeight;
  canvas.width = Math.floor(width * dpr);
  canvas.height = Math.floor(height * dpr);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const count = Math.max(90, Math.floor((width * height) / 8500));
  stars = Array.from({ length: count }, () => ({
    x: Math.floor(Math.random() * width),
    y: Math.floor(Math.random() * height),
    size: Math.random() > 0.9 ? 3 : 1,
    speed: Math.random() * 0.3 + 0.05,
    alpha: Math.random() * 0.65 + 0.25,
    cyan: Math.random() > 0.72,
  }));
}

function drawStars() {
  ctx.clearRect(0, 0, width, height);

  for (const star of stars) {
    star.y += star.speed;
    if (star.y > height + 4) {
      star.y = -4;
      star.x = Math.floor(Math.random() * width);
    }

    ctx.fillStyle = star.cyan
      ? `rgba(95,227,232,${star.alpha})`
      : `rgba(232,248,244,${star.alpha})`;
    ctx.fillRect(Math.round(star.x), Math.round(star.y), star.size, star.size);

    if (star.size === 3) {
      ctx.fillRect(Math.round(star.x - 2), Math.round(star.y + 1), 7, 1);
      ctx.fillRect(Math.round(star.x + 1), Math.round(star.y - 2), 1, 7);
    }
  }

  requestAnimationFrame(drawStars);
}

menuToggle?.addEventListener('click', () => {
  const isOpen = nav.classList.toggle('open');
  menuToggle.setAttribute('aria-expanded', String(isOpen));
});

document.querySelectorAll('.nav a').forEach((link) => {
  link.addEventListener('click', () => {
    nav.classList.remove('open');
    menuToggle?.setAttribute('aria-expanded', 'false');
  });
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    entry.target.classList.add('visible');
    observer.unobserve(entry.target);
  });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal').forEach((element, index) => {
  element.style.transitionDelay = `${Math.min(index % 3, 2) * 80}ms`;
  observer.observe(element);
});

document.querySelectorAll('[data-copy]').forEach((button) => {
  button.addEventListener('click', async () => {
    const original = button.textContent;
    try {
      await navigator.clipboard.writeText(button.dataset.copy);
      button.textContent = 'COPIED';
    } catch {
      button.textContent = 'SELECT CODE';
    }
    setTimeout(() => { button.textContent = original; }, 1600);
  });
});

year.textContent = new Date().getFullYear();
window.addEventListener('resize', resizeCanvas);
resizeCanvas();
drawStars();
