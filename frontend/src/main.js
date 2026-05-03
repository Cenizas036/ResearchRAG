import './style.css'

document.addEventListener('DOMContentLoaded', () => {
  // ── Nav scroll effect ──
  const nav = document.getElementById('main-nav');
  const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 50);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ── Typing Animation ──
  const phrases = [
    "AI-powered research at your fingertips.",
    "Hybrid search across thousands of papers.",
    "Cited answers you can trust.",
    "Multi-hop reasoning meets RAG."
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

  // ── API Integration ──
  const sendBtn = document.getElementById('send-btn');
  const vibeTextarea = document.getElementById('vibe-textarea');
  const responseContainer = document.getElementById('chat-response-container');

  async function handleSend() {
    const query = vibeTextarea.value.trim();
    if (!query) return;

    // Show loading state
    sendBtn.disabled = true;
    sendBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="spin"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>`;
    const spinStyle = document.createElement('style');
    spinStyle.innerHTML = `@keyframes spin { 100% { transform: rotate(360deg); } } .spin { animation: spin 1s linear infinite; }`;
    document.head.appendChild(spinStyle);
    
    responseContainer.style.display = 'block';
    responseContainer.innerHTML = '<p>Thinking...</p>';
    const integrationBar = document.querySelector('.integration-bar');
    if (integrationBar) integrationBar.style.display = 'none';

    try {
      const res = await fetch('https://sanket036-researchrag-api.hf.space/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      
      if (!res.ok) throw new Error('API Request Failed');
      const data = await res.json();
      
      // Simple markdown to HTML
      function md(text) {
        return text
          .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
          .replace(/^### (.+)$/gm, '<h3>$1</h3>')
          .replace(/^## (.+)$/gm, '<h2>$1</h2>')
          .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.+?)\*/g, '<em>$1</em>')
          .replace(/^- (.+)$/gm, '<li>$1</li>')
          .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
          .replace(/\n{2,}/g, '</p><p>')
          .replace(/\n/g, '<br>')
          .replace(/^/, '<p>')
          .replace(/$/, '</p>');
      }
      responseContainer.innerHTML = `<div class="ai-response">${md(data.response)}</div>`;
      vibeTextarea.value = '';
    } catch (err) {
      responseContainer.innerHTML = `<p style="color: #ef4444;">Error: ${err.message}</p>`;
    } finally {
      sendBtn.disabled = false;
      sendBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>`;
    }
  }

  sendBtn.addEventListener('click', handleSend);
  vibeTextarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });
});
