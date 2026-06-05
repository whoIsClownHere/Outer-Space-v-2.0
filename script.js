const canvas = document.getElementById('stars');
const ctx = canvas.getContext('2d');
const header = document.querySelector('.header');
const menuButton = document.querySelector('.menu-button');
const nav = document.querySelector('.nav');
const year = document.getElementById('year');

let stars = [];
let width = 0;
let height = 0;
let mouseX = 0;
let mouseY = 0;

function resizeCanvas() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  width = window.innerWidth;
  height = window.innerHeight;
  canvas.width = Math.floor(width * dpr);
  canvas.height = Math.floor(height * dpr);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const starCount = Math.max(90, Math.floor((width * height) / 9500));
  stars = Array.from({ length: starCount }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    radius: Math.random() * 1.25 + 0.15,
    speed: Math.random() * 0.13 + 0.025,
    alpha: Math.random() * 0.65 + 0.2,
  }));
}

function drawStars() {
  ctx.clearRect(0, 0, width, height);

  for (const star of stars) {
    star.y += star.speed;
    if (star.y > height + 2) {
      star.y = -2;
      star.x = Math.random() * width;
    }

    const parallaxX = (mouseX - width / 2) * star.speed * 0.018;
    const parallaxY = (mouseY - height / 2) * star.speed * 0.018;

    ctx.beginPath();
    ctx.arc(star.x + parallaxX, star.y + parallaxY, star.radius, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255,255,255,${star.alpha})`;
    ctx.fill();
  }

  requestAnimationFrame(drawStars);
}

window.addEventListener('resize', resizeCanvas);
window.addEventListener('pointermove', (event) => {
  mouseX = event.clientX;
  mouseY = event.clientY;
});

window.addEventListener('scroll', () => {
  header.classList.toggle('scrolled', window.scrollY > 30);
});

menuButton.addEventListener('click', () => {
  const isOpen = nav.classList.toggle('open');
  menuButton.setAttribute('aria-expanded', String(isOpen));
  document.body.style.overflow = isOpen ? 'hidden' : '';
});

document.querySelectorAll('.nav a').forEach((link) => {
  link.addEventListener('click', () => {
    nav.classList.remove('open');
    menuButton.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  });
});

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal').forEach((element, index) => {
  element.style.transitionDelay = `${Math.min(index % 3, 2) * 90}ms`;
  revealObserver.observe(element);
});

const counter = document.querySelector('[data-counter]');
if (counter) {
  const counterObserver = new IntersectionObserver(([entry]) => {
    if (!entry.isIntersecting) return;

    const target = Number(counter.dataset.counter);
    const duration = 1000;
    const startTime = performance.now();

    function updateCounter(time) {
      const progress = Math.min((time - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      counter.textContent = Math.round(target * eased);
      if (progress < 1) requestAnimationFrame(updateCounter);
    }

    requestAnimationFrame(updateCounter);
    counterObserver.disconnect();
  }, { threshold: 0.5 });

  counterObserver.observe(counter);
}

year.textContent = new Date().getFullYear();
resizeCanvas();
drawStars();
