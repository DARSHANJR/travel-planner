/* ═══════════════════════════════════════════════
   WANDERLUST — app.js
   ═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ─── MOBILE MENU ──────────────────────────────
  const mobileBtn = document.getElementById('mobileMenuBtn');
  const mobileMenu = document.getElementById('mobileMenu');
  if (mobileBtn && mobileMenu) {
    mobileBtn.addEventListener('click', () => {
      mobileMenu.classList.toggle('open');
      const icon = mobileBtn.querySelector('i');
      icon.className = mobileMenu.classList.contains('open') ? 'fa-solid fa-xmark' : 'fa-solid fa-bars';
    });
  }

  // ─── AUTO-DISMISS FLASH MESSAGES ──────────────
  document.querySelectorAll('.flash').forEach(flash => {
    setTimeout(() => {
      flash.style.opacity = '0';
      flash.style.transform = 'translateX(20px)';
      flash.style.transition = 'all .3s';
      setTimeout(() => flash.remove(), 300);
    }, 4000);
  });

  // ─── WISHLIST TOGGLE (cards on listing pages) ──
  document.querySelectorAll('.wishlist-btn[data-id]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const id = btn.dataset.id;
      try {
        const res = await fetch(`/wishlist/toggle/${id}`, { method: 'POST' });
        const data = await res.json();
        const icon = btn.querySelector('i');
        if (data.status === 'added') {
          btn.classList.add('wishlisted');
          icon.className = 'fa-solid fa-heart';
          showToast('Added to wishlist!', 'success');
        } else {
          btn.classList.remove('wishlisted');
          icon.className = 'fa-regular fa-heart';
          showToast('Removed from wishlist', 'info');
        }
      } catch (err) {
        showToast('Please sign in to use wishlist', 'warning');
      }
    });
  });

  // ─── TOAST NOTIFICATION ───────────────────────
  window.showToast = function(message, type = 'info') {
    const icons = { success: 'fa-circle-check', danger: 'fa-circle-xmark', info: 'fa-circle-info', warning: 'fa-triangle-exclamation' };
    const toast = document.createElement('div');
    toast.className = `flash flash-${type}`;
    toast.innerHTML = `<i class="fa-solid ${icons[type] || icons.info}"></i>${message}<button onclick="this.parentElement.remove()" class="flash-close">&times;</button>`;
    let container = document.querySelector('.flash-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'flash-container';
      document.body.appendChild(container);
    }
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      toast.style.transition = 'all .3s';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  };

  // ─── CARD ANIMATION ON SCROLL ─────────────────
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.dest-card, .trip-card').forEach((card, i) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = `opacity .4s ease ${i * 0.05}s, transform .4s ease ${i * 0.05}s`;
    observer.observe(card);
  });

  // ─── DATE VALIDATION IN PLANNER ───────────────
  const startDate = document.querySelector('input[name="start_date"]');
  const endDate = document.querySelector('input[name="end_date"]');
  if (startDate && endDate) {
    const today = new Date().toISOString().split('T')[0];
    startDate.min = today;
    startDate.addEventListener('change', () => {
      endDate.min = startDate.value;
      if (endDate.value && endDate.value < startDate.value) {
        endDate.value = startDate.value;
      }
    });
  }

  // ─── SMOOTH SCROLL ────────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ─── IMAGE LAZY LOAD FALLBACK ──────────────────
  document.querySelectorAll('img[loading="lazy"]').forEach(img => {
    img.addEventListener('error', () => {
      img.src = 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&q=60';
    });
  });

  // ─── CONFIRM DELETE ───────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm(btn.dataset.confirm)) e.preventDefault();
    });
  });

  // ─── HERO SEARCH PLACEHOLDER CYCLE ───────────
  const searchInput = document.querySelector('.hero-search input');
  if (searchInput) {
    const placeholders = [
      'Where do you want to go? Try "Goa"...',
      'Search "Manali" for mountain trips...',
      'Try "Kerala" for backwater bliss...',
      'Search "historical" for heritage tours...',
      'Try "beach" for coastal escapes...'
    ];
    let pi = 0;
    setInterval(() => {
      pi = (pi + 1) % placeholders.length;
      searchInput.setAttribute('placeholder', placeholders[pi]);
    }, 3000);
  }

});
  // ─── IMAGE ERROR FALLBACK (all images) ────────────────────────────────────────────────
  const FALLBACK_IMG = 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&q=80&auto=format&fit=crop';
  document.querySelectorAll('img').forEach(img => {
    if (!img.getAttribute('onerror')) {
      img.addEventListener('error', function() {
        if (this.src !== FALLBACK_IMG) {
          this.onerror = null;
          this.src = FALLBACK_IMG;
        }
      });
    }
  });

});