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

  /* ── GitHub repos ── */
  const LANG_COLORS = {
    JavaScript: '#f1e05a',
    TypeScript: '#3178c6',
    Python: '#3572A5',
    HTML: '#e34c26',
    CSS: '#563d7c',
    Shell: '#89e051',
    Java: '#b07219',
    Go: '#00ADD8',
    Rust: '#dea584',
    Ruby: '#701516',
    'C++': '#f34b7d',
    C: '#555555',
    Swift: '#F05138',
    Kotlin: '#7F52FF',
    Jupyter: '#DA5B0B',
  };

  function buildRepoCard(repo) {
    const card = document.createElement('a');
    card.className = 'repo-card';
    card.href = repo.html_url;
    card.target = '_blank';
    card.rel = 'noopener noreferrer';
    card.setAttribute('aria-label', repo.name + (repo.description ? ': ' + repo.description : ''));

    const name = document.createElement('span');
    name.className = 'repo-name';
    name.textContent = repo.name;

    const arrow = document.createElement('span');
    arrow.setAttribute('aria-hidden', 'true');
    arrow.textContent = ' ↗';
    name.appendChild(arrow);

    const desc = document.createElement('p');
    desc.className = 'repo-desc';
    desc.textContent = repo.description || 'No description.';

    const meta = document.createElement('div');
    meta.className = 'repo-meta';

    if (repo.language) {
      const lang = document.createElement('span');
      lang.className = 'repo-lang';

      const dot = document.createElement('span');
      dot.className = 'repo-lang-dot';
      dot.style.background = LANG_COLORS[repo.language] || '#7A9AB5';
      dot.setAttribute('aria-hidden', 'true');

      lang.appendChild(dot);
      lang.appendChild(document.createTextNode(repo.language));
      meta.appendChild(lang);
    }

    if (repo.stargazers_count > 0) {
      const stars = document.createElement('span');
      stars.className = 'repo-stars';
      stars.innerHTML = '<span aria-hidden="true">★</span> ' + repo.stargazers_count;
      meta.appendChild(stars);
    }

    card.appendChild(name);
    card.appendChild(desc);
    card.appendChild(meta);
    return card;
  }

  const grid = document.getElementById('repos-grid');

  fetch('https://api.github.com/users/DivyaKunaparaju/repos?sort=updated&per_page=12')
    .then(function (res) {
      if (!res.ok) throw new Error('Request failed: ' + res.status);
      return res.json();
    })
    .then(function (repos) {
      grid.innerHTML = '';
      if (!repos.length) {
        grid.innerHTML = '<p class="repos-status">No public repositories yet.</p>';
        return;
      }
      repos.forEach(function (repo) {
        grid.appendChild(buildRepoCard(repo));
      });
    })
    .catch(function () {
      grid.innerHTML = '<p class="repos-status">Couldn\'t load repositories right now — visit <a href="https://github.com/DivyaKunaparaju" target="_blank" rel="noopener noreferrer" style="color:var(--accent)">GitHub</a> directly.</p>';
    });
})();
