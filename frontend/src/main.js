import './style.css'

document.addEventListener('DOMContentLoaded', () => {
  // ── Nav scroll effect ──
  const nav = document.getElementById('main-nav');
  const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 50);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ── Typing Animation ──
  const phrases = [
    "Build interfaces that feel alive.",
    "A vibe-centric design system.",
    "Engineered for the modern web.",
    "Glassmorphism meets performance."
  ];
  let pi = 0, ci = 0, deleting = false;
  const el = document.getElementById('typing-text');
  function tick() {
    const phrase = phrases[pi];
    if (deleting) { ci--; } else { ci++; }
    el.textContent = phrase.substring(0, ci);
    let delay = deleting ? 40 : 80;
    if (!deleting && ci === phrase.length) { delay = 2200; deleting = true; }
    else if (deleting && ci === 0) { deleting = false; pi = (pi + 1) % phrases.length; delay = 400; }
    setTimeout(tick, delay);
  }
  if (el) tick();

  // ── FAQ Accordion ──
  document.querySelectorAll('.accordion-item').forEach(item => {
    const trigger = item.querySelector('.accordion-trigger');
    const content = item.querySelector('.accordion-content');
    trigger.addEventListener('click', () => {
      const open = item.classList.contains('open');
      document.querySelectorAll('.accordion-item').forEach(i => {
        i.classList.remove('open');
        i.querySelector('.accordion-trigger').setAttribute('aria-expanded', 'false');
        i.querySelector('.accordion-content').style.maxHeight = null;
      });
      if (!open) {
        item.classList.add('open');
        trigger.setAttribute('aria-expanded', 'true');
        content.style.maxHeight = content.scrollHeight + 'px';
      }
    });
  });

  // ── Scroll-Spy ──
  const blocks = document.querySelectorAll('.feature-block');
  const links = document.querySelectorAll('.spy-link');
  const dot = document.getElementById('active-indicator');
  const navUl = document.querySelector('.sticky-feature-nav ul');

  function moveDot(link) {
    if (!link || !dot || !navUl) return;
    const lr = link.getBoundingClientRect();
    const nr = navUl.getBoundingClientRect();
    dot.style.top = (lr.top - nr.top + lr.height / 2 - 3) + 'px';
  }

  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        links.forEach(l => l.classList.remove('active'));
        const hit = document.querySelector(`.spy-link[href="#${e.target.id}"]`);
        if (hit) { hit.classList.add('active'); moveDot(hit); }
      }
    });
  }, { rootMargin: '-30% 0px -50% 0px' });

  blocks.forEach(b => obs.observe(b));
  setTimeout(() => { const a = document.querySelector('.spy-link.active'); if (a) moveDot(a); }, 150);
  window.addEventListener('resize', () => { const a = document.querySelector('.spy-link.active'); if (a) moveDot(a); });
});
