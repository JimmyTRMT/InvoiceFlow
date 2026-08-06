// Off canvas sidebar behaviour for the application shell.

const DESKTOP_QUERY = window.matchMedia('(min-width: 1024px)');

const sidebar = document.getElementById('sidebar');
const backdrop = document.getElementById('sidebar-backdrop');
const toggle = document.getElementById('sidebar-toggle');

// Move the panel and keep the toggle, the backdrop and scrolling in step.
function setSidebar(open) {
  sidebar.classList.toggle('is-open', open);
  backdrop.classList.toggle('hidden', !open);
  document.body.classList.toggle('no-scroll', open);
  toggle.setAttribute('aria-expanded', String(open));
}

function isOpen() {
  return sidebar.classList.contains('is-open');
}

toggle.addEventListener('click', () => {
  const opening = !isOpen();
  setSidebar(opening);
  if (opening) {
    sidebar.querySelector('a').focus();
  }
});

backdrop.addEventListener('click', () => setSidebar(false));

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && isOpen()) {
    setSidebar(false);
    toggle.focus();
  }
});

// Following a link should reveal the page, not leave the panel over it.
sidebar.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', () => setSidebar(false));
});

// Growing past the mobile layout must never strand the backdrop on screen.
DESKTOP_QUERY.addEventListener('change', () => setSidebar(false));
