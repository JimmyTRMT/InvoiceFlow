// Renders one invoice as a printable sheet and drives its actions.

import { ApiError, deleteJson, getJson, postJson } from './api.js';
import {
  applyStatus,
  askConfirmation,
  formatDate,
  formatMoney,
  showToast,
} from './ui.js';

const DASHBOARD_URL = '/';

const invoiceId = document.querySelector('[data-invoice-id]').dataset.invoiceId;

const loading = document.getElementById('invoice-loading');
const errorPanel = document.getElementById('invoice-error');
const sheet = document.getElementById('invoice-sheet');
const actions = document.getElementById('invoice-actions');
const linesBody = document.getElementById('invoice-lines');
const lineTemplate = document.getElementById('invoice-line-template');
const markPaidButton = document.getElementById('mark-paid');

let invoice = null;

function field(name, root = sheet) {
  return root.querySelector(`[data-field="${name}"]`);
}

function set(name, text) {
  field(name).textContent = text;
}

function buildLine(item) {
  const row = lineTemplate.content.firstElementChild.cloneNode(true);
  row.querySelector('[data-field="description"]').textContent =
    item.description;
  row.querySelector('[data-field="quantity"]').textContent = item.quantity;
  row.querySelector('[data-field="unit-price"]').textContent =
    formatMoney(item.unit_price);
  row.querySelector('[data-field="amount"]').textContent =
    formatMoney(item.line_total);
  return row;
}

function render() {
  const client = invoice.client || {};

  set('number', invoice.number);
  applyStatus(field('status'), invoice.effective_status);

  set('client-name', client.name || '');
  set('client-company', client.company || '');
  set('client-address', client.address || '');
  set('client-email', client.email || '');

  set('issue-date', formatDate(invoice.issue_date));
  set('due-date', formatDate(invoice.due_date));
  field('paid-row').hidden = !invoice.paid_at;
  set('paid-at', formatDate(invoice.paid_at));

  linesBody.replaceChildren(...invoice.line_items.map(buildLine));

  set('subtotal', formatMoney(invoice.subtotal));
  set('tax-rate', `(${invoice.tax_rate}%)`);
  set('tax-amount', formatMoney(invoice.tax_amount));
  set('total', formatMoney(invoice.total));

  field('notes-block').hidden = !invoice.notes;
  set('notes', invoice.notes || '');

  markPaidButton.hidden = invoice.status === 'paid';
  loading.hidden = true;
  errorPanel.hidden = true;
  sheet.hidden = false;
  actions.hidden = false;
}

function showError(error, fallback) {
  errorPanel.querySelector('[data-field="error-message"]').textContent =
    error instanceof ApiError ? error.message : fallback;
  loading.hidden = true;
  sheet.hidden = true;
  actions.hidden = true;
  errorPanel.hidden = false;
}

async function markAsPaid() {
  markPaidButton.disabled = true;
  try {
    invoice = await postJson(`/invoices/${invoiceId}/mark-paid`);
    render();
    showToast('Invoice marked as paid.');
  } catch (error) {
    showToast(
      error instanceof ApiError
        ? error.message
        : 'The invoice could not be updated.',
      'error'
    );
  } finally {
    markPaidButton.disabled = false;
  }
}

async function removeInvoice() {
  const accepted = await askConfirmation({
    title: 'Delete this invoice',
    message: `${invoice.number} and all of its lines will be removed.`,
    confirmLabel: 'Delete invoice',
  });
  if (!accepted) {
    return;
  }

  try {
    await deleteJson(`/invoices/${invoiceId}`);
    window.location.assign(DASHBOARD_URL);
  } catch (error) {
    showToast(
      error instanceof ApiError
        ? error.message
        : 'The invoice could not be deleted.',
      'error'
    );
  }
}

async function load() {
  try {
    invoice = await getJson(`/invoices/${invoiceId}`);
    document.title = `${invoice.number} - InvoiceFlow`;
    render();
  } catch (error) {
    showError(error, 'The invoice could not be loaded.');
  }
}

document.getElementById('print-invoice')
  .addEventListener('click', () => window.print());
document.getElementById('delete-invoice')
  .addEventListener('click', removeInvoice);
markPaidButton.addEventListener('click', markAsPaid);

load();
