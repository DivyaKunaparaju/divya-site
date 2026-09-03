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

  /* ── Section reveal via IntersectionObserver ── */
  if ('IntersectionObserver' in window) {
    const revealItems = document.querySelectorAll('.reveal');
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    revealItems.forEach(function (el) {
      observer.observe(el);
    });
  } else {
    document.querySelectorAll('.reveal').forEach(function (el) {
      el.classList.add('is-visible');
    });
  }

})();
