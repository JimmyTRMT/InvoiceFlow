// Fills the dashboard with the figures and invoices served by the API.

import { ApiError, getJson } from './api.js';
import { applyStatus, formatDate, formatMonth, formatMoney } from './ui.js';

const RECENT_LIMIT = 6;
const UNAVAILABLE = 'n/a';

const errorBanner = document.getElementById('dashboard-error');
const tableWrapper = document.getElementById('recent-invoices-table');
const invoicesBody = document.getElementById('recent-invoices');
const emptyState = document.getElementById('recent-invoices-empty');
const rowTemplate = document.getElementById('invoice-row-template');

function setStat(name, text) {
  document.querySelector(`[data-stat="${name}"]`).textContent = text;
}

function renderStats(stats) {
  setStat('outstanding_total', formatMoney(stats.outstanding_total));
  setStat('paid_this_month', formatMoney(stats.paid_this_month));
  setStat('overdue_count', String(stats.overdue_count));
  setStat('month', formatMonth(stats.month));
}

// Clone the markup declared in the page instead of building HTML here,
// which also means no invoice text is ever parsed as markup.
function buildRow(invoice) {
  const row = rowTemplate.content.firstElementChild.cloneNode(true);
  const field = (name) => row.querySelector(`[data-field="${name}"]`);

  field('number').textContent = invoice.number;
  field('client').textContent = invoice.client ? invoice.client.name : '';
  field('issue-date').textContent = formatDate(invoice.issue_date);
  field('due-date').textContent = formatDate(invoice.due_date);
  field('total').textContent = formatMoney(invoice.total);
  applyStatus(field('status'), invoice.effective_status);
  return row;
}

function renderInvoices(invoices) {
  invoicesBody.replaceChildren(...invoices.map(buildRow));
  const isEmpty = invoices.length === 0;
  tableWrapper.hidden = isEmpty;
  emptyState.hidden = !isEmpty;
}

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.hidden = false;
  ['outstanding_total', 'paid_this_month', 'overdue_count', 'month']
    .forEach((name) => setStat(name, UNAVAILABLE));
  invoicesBody.replaceChildren();
  tableWrapper.hidden = true;
  emptyState.hidden = true;
}

async function load() {
  try {
    const [stats, invoices] = await Promise.all([
      getJson('/dashboard/stats'),
      getJson(`/invoices?limit=${RECENT_LIMIT}`),
    ]);
    renderStats(stats);
    renderInvoices(invoices);
  } catch (error) {
    showError(
      error instanceof ApiError
        ? error.message
        : 'The dashboard could not be loaded.'
    );
  }
}

load();
