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
     SCROLL PROGRESS BAR
  ------------------------------------------------------- */
  function initScrollProgress() {
    var bar = document.createElement('div');
    bar.className = 'scroll-progress';
    bar.setAttribute('aria-hidden', 'true');
    document.body.appendChild(bar);

    function update() {
      var scrollTop = window.scrollY || document.documentElement.scrollTop;
      var docHeight = document.documentElement.scrollHeight - window.innerHeight;
      var pct = docHeight > 0 ? (scrollTop / docHeight) : 0;
      bar.style.transform = 'scaleX(' + pct + ')';
    }
    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  /* -------------------------------------------------------
     HEADER SCROLL STATE
  ------------------------------------------------------- */
  function initHeaderScroll() {
    var header = document.querySelector('.site-header');
    if (!header) return;

    function update() {
      header.classList.toggle('scrolled', window.scrollY > 40);
    }
    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  /* -------------------------------------------------------
     BACK TO TOP BUTTON
  ------------------------------------------------------- */
  function initBackToTop() {
    var btn = document.createElement('button');
    btn.className = 'back-to-top';
    btn.setAttribute('aria-label', 'Back to top');
    btn.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><polyline points="18 15 12 9 6 15"/></svg>';
    document.body.appendChild(btn);

    window.addEventListener('scroll', function () {
      btn.classList.toggle('visible', window.scrollY > 500);
    }, { passive: true });

    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* -------------------------------------------------------
     BUTTON RIPPLE EFFECT
  ------------------------------------------------------- */
  function initButtonRipple() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.btn');
      if (!btn || reducedMotion) return;

      var rect = btn.getBoundingClientRect();
      var size = Math.max(rect.width, rect.height) * 2;
      var x = e.clientX - rect.left - size / 2;
      var y = e.clientY - rect.top - size / 2;

      var ripple = document.createElement('span');
      ripple.className = 'ripple';
      ripple.style.cssText = 'width:' + size + 'px;height:' + size + 'px;left:' + x + 'px;top:' + y + 'px;';
      btn.appendChild(ripple);
      ripple.addEventListener('animationend', function () { ripple.remove(); });
    });
  }

  /* -------------------------------------------------------
     MOBILE MENU
  ------------------------------------------------------- */
  function initMobileMenu() {
    var btn = document.querySelector('.hamburger');
    var wrapper = document.querySelector('.nav-wrapper');
    if (!btn || !wrapper) return;

    btn.addEventListener('click', function () {
      var open = wrapper.classList.toggle('open');
      btn.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open);
    });

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
    var path = location.pathname;
    document.querySelectorAll('.site-nav a').forEach(function (a) {
      var href = a.getAttribute('href');
      if (!href) return;
      var abs = new URL(href, location.href).pathname;
      if (abs === path || (path.endsWith('/') && abs === path.slice(0, -1))) {
        a.classList.add('active');
      }
    });
  }

  /* -------------------------------------------------------
     CAROUSEL
  ------------------------------------------------------- */
  function initCarousel(el) {
    var track = el.querySelector('.carousel-track');
    var slides = el.querySelectorAll('.carousel-slide');
    var prevBtn = el.querySelector('.carousel-btn--prev');
    var nextBtn = el.querySelector('.carousel-btn--next');
    var dotsWrap = el.querySelector('.carousel-dots');
    var autoplay = el.dataset.autoplay !== 'false';
    var interval = parseInt(el.dataset.interval || '4500', 10);
    var current = 0;
    var timer = null;
    var startX = 0;
    var isDragging = false;

    if (!track || slides.length === 0) return;

    if (dotsWrap) {
      slides.forEach(function (_, i) {
        var dot = document.createElement('button');
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

    track.addEventListener('touchstart', function (e) {
      startX = e.touches[0].clientX;
    }, { passive: true });
    track.addEventListener('touchend', function (e) {
      var dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 40) { dx < 0 ? next() : prev(); resetTimer(); }
    }, { passive: true });
    track.addEventListener('mousedown', function (e) {
      startX = e.clientX;
      isDragging = true;
    });
    _dragCallbacks.push(function (e) {
      if (!isDragging) return;
      isDragging = false;
      var dx = e.clientX - startX;
      if (Math.abs(dx) > 40) { dx < 0 ? next() : prev(); resetTimer(); }
    });

    function startTimer() {
      if (!autoplay || reducedMotion) return;
      timer = setInterval(next, interval);
    }
    function resetTimer() { clearInterval(timer); startTimer(); }

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
    if (reducedMotion) {
      document.querySelectorAll('.reveal, .stagger').forEach(function (el) {
        el.classList.add('visible');
      });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.reveal, .stagger').forEach(function (el) {
      observer.observe(el);
    });
  }

  /* -------------------------------------------------------
     HERO PARALLAX (subtle)
  ------------------------------------------------------- */
  function initHeroParallax() {
    if (reducedMotion) return;
    var heroBg = document.querySelector('.hero-bg');
    var homepageHero = document.querySelector('.hero--split.instagram-band');
    if (!heroBg && !homepageHero) return;

    window.addEventListener('scroll', function () {
      var scrollY = window.scrollY;
      if (heroBg) {
        var heroEl = heroBg.closest('.hero');
        if (heroEl) {
          var heroH = heroEl.offsetHeight;
          if (scrollY <= heroH) {
            var pct = scrollY / heroH;
            heroBg.style.transform = 'scale(1.08) translateY(' + (pct * 30) + 'px)';
          }
        }
      }
      if (homepageHero) {
        var heroTop = homepageHero.getBoundingClientRect().top + scrollY;
        var offset = Math.max(0, Math.min(120, (scrollY - heroTop) * 0.2));
        homepageHero.style.setProperty('--hero-parallax-offset', offset + 'px');
      }
    }, { passive: true });
  }

  /* -------------------------------------------------------
     LIGHTBOX
  ------------------------------------------------------- */
  (function () {
    var images = [];
    var currentIdx = 0;
    var lb, lbImg, lbClose, lbPrev, lbNext, lbCounter;
    var startX = 0;
    var triggerEl = null;

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

      var inner = document.createElement('div');
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

      document.addEventListener('keydown', function (e) {
        if (!lb.classList.contains('open')) return;
        if (e.key === 'Escape') { close(); return; }
        if (e.key === 'ArrowLeft') { show(currentIdx - 1); return; }
        if (e.key === 'ArrowRight') { show(currentIdx + 1); return; }
        if (e.key === 'Tab') {
          var focusables = getFocusables();
          if (!focusables.length) return;
          var first = focusables[0];
          var last = focusables[focusables.length - 1];
          if (e.shiftKey) {
            if (document.activeElement === first) { e.preventDefault(); last.focus(); }
          } else {
            if (document.activeElement === last) { e.preventDefault(); first.focus(); }
          }
        }
      });

      lb.addEventListener('touchstart', function (e) { startX = e.touches[0].clientX; }, { passive: true });
      lb.addEventListener('touchend', function (e) {
        var dx = e.changedTouches[0].clientX - startX;
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
        var img = item.querySelector('img');
        if (!img) return;
        item.addEventListener('click', function () {
          var gallery = item.closest('.gallery-grid, .post-gallery');
          var imgs;
          if (gallery) {
            imgs = Array.from(gallery.querySelectorAll('.gallery-item img')).map(function (i) {
              return { src: i.src, alt: i.alt };
            });
          } else {
            imgs = [{ src: img.src, alt: img.alt }];
          }
          var idx = gallery
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
    initScrollProgress();
    initHeaderScroll();
    initBackToTop();
    initButtonRipple();
    initMobileMenu();
    markActiveNav();
    initCarousels();
    initScrollReveal();
    initHeroParallax();
    if (window.__initGalleries) window.__initGalleries();
  });
})();
