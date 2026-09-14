const LOCALE = navigator.language || 'en-US';
const CURRENCY = document.body.dataset.currency || 'EUR';
const TOAST_DURATION = 4000;

const toastRegion = document.getElementById('toast-region');
const toastTemplate = document.getElementById('toast-template');

const confirmDialog = document.getElementById('confirm-dialog');
const confirmTitle = document.getElementById('confirm-title');
const confirmMessage = document.getElementById('confirm-message');
const confirmAccept = document.getElementById('confirm-accept');

const STATUS_LABELS = {
  draft: 'Draft',
  sent: 'Sent',
  paid: 'Paid',
  overdue: 'Overdue',
};

// An unknown currency code makes Intl throw, so fall back to plain numbers.
function buildMoneyFormatter() {
  try {
    return new Intl.NumberFormat(LOCALE, {
      style: 'currency',
      currency: CURRENCY,
    });
  } catch (error) {
    return new Intl.NumberFormat(LOCALE, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
}

const moneyFormatter = buildMoneyFormatter();

const dayFormatter = new Intl.DateTimeFormat(LOCALE, {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
});

const monthFormatter = new Intl.DateTimeFormat(LOCALE, {
  month: 'long',
  year: 'numeric',
});

export function formatMoney(value) {
  return moneyFormatter.format(Number(value) || 0);
}

// Build the date from its parts: parsing the string would read it as UTC
// and show the day before in western timezones.
export function formatDate(isoDate) {
  if (!isoDate) {
    return '';
  }
  const [year, month, day] = isoDate.slice(0, 10).split('-').map(Number);
  if (!year || !month || !day) {
    return '';
  }
  return dayFormatter.format(new Date(year, month - 1, day));
}

export function formatMonth(isoMonth) {
  const [year, month] = String(isoMonth).split('-').map(Number);
  if (!year || !month) {
    return '';
  }
  return monthFormatter.format(new Date(year, month - 1, 1));
}

// Label a status badge and colour it, leaving unknown values readable.
export function applyStatus(element, status) {
  element.textContent = STATUS_LABELS[status] || status;
  element.className = `badge badge--${status}`;
}

// Resolve once the dialog closes, whichever button or key closed it.
export function askConfirmation({ title, message, confirmLabel }) {
  confirmTitle.textContent = title;
  confirmMessage.textContent = message;
  confirmAccept.textContent = confirmLabel;
  confirmDialog.returnValue = 'cancel';
  confirmDialog.showModal();

  return new Promise((resolve) => {
    confirmDialog.addEventListener(
      'close',
      () => resolve(confirmDialog.returnValue === 'confirm'),
      { once: true }
    );
  });
}

const MENU_GAP = 6;
const MENU_EDGE = 8;

const openMenus = new Set();

// One listener for every menu on the page, so a table of rows does not
// register a hundred of them. A click outside dismisses, which is also
// what closes one menu when another is opened.
document.addEventListener('click', (event) => {
  openMenus.forEach((menu) => {
    if (!menu.root.isConnected || !menu.root.contains(event.target)) {
      menu.close();
    }
  });
});

// A fixed panel does not follow its trigger, so scrolling dismisses it
// instead of leaving it behind. Capture, to catch inner scrollers too.
function closeAllMenus() {
  openMenus.forEach((menu) => menu.close());
}

window.addEventListener('scroll', closeAllMenus, true);
window.addEventListener('resize', closeAllMenus);

// Right aligned under the trigger, flipped above when the bottom of the
// window is too close, and never pushed off the left edge.
function placeMenu(trigger, panel) {
  const anchor = trigger.getBoundingClientRect();
  const below = anchor.bottom + MENU_GAP;
  const fitsBelow = below + panel.offsetHeight <= window.innerHeight;

  panel.style.top = fitsBelow
    ? `${below}px`
    : `${Math.max(MENU_EDGE, anchor.top - panel.offsetHeight - MENU_GAP)}px`;
  panel.style.left =
    `${Math.max(MENU_EDGE, anchor.right - panel.offsetWidth)}px`;
}

// offsetParent is null for anything not displayed, which covers both the
// hidden attribute and an item a breakpoint has switched off.
function menuItems(panel) {
  return Array.from(panel.querySelectorAll('[data-action]'))
    .filter((item) => item.offsetParent !== null && !item.disabled);
}

// A popover menu: one trigger, one panel, closed by Escape, by a choice
// or by a click anywhere else.
export function setupMenu(root) {
  const trigger = root.querySelector('[data-menu-trigger]');
  const panel = root.querySelector('[data-menu-panel]');
  const menu = { root, close };

  function close() {
    panel.hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
    openMenus.delete(menu);
  }

  // Shown before being measured, since a hidden panel has no size.
  function open() {
    panel.hidden = false;
    placeMenu(trigger, panel);
    trigger.setAttribute('aria-expanded', 'true');
    openMenus.add(menu);
  }

  trigger.addEventListener('click', () => {
    if (panel.hidden) {
      open();
    } else {
      close();
    }
  });

  panel.addEventListener('click', close);

  root.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      close();
      trigger.focus();
      return;
    }
    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') {
      return;
    }
    event.preventDefault();
    open();
    const items = menuItems(panel);
    const step = event.key === 'ArrowDown' ? 1 : -1;
    const current = items.indexOf(document.activeElement);
    let next = step === 1 ? 0 : items.length - 1;
    if (current !== -1) {
      next = (current + step + items.length) % items.length;
    }
    if (items[next]) {
      items[next].focus();
    }
  });

  return menu;
}

// Announce the outcome of an action, then get out of the way.
export function showToast(message, tone = 'success') {
  const toast = toastTemplate.content.firstElementChild.cloneNode(true);
  toast.classList.add(`toast--${tone}`);
  toast.querySelector('[data-field="message"]').textContent = message;
  toastRegion.append(toast);
  window.setTimeout(() => toast.remove(), TOAST_DURATION);
}
