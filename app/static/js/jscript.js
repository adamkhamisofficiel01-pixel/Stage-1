// ── Tab switching (Accueil info tabs) ───────────────────────
function switchTab(event, sectionId) {
  document.querySelectorAll('.content-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
  document.getElementById(sectionId).classList.add('active');
  event.currentTarget.classList.add('active');
}

// ── Tab switching (Documents page) ──────────────────────────
function switchTab1(event, sectionId) {
  document.querySelectorAll('.doc-content-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.doc-tab-btn').forEach(t => t.classList.remove('active'));
  document.getElementById(sectionId).classList.add('active');
  event.currentTarget.classList.add('active');
}

// ── Slideshow (Accueil) ──────────────────────────────────────
const SLIDESHOW_IMAGES = [
  '/static/images/im1.jpg',
  '/static/images/im2.jpeg',
  '/static/images/im3.jpg',
  '/static/images/im4.webp',
];
let currentSlide = 0;

function goToSlide(idx) {
  const slide = document.getElementById('slide');
  const dots = document.querySelectorAll('.slide-dot');
  if (!slide) return;
  slide.style.opacity = '0';
  setTimeout(() => {
    currentSlide = (idx + SLIDESHOW_IMAGES.length) % SLIDESHOW_IMAGES.length;
    slide.src = SLIDESHOW_IMAGES[currentSlide];
    slide.style.opacity = '1';
    dots.forEach((d, i) => d.classList.toggle('active', i === currentSlide));
  }, 300);
}

function initSlideshow() {
  const container = document.querySelector('.slide-controls');
  if (!container) return;
  SLIDESHOW_IMAGES.forEach((_, i) => {
    const dot = document.createElement('div');
    dot.className = 'slide-dot' + (i === 0 ? ' active' : '');
    dot.onclick = () => goToSlide(i);
    container.appendChild(dot);
  });
  setInterval(() => goToSlide(currentSlide + 1), 4000);
}

// ── Toast notifications ──────────────────────────────────────
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';
  toast.className = `toast ${type}`;
  toast.innerHTML = `<i class="fa-solid ${icon}"></i><span></span>`;
  toast.querySelector('span').textContent = message; // textContent avoids HTML injection
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'fadeOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ── Modal helpers ────────────────────────────────────────────
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('open');
}
function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('open');
}

// ── Login page: password visibility toggle ──────────────────
function initPasswordToggle() {
  const toggleBtn = document.getElementById('toggle-pw');
  const pwInput = document.getElementById('password');
  if (toggleBtn && pwInput) {
    toggleBtn.addEventListener('click', () => {
      const isText = pwInput.type === 'text';
      pwInput.type = isText ? 'password' : 'text';
      toggleBtn.querySelector('i').className = `fa-solid ${isText ? 'fa-eye' : 'fa-eye-slash'}`;
    });
  }
}

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initSlideshow();
  initPasswordToggle();
});
