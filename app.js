/* ═══════════════════════════════════════════════════════════════════
   WorldForge AI — Main Frontend JavaScript
   Handles: particles, nav, hero interactions, auth state, toasts
═══════════════════════════════════════════════════════════════════ */

'use strict';

// ── Particle System ──────────────────────────────────────────────────────────
(function initParticles() {
  const canvas = document.getElementById('particles-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, particles = [], animId;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  class Particle {
    constructor() { this.reset(true); }
    reset(init = false) {
      this.x   = Math.random() * W;
      this.y   = init ? Math.random() * H : H + 10;
      this.r   = Math.random() * 1.5 + 0.3;
      this.vx  = (Math.random() - 0.5) * 0.3;
      this.vy  = -(Math.random() * 0.4 + 0.1);
      this.op  = Math.random() * 0.6 + 0.1;
      this.col = Math.random() > 0.6
        ? `rgba(201,162,39,${this.op})`
        : Math.random() > 0.5
          ? `rgba(107,33,168,${this.op})`
          : `rgba(8,145,178,${this.op})`;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      if (this.y < -10) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = this.col;
      ctx.fill();
    }
  }

  function init() {
    resize();
    particles = Array.from({ length: 120 }, () => new Particle());
    loop();
  }

  function loop() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => { p.update(); p.draw(); });
    animId = requestAnimationFrame(loop);
  }

  window.addEventListener('resize', () => { resize(); });
  window.addEventListener('load', init);
})();


// ── Sticky Header ────────────────────────────────────────────────────────────
(function stickyHeader() {
  const header = document.getElementById('main-header');
  if (!header) return;
  window.addEventListener('scroll', () => {
    header.classList.toggle('scrolled', window.scrollY > 40);
  }, { passive: true });
})();


// ── Mobile Hamburger ─────────────────────────────────────────────────────────
(function hamburger() {
  const btn   = document.getElementById('hamburger');
  const links = document.getElementById('nav-links');
  if (!btn || !links) return;
  btn.addEventListener('click', () => links.classList.toggle('open'));
  document.addEventListener('click', e => {
    if (!btn.contains(e.target) && !links.contains(e.target))
      links.classList.remove('open');
  });
})();


// ── Scroll Reveal ────────────────────────────────────────────────────────────
(function scrollReveal() {
  const els = document.querySelectorAll('.feature-card, .pricing-card, .world-gallery-card');
  if (!els.length) return;
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const delay = e.target.dataset.delay || 0;
        setTimeout(() => e.target.style.animationPlayState = 'running', +delay);
        e.target.style.opacity = '1';
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.15 });
  els.forEach(el => {
    el.style.opacity = '0';
    el.style.animationPlayState = 'paused';
    io.observe(el);
  });
})();


// ── Hero Idea Pills ───────────────────────────────────────────────────────────
function setIdea(btn) {
  const inp = document.getElementById('hero-idea');
  if (inp) inp.value = btn.textContent;
}


// ── Quick Generate (hero) ────────────────────────────────────────────────────
async function quickGenerate() {
  const idea = (document.getElementById('hero-idea')?.value || '').trim();
  if (!idea) {
    showToast('✦ Please enter a world idea first!');
    return;
  }
  // Check auth first
  try {
    const r = await fetch('/api/auth/me');
    if (r.ok) {
      // Redirect to dashboard with idea pre-filled
      sessionStorage.setItem('pendingIdea', idea);
      window.location.href = '/dashboard';
    } else {
      openQuickModal();
    }
  } catch {
    openQuickModal();
  }
}

function openQuickModal() {
  const m = document.getElementById('quick-modal');
  if (m) m.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeQuickModal(e) {
  if (e && e.target !== document.getElementById('quick-modal')) return;
  const m = document.getElementById('quick-modal');
  if (m) m.classList.remove('open');
  document.body.style.overflow = '';
}


// ── Toast Notification ───────────────────────────────────────────────────────
function showToast(msg, duration = 3500) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  const t = document.createElement('div');
  t.className = 'toast';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => {
    t.style.animation = 'slideInRight 0.3s ease reverse';
    setTimeout(() => t.remove(), 300);
  }, duration);
}


// ── Auth State (single cached fetch per page load) ───────────────────────────
// One promise shared across all callers — /api/auth/me fires exactly ONCE.
let _authPromise = null;
function getAuthState() {
  if (!_authPromise) {
    _authPromise = fetch('/api/auth/me')
      .then(r => r.ok ? r.json() : { authenticated: false })
      .catch(() => ({ authenticated: false }));
  }
  return _authPromise;
}

// Updates the homepage/auth-page nav when user is already logged in.
// Does NOT redirect — pages handle their own redirect logic.
async function checkAuthState() {
  const d = await getAuthState();
  if (d.authenticated) {
    const cta = document.querySelector('.nav-cta');
    if (cta) {
      const theme = document.documentElement.getAttribute('data-theme') || 'dark';
      const icon  = theme === 'dark' ? '☀' : '🌙';
      const label = theme === 'dark' ? 'Light' : 'Dark';
      cta.innerHTML = `
        <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">
          <span class="toggle-icon">${icon}</span>
          <span class="toggle-label">${label}</span>
        </button>
        <a href="/dashboard" class="btn-ghost">My Worlds</a>
        <button class="btn-primary" onclick="logout()">Logout</button>
      `;
    }
    return d.user;
  }
  return null;
}

// Used by login/signup pages to redirect away if already authenticated.
// Exported so inline scripts can call it without a second fetch.
async function redirectIfAuthenticated(dest) {
  const d = await getAuthState();
  if (d && d.authenticated) window.location.href = dest || '/dashboard';
}

async function logout() {
  await fetch('/api/auth/logout', { method: 'POST' });
  _authPromise = null; // clear cache on logout
  window.location.href = '/';
}

// Only run nav update on pages that have a nav-cta and are NOT auth/dashboard pages
// (those handle their own auth logic via redirectIfAuthenticated / dashboard init)
(function() {
  const path = window.location.pathname;
  const isAuthPage = path === '/login' || path === '/signup';
  const isDashboard = path.startsWith('/dashboard');
  if (!isAuthPage && !isDashboard && document.querySelector('.nav-cta')) {
    checkAuthState();
  }
})();

// ── Theme Toggle ─────────────────────────────────────────────────────────────
(function initTheme() {
  const saved = localStorage.getItem('wf-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);

  function updateToggleLabel() {
    const theme = document.documentElement.getAttribute('data-theme');
    document.querySelectorAll('.theme-toggle').forEach(btn => {
      const icon = btn.querySelector('.toggle-icon');
      const label = btn.querySelector('.toggle-label');
      if (icon) icon.textContent = theme === 'dark' ? '☀' : '🌙';
      if (label) label.textContent = theme === 'dark' ? 'Light' : 'Dark';
    });
  }

  window.toggleTheme = function() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('wf-theme', next);
    updateToggleLabel();
  };

  // Wait for DOM then update labels
  document.addEventListener('DOMContentLoaded', updateToggleLabel);
  if (document.readyState !== 'loading') updateToggleLabel();
})();


window.showToast              = showToast;
window.quickGenerate          = quickGenerate;
window.openQuickModal         = openQuickModal;
window.closeQuickModal        = closeQuickModal;
window.setIdea                = setIdea;
window.logout                 = logout;
window.getAuthState           = getAuthState;
window.redirectIfAuthenticated = redirectIfAuthenticated;
window.clearAuthCache         = function() { _authPromise = null; };
window.toggleTheme = window.toggleTheme || function(){};
