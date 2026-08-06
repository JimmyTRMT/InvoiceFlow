// Formatting helpers shared by every page.

const LOCALE = navigator.language || 'en-US';
const CURRENCY = document.body.dataset.currency || 'EUR';

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
