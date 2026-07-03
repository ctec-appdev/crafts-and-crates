/* Crafts & Crates ATL — main.js */
(function () {
  'use strict';

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Single document-level mouseup handler; carousels register callbacks here.
  var _dragCallbacks = [];
  document.addEventListener('mouseup', function (e) {
    _dragCallbacks.forEach(function (cb) { cb(e); });
  });

  /* -------------------------------------------------------
     MOBILE MENU
  ------------------------------------------------------- */
  function initMobileMenu() {
    const btn = document.querySelector('.hamburger');
    const wrapper = document.querySelector('.nav-wrapper');
    if (!btn || !wrapper) return;

    btn.addEventListener('click', function () {
      const open = wrapper.classList.toggle('open');
      btn.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open);
    });

    // Close on outside click
    document.addEventListener('click', function (e) {
      if (!btn.contains(e.target) && !wrapper.contains(e.target)) {
        wrapper.classList.remove('open');
        btn.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* -------------------------------------------------------
     ACTIVE NAV LINK
  ------------------------------------------------------- */
  function markActiveNav() {
    const path = location.pathname;
    document.querySelectorAll('.site-nav a').forEach(function (a) {
      const href = a.getAttribute('href');
      if (!href) return;
      // Resolve relative href against current document
      const abs = new URL(href, location.href).pathname;
      if (abs === path || (path.endsWith('/') && abs === path.slice(0, -1))) {
        a.classList.add('active');
      }
    });
  }

  /* -------------------------------------------------------
     CAROUSEL
  ------------------------------------------------------- */
  function initCarousel(el) {
    const track = el.querySelector('.carousel-track');
    const slides = el.querySelectorAll('.carousel-slide');
    const prevBtn = el.querySelector('.carousel-btn--prev');
    const nextBtn = el.querySelector('.carousel-btn--next');
    const dotsWrap = el.querySelector('.carousel-dots');
    const autoplay = el.dataset.autoplay !== 'false';
    const interval = parseInt(el.dataset.interval || '4500', 10);
    let current = 0;
    let timer = null;
    let startX = 0;
    let isDragging = false;

    if (!track || slides.length === 0) return;

    // Create dots
    if (dotsWrap) {
      slides.forEach(function (_, i) {
        const dot = document.createElement('button');
        dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
        dot.setAttribute('aria-label', 'Slide ' + (i + 1));
        dot.addEventListener('click', function () { goTo(i); resetTimer(); });
        dotsWrap.appendChild(dot);
      });
    }

    function goTo(idx) {
      current = ((idx % slides.length) + slides.length) % slides.length;
      track.style.transform = 'translateX(-' + (current * 100) + '%)';
      if (dotsWrap) {
        dotsWrap.querySelectorAll('.carousel-dot').forEach(function (d, i) {
          d.classList.toggle('active', i === current);
        });
      }
    }

    function next() { goTo(current + 1); }
    function prev() { goTo(current - 1); }

    if (prevBtn) prevBtn.addEventListener('click', function () { prev(); resetTimer(); });
    if (nextBtn) nextBtn.addEventListener('click', function () { next(); resetTimer(); });

    // Swipe / drag
    track.addEventListener('touchstart', function (e) {
      startX = e.touches[0].clientX;
    }, { passive: true });
    track.addEventListener('touchend', function (e) {
      const dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 40) { dx < 0 ? next() : prev(); resetTimer(); }
    }, { passive: true });
    track.addEventListener('mousedown', function (e) {
      startX = e.clientX;
      isDragging = true;
    });
    _dragCallbacks.push(function (e) {
      if (!isDragging) return;
      isDragging = false;
      const dx = e.clientX - startX;
      if (Math.abs(dx) > 40) { dx < 0 ? next() : prev(); resetTimer(); }
    });

    // Autoplay
    function startTimer() {
      if (!autoplay || reducedMotion) return;
      timer = setInterval(next, interval);
    }
    function resetTimer() {
      clearInterval(timer);
      startTimer();
    }

    el.addEventListener('mouseenter', function () { clearInterval(timer); });
    el.addEventListener('mouseleave', startTimer);

    startTimer();
  }

  function initCarousels() {
    document.querySelectorAll('.carousel-wrap').forEach(initCarousel);
  }

  /* -------------------------------------------------------
     SCROLL REVEAL
  ------------------------------------------------------- */
  function initScrollReveal() {
    if (reducedMotion) return;

    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.reveal, .stagger').forEach(function (el) {
      observer.observe(el);
    });
  }

  /* -------------------------------------------------------
     LIGHTBOX
  ------------------------------------------------------- */
  (function () {
    let images = [];
    let currentIdx = 0;
    let lb, lbImg, lbClose, lbPrev, lbNext, lbCounter;
    let startX = 0;
    let triggerEl = null;

    // Focusable elements inside the lightbox (order matches DOM order).
    function getFocusables() {
      return [lbClose, lbPrev, lbNext].filter(Boolean);
    }

    function buildLightbox() {
      if (document.querySelector('.lightbox')) return;
      lb = document.createElement('div');
      lb.className = 'lightbox';
      lb.setAttribute('role', 'dialog');
      lb.setAttribute('aria-modal', 'true');
      lb.setAttribute('aria-label', 'Image viewer');

      lbClose = document.createElement('button');
      lbClose.className = 'lightbox-close';
      lbClose.innerHTML = '&times;';
      lbClose.setAttribute('aria-label', 'Close');

      lbPrev = document.createElement('button');
      lbPrev.className = 'lightbox-btn lightbox-prev';
      lbPrev.setAttribute('aria-label', 'Previous image');
      lbPrev.innerHTML = '<svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>';

      lbNext = document.createElement('button');
      lbNext.className = 'lightbox-btn lightbox-next';
      lbNext.setAttribute('aria-label', 'Next image');
      lbNext.innerHTML = '<svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>';

      const inner = document.createElement('div');
      inner.className = 'lightbox-inner';
      lbImg = document.createElement('img');
      lbImg.className = 'lightbox-img';
      lbImg.alt = '';
      inner.appendChild(lbImg);

      lbCounter = document.createElement('div');
      lbCounter.className = 'lightbox-counter';

      lb.appendChild(lbClose);
      lb.appendChild(lbPrev);
      lb.appendChild(lbNext);
      lb.appendChild(inner);
      lb.appendChild(lbCounter);
      document.body.appendChild(lb);

      lbClose.addEventListener('click', close);
      lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
      lbPrev.addEventListener('click', function () { show(currentIdx - 1); });
      lbNext.addEventListener('click', function () { show(currentIdx + 1); });

      // Keyboard: navigation + focus trap
      document.addEventListener('keydown', function (e) {
        if (!lb.classList.contains('open')) return;
        if (e.key === 'Escape') { close(); return; }
        if (e.key === 'ArrowLeft') { show(currentIdx - 1); return; }
        if (e.key === 'ArrowRight') { show(currentIdx + 1); return; }
        if (e.key === 'Tab') {
          const focusables = getFocusables();
          if (!focusables.length) return;
          const first = focusables[0];
          const last = focusables[focusables.length - 1];
          if (e.shiftKey) {
            if (document.activeElement === first) { e.preventDefault(); last.focus(); }
          } else {
            if (document.activeElement === last) { e.preventDefault(); first.focus(); }
          }
        }
      });

      // Swipe
      lb.addEventListener('touchstart', function (e) { startX = e.touches[0].clientX; }, { passive: true });
      lb.addEventListener('touchend', function (e) {
        const dx = e.changedTouches[0].clientX - startX;
        if (Math.abs(dx) > 50) { dx < 0 ? show(currentIdx + 1) : show(currentIdx - 1); }
      }, { passive: true });
    }

    function open(idx, imgs, trigger) {
      triggerEl = trigger || null;
      images = imgs;
      show(idx);
      lb.classList.add('open');
      document.body.style.overflow = 'hidden';
      lbClose.focus();
    }

    function close() {
      lb.classList.remove('open');
      document.body.style.overflow = '';
      if (triggerEl) { triggerEl.focus(); triggerEl = null; }
    }

    function show(idx) {
      currentIdx = ((idx % images.length) + images.length) % images.length;
      lbImg.src = images[currentIdx].src;
      lbImg.alt = images[currentIdx].alt || '';
      if (lbCounter) lbCounter.textContent = (currentIdx + 1) + ' / ' + images.length;
    }

    function initGalleries() {
      buildLightbox();
      document.querySelectorAll('.gallery-item').forEach(function (item) {
        const img = item.querySelector('img');
        if (!img) return;
        item.addEventListener('click', function () {
          // Collect all images from the same gallery container
          const gallery = item.closest('.gallery-grid, .post-gallery');
          let imgs;
          if (gallery) {
            imgs = Array.from(gallery.querySelectorAll('.gallery-item img')).map(function (i) {
              return { src: i.src, alt: i.alt };
            });
          } else {
            imgs = [{ src: img.src, alt: img.alt }];
          }
          const idx = gallery
            ? Array.from(gallery.querySelectorAll('.gallery-item')).indexOf(item)
            : 0;
          open(idx, imgs, item);
        });
      });
    }

    window.__initGalleries = initGalleries;
  })();

  /* -------------------------------------------------------
     INIT
  ------------------------------------------------------- */
  document.addEventListener('DOMContentLoaded', function () {
    initMobileMenu();
    markActiveNav();
    initCarousels();
    initScrollReveal();
    if (window.__initGalleries) window.__initGalleries();
  });
})();
