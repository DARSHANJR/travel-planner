/* ═══════════════════════════════════════════════
   WANDERLUST — app.js  (fully fixed wishlist)
   ═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ─── MOBILE MENU ────────────────────────────
  const mobileBtn  = document.getElementById('mobileMenuBtn');
  const mobileMenu = document.getElementById('mobileMenu');
  if (mobileBtn && mobileMenu) {
    mobileBtn.addEventListener('click', () => {
      mobileMenu.classList.toggle('open');
      const icon = mobileBtn.querySelector('i');
      icon.className = mobileMenu.classList.contains('open')
        ? 'fa-solid fa-xmark' : 'fa-solid fa-bars';
    });
  }

  // ─── NAV DROPDOWN (click toggle) ────────────
  const avatarBtn    = document.getElementById('navAvatarBtn');
  const dropdownMenu = document.getElementById('navDropdownMenu');

  if (avatarBtn && dropdownMenu) {
    // Open/close on click
    avatarBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = dropdownMenu.classList.contains('open');
      dropdownMenu.classList.toggle('open', !isOpen);
      avatarBtn.classList.toggle('open', !isOpen);
      avatarBtn.setAttribute('aria-expanded', !isOpen);
    });

    // Close when clicking anywhere else
    document.addEventListener('click', (e) => {
      if (!avatarBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.remove('open');
        avatarBtn.classList.remove('open');
        avatarBtn.setAttribute('aria-expanded', 'false');
      }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        dropdownMenu.classList.remove('open');
        avatarBtn.classList.remove('open');
        avatarBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // ─── FLASH AUTO-DISMISS ──────────────────────
  document.querySelectorAll('.flash').forEach(flash => {
    setTimeout(() => {
      flash.style.transition = 'all .3s';
      flash.style.opacity    = '0';
      flash.style.transform  = 'translateX(20px)';
      setTimeout(() => flash.remove(), 300);
    }, 4000);
  });

  // ─── TOAST ──────────────────────────────────
  window.showToast = function(msg, type = 'info') {
    const icons = { success:'fa-circle-check', danger:'fa-circle-xmark',
                    info:'fa-circle-info', warning:'fa-triangle-exclamation' };
    const toast = document.createElement('div');
    toast.className = `flash flash-${type}`;
    toast.innerHTML = `<i class="fa-solid ${icons[type]||icons.info}"></i>${msg}
      <button onclick="this.parentElement.remove()" class="flash-close">&times;</button>`;
    let box = document.querySelector('.flash-container');
    if (!box) {
      box = document.createElement('div');
      box.className = 'flash-container';
      document.body.appendChild(box);
    }
    box.appendChild(toast);
    setTimeout(() => {
      toast.style.transition = 'all .3s';
      toast.style.opacity    = '0';
      toast.style.transform  = 'translateX(20px)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  };

  // ═══════════════════════════════════════════
  //  WISHLIST — single unified handler
  //  Covers: .wishlist-btn  AND  .btn-wishlist-big
  // ═══════════════════════════════════════════
  async function doWishlistToggle(destId, btn) {
    if (btn.dataset.loading === '1') return;
    btn.dataset.loading = '1';

    const icon       = btn.querySelector('i');
    const textEl     = btn.querySelector('span');          // only on detail page big btn
    const wasActive  = btn.classList.contains('wishlisted');
    const card       = btn.closest('.dest-card');
    const onWishPage = window.location.pathname === '/wishlist';

    // ── Optimistic UI ──
    btn.classList.toggle('wishlisted', !wasActive);
    if (icon) icon.className = wasActive ? 'fa-regular fa-heart' : 'fa-solid fa-heart';
    if (textEl) textEl.textContent = wasActive ? 'Save to Wishlist' : 'Saved to Wishlist';

    try {
      const res = await fetch(`/wishlist/toggle/${destId}`, {
        method:  'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest',
                   'Accept':           'application/json' }
      });

      // Not logged in → 401 JSON
      if (res.status === 401) {
        // revert
        btn.classList.toggle('wishlisted', wasActive);
        if (icon)   icon.className  = wasActive ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
        if (textEl) textEl.textContent = wasActive ? 'Saved to Wishlist' : 'Save to Wishlist';
        showToast('Please sign in to use the wishlist', 'warning');
        setTimeout(() => window.location.href = '/login', 1800);
        return;
      }

      // Parse JSON safely
      let data;
      try { data = await res.json(); }
      catch(e) {
        // Got non-JSON (unexpected) — revert
        btn.classList.toggle('wishlisted', wasActive);
        if (icon)   icon.className  = wasActive ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
        if (textEl) textEl.textContent = wasActive ? 'Saved to Wishlist' : 'Save to Wishlist';
        showToast('Something went wrong. Please try again.', 'danger');
        return;
      }

      if (data.status === 'added') {
        btn.classList.add('wishlisted');
        if (icon)   icon.className  = 'fa-solid fa-heart';
        if (textEl) textEl.textContent = 'Saved to Wishlist';
        showToast(`❤️ Added to wishlist!`, 'success');

      } else if (data.status === 'removed') {
        btn.classList.remove('wishlisted');
        if (icon)   icon.className  = 'fa-regular fa-heart';
        if (textEl) textEl.textContent = 'Save to Wishlist';
        showToast('Removed from wishlist', 'info');

        // On wishlist page → animate card out
        if (card && onWishPage) {
          card.style.transition = 'opacity .3s, transform .3s';
          card.style.opacity    = '0';
          card.style.transform  = 'scale(0.92)';
          setTimeout(() => {
            card.remove();
            if (!document.querySelector('.dest-card')) {
              const grid = document.getElementById('wishlistGrid');
              if (grid) grid.remove();
              const cont = document.querySelector('.wishlist-page');
              if (cont) cont.innerHTML = `
                <div class="empty-state large">
                  <div class="empty-state-icon"><i class="fa-regular fa-heart"></i></div>
                  <h2>Your wishlist is empty</h2>
                  <p>Browse destinations and tap the heart icon to save places here.</p>
                  <a href="/destinations" class="btn-primary">
                    <i class="fa-solid fa-compass"></i> Explore Destinations
                  </a>
                </div>`;
            }
          }, 320);
        }
      }

    } catch(err) {
      // Network error — revert optimistic change
      btn.classList.toggle('wishlisted', wasActive);
      if (icon)   icon.className  = wasActive ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
      if (textEl) textEl.textContent = wasActive ? 'Saved to Wishlist' : 'Save to Wishlist';
      showToast('Network error. Check connection and try again.', 'danger');
      console.error('Wishlist error:', err);
    } finally {
      delete btn.dataset.loading;
    }
  }

  // Attach to .wishlist-btn (cards on index / destinations / wishlist)
  document.querySelectorAll('.wishlist-btn[data-id]').forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      doWishlistToggle(btn.dataset.id, btn);
    });
  });

  // Attach to .btn-wishlist-big (detail page sidebar button)
  document.querySelectorAll('.btn-wishlist-big[data-id]').forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      doWishlistToggle(btn.dataset.id, btn);
    });
  });

  // ─── SCROLL ANIMATION ───────────────────────
  const obs = new IntersectionObserver(entries => {
    entries.forEach(en => {
      if (en.isIntersecting) {
        en.target.style.opacity   = '1';
        en.target.style.transform = 'translateY(0)';
        obs.unobserve(en.target);
      }
    });
  }, { threshold: 0.08 });

  document.querySelectorAll('.dest-card, .trip-card').forEach((card, i) => {
    card.style.opacity    = '0';
    card.style.transform  = 'translateY(24px)';
    card.style.transition = `opacity .4s ease ${i * 0.05}s, transform .4s ease ${i * 0.05}s`;
    obs.observe(card);
  });

  // ─── PLANNER DATE VALIDATION ─────────────────
  const startDate = document.querySelector('input[name="start_date"]');
  const endDate   = document.querySelector('input[name="end_date"]');
  if (startDate && endDate) {
    startDate.min = new Date().toISOString().split('T')[0];
    startDate.addEventListener('change', () => {
      endDate.min = startDate.value;
      if (endDate.value && endDate.value < startDate.value) endDate.value = startDate.value;
    });
  }

  // ─── IMAGE FALLBACK ──────────────────────────
  const FALLBACK = 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&q=80&auto=format&fit=crop';
  document.querySelectorAll('img').forEach(img => {
    img.addEventListener('error', function () {
      if (this.src !== FALLBACK) { this.onerror = null; this.src = FALLBACK; }
    });
  });

  // ─── HERO SEARCH PLACEHOLDER ─────────────────
  const searchInput = document.querySelector('.hero-search input');
  if (searchInput) {
    const ph = ['Where do you want to go? Try "Goa"...','Search "Manali" for mountains...',
                 'Try "Kerala" for backwaters...','Search "historical" places...','Try "beach" escapes...'];
    let pi = 0;
    setInterval(() => { pi = (pi+1)%ph.length; searchInput.placeholder = ph[pi]; }, 3000);
  }

  // ─── ADMIN CHECKBOX CARDS ────────────────────
  document.querySelectorAll('.checkbox-card input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', function () {
      this.closest('.checkbox-card').classList.toggle('checked', this.checked);
    });
  });

  // ─── ITINERARY DURATION +/- BUTTONS ─────────
  document.querySelectorAll('.duration-form').forEach(form => {
    const input = form.querySelector('.dur-input');
    form.querySelector('.minus')?.addEventListener('click', () => {
      input.value = Math.max(1, parseInt(input.value) - 1);
    });
    form.querySelector('.plus')?.addEventListener('click', () => {
      input.value = Math.min(30, parseInt(input.value) + 1);
    });
  });

});
