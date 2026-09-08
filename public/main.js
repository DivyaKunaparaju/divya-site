(function () {
  'use strict';

  /* ── Nav: transparent → solid on scroll ── */
  const nav = document.getElementById('nav');
  function onScroll() {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ── Nav: mobile toggle ── */
  const toggle = document.querySelector('.nav-toggle');
  const navLinks = document.getElementById('nav-links');

  toggle.addEventListener('click', function () {
    const expanded = this.getAttribute('aria-expanded') === 'true';
    this.setAttribute('aria-expanded', String(!expanded));
    navLinks.classList.toggle('is-open', !expanded);
  });

  navLinks.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
      toggle.setAttribute('aria-expanded', 'false');
      navLinks.classList.remove('is-open');
    });
  });

  document.addEventListener('click', function (e) {
    if (!nav.contains(e.target)) {
      toggle.setAttribute('aria-expanded', 'false');
      navLinks.classList.remove('is-open');
    }
  });

  /* ── Section reveal via IntersectionObserver ──
     Sections are visible by default (no "reveal" class in the static HTML).
     JS only *adds* the fade-in treatment as an enhancement. Two safeguards
     keep this from ever permanently hiding content:
       1. A section only gets the "reveal" (opacity: 0) class right before
          it's observed -- if this script fails to load or run at all,
          nothing is ever hidden in the first place.
       2. Some browsers don't reliably fire IntersectionObserver for very
          tall elements already in the initial viewport (a known issue on
          older WebKit/mobile Safari). A fallback timer force-reveals any
          section the observer hasn't caught within 1.5s, so a missed
          callback degrades to "no animation" instead of "invisible". */
  if ('IntersectionObserver' in window) {
    const revealItems = document.querySelectorAll('.section');
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    revealItems.forEach(function (el) {
      el.classList.add('reveal');
      observer.observe(el);
    });

    setTimeout(function () {
      revealItems.forEach(function (el) {
        el.classList.add('is-visible');
      });
      observer.disconnect();
    }, 1500);
  }

})();
