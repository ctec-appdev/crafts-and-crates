/* Crafts & Crates ATL — experience.html scroll choreography
   Rules of this page:
   - Content-first: with JS off (or reduced motion), everything is visible.
     The only hidden-from state lives in CSS under body.motion-on.
   - body.motion-on is added ONLY after GSAP + ScrollTrigger are confirmed loaded.
   - Pins/parallax/horizontal track are desktop-only via gsap.matchMedia().
   - Reveals are created AFTER pins (pre-pin triggers keep stale offsets). */
(function () {
  'use strict';

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return; // static page
  if (!window.gsap || !window.ScrollTrigger) return;                          // CDN blocked → readable page
  gsap.registerPlugin(ScrollTrigger);

  /* Load-time hero intro — .from() plays from the visible markup, so a dead
     CDN or interrupted script can never leave the hero hidden. */
  gsap.from('.x-hero-content > *', {
    opacity: 0, y: 24, duration: 0.7, stagger: 0.09, ease: 'power2.out',
    delay: 0.12, clearProps: 'all'
  });

  var mm = gsap.matchMedia();

  /* ---------------- DESKTOP ---------------- */
  mm.add('(min-width: 1024px)', function () {
    document.body.classList.add('motion-on');
    var ok = true;
    try {
      buildDesktopPins();   // pins FIRST…
      buildDesktopParallax();
      buildReveals();       // …then reveals (pre-pin triggers measure stale offsets)
      buildCounters();
    } catch (e) {
      ok = false;
      if (window.console) console.error('experience: motion fallback to static layout', e);
    }
    if (!ok) {
      document.body.classList.remove('motion-on');
      return function () {};
    }
    return function () {
      document.body.classList.remove('motion-on');
      clearMotion([
        '.x-hero-media img', '.x-hero-content',
        '.x-track', '.x-rail-bar',
        '.x-climax-media img', '.x-climax-line',
        '.x-reveal', '[data-count]'
      ]);
    };
  });

  /* ---------------- MOBILE ---------------- */
  mm.add('(max-width: 1023px)', function () {
    document.body.classList.add('motion-on');
    var ok = true;
    try {
      buildReveals();
      buildCounters();
    } catch (e) {
      ok = false;
      if (window.console) console.error('experience: motion fallback to static layout', e);
    }
    if (!ok) {
      document.body.classList.remove('motion-on');
      return function () {};
    }
    return function () {
      document.body.classList.remove('motion-on');
      clearMotion(['.x-reveal', '[data-count]']);
    };
  });

  window.addEventListener('load', function () {
    ScrollTrigger.refresh();
  });

  /* =========================================================
     Desktop choreography (pins + parallax)
     ========================================================= */

  function buildDesktopPins() {
    /* JOURNEY — pinned horizontal filmtrack */
    var track = document.querySelector('.x-track');
    var pinwrap = document.querySelector('.x-pinwrap');
    var bar = document.querySelector('.x-rail-bar');
    if (track && pinwrap) {
      var dist = function () {
        return Math.max(track.scrollWidth - window.innerWidth, 0);
      };
      if (dist() > window.innerWidth * 0.5) {
        gsap.to(track, {
          x: function () { return -dist(); },
          ease: 'none',
          scrollTrigger: {
            trigger: pinwrap,
            pin: true,
            start: 'top top',
            end: function () { return '+=' + dist(); },
            scrub: 1,
            anticipatePin: 1,
            invalidateOnRefresh: true,
            onUpdate: function (self) {
              if (bar) gsap.set(bar, { scaleX: self.progress });
            }
          }
        });
      }
    }

    /* CLIMAX — pinned three-beat crossfade; every stop moves, no dead scroll */
    var lines = gsap.utils.toArray('.x-climax-line');
    if (lines.length > 1) {
      gsap.set(lines, { autoAlpha: 0 });
      gsap.set(lines[0], { autoAlpha: 1 });
      var tl = gsap.timeline({
        scrollTrigger: {
          trigger: '.x-climax',
          pin: true,
          start: 'top top',
          end: '+=180%',
          scrub: true,
          anticipatePin: 1
        }
      });
      // beat 1 → beat 2
      tl.to(lines[1], { autoAlpha: 1, duration: 0.9 }, '+=0.6')
       .to(lines[0], { autoAlpha: 0, duration: 0.9 }, '<');
      // beat 2 → beat 3 (accent line)
      tl.to(lines[2], { autoAlpha: 1, duration: 0.9 }, '+=1.0')
       .to(lines[1], { autoAlpha: 0, duration: 0.9 }, '<');
      // hold the accent line while the bg keeps drifting
      tl.to({}, { duration: 1.4 });
    }
  }

  function buildDesktopParallax() {
    /* HERO — bg layer drifts slower than the page (layer has a 12% overhang;
       8% of img height ≈ 10% of section, so no canvas ever shows). */
    gsap.to('.x-hero-media img', {
      yPercent: 8,
      ease: 'none',
      scrollTrigger: { trigger: '.x-hero', start: 'top top', end: 'bottom top', scrub: true }
    });
    gsap.to('.x-hero-content', {
      opacity: 0, y: -56,
      ease: 'none',
      scrollTrigger: { trigger: '.x-hero', start: 'top top', end: 'bottom 25%', scrub: true }
    });

    /* CLIMAX — bg drift across the whole approach + pin */
    gsap.fromTo('.x-climax-media img',
      { yPercent: -6 },
      { yPercent: 6, ease: 'none',
        scrollTrigger: { trigger: '.x-climax', start: 'top bottom', end: 'bottom top', scrub: true }
      });
  }

  /* =========================================================
     Reveal batch + counters (both breakpoints)
     ========================================================= */

  function buildReveals() {
    var targets = gsap.utils.toArray('.x-reveal');
    if (!targets.length) return;
    ScrollTrigger.batch(targets, {
      start: 'top 88%',
      once: true,
      onEnter: function (batch) {
        gsap.to(batch, {
          opacity: 1, y: 0,
          duration: 0.7, ease: 'power2.out', stagger: 0.12,
          overwrite: true
          // NO clearProps here: clearing inline styles would re-apply the
          // .motion-on .x-reveal hidden CSS and re-hide revealed content.
        });
      }
    });
  }

  function buildCounters() {
    gsap.utils.toArray('[data-count]').forEach(function (el) {
      ScrollTrigger.create({
        trigger: el,
        start: 'top 88%',
        once: true,
        onEnter: function () {
          var end = parseInt(el.getAttribute('data-count'), 10) || 0;
          if (!end) return;
          var obj = { v: 0 };
          gsap.to(obj, {
            v: end,
            duration: 1.2,
            ease: 'power1.out',
            onUpdate: function () { el.textContent = Math.round(obj.v); }
          });
        }
      });
    });
  }

  function clearMotion(selectors) {
    selectors.forEach(function (sel) {
      gsap.utils.toArray(sel).forEach(function (el) {
        gsap.set(el, { clearProps: 'all' });
      });
    });
  }
})();
