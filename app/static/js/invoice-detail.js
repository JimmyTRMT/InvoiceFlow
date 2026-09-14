import { ApiError, getJson } from './api.js';
import {
  NEXT_STATUS,
  REVERT_STATUS,
  changeStatus,
  confirmDelete,
  duplicate,
  remove,
  reportFailure,
} from './invoice-actions.js';
import {
  applyStatus,
  formatDate,
  formatMoney,
  setupMenu,
  showToast,
} from './ui.js';

const LIST_URL = '/invoices';
const INVOICE_PATH = '/invoices/';

const invoiceId = document.querySelector('[data-invoice-id]').dataset.invoiceId;

const loading = document.getElementById('invoice-loading');
const errorPanel = document.getElementById('invoice-error');
const sheet = document.getElementById('invoice-sheet');
const actions = document.getElementById('invoice-actions');
const linesBody = document.getElementById('invoice-lines');
const lineTemplate = document.getElementById('invoice-line-template');
const statusButton = document.getElementById('status-action');
const menu = document.getElementById('invoice-menu');
const revertButton = menu.querySelector('[data-action="revert"]');

setupMenu(menu);

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

// The button offers the next step, the menu offers the way back.
function renderActions() {
  const next = NEXT_STATUS[invoice.status];
  statusButton.hidden = !next;
  if (next) {
    statusButton.textContent = next.label;
  }

  const revert = REVERT_STATUS[invoice.status];
  revertButton.hidden = !revert;
  if (revert) {
    revertButton.textContent = revert.label;
  }
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

  renderActions();
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

async function moveTo(status, button) {
  button.disabled = true;
  try {
    invoice = await changeStatus(invoice, status);
    render();
    showToast(`Invoice moved to ${status}.`);
  } catch (error) {
    reportFailure(error, 'The invoice could not be updated.');
  } finally {
    button.disabled = false;
  }
}

async function duplicateInvoice() {
  try {
    const copy = await duplicate(invoice);
    showToast(`Copied to ${copy.number}.`);
    window.location.assign(`${INVOICE_PATH}${copy.id}`);
  } catch (error) {
    reportFailure(error, 'The invoice could not be duplicated.');
  }
}

async function removeInvoice() {
  if (!await confirmDelete(invoice)) {
    return;
  }
  try {
    await remove(invoice);
    window.location.assign(LIST_URL);
  } catch (error) {
    reportFailure(error, 'The invoice could not be deleted.');
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

statusButton.addEventListener('click', () => {
  moveTo(NEXT_STATUS[invoice.status].value, statusButton);
});
revertButton.addEventListener('click', () => {
  moveTo(REVERT_STATUS[invoice.status].value, revertButton);
});
menu.querySelector('[data-action="duplicate"]')
  .addEventListener('click', duplicateInvoice);
menu.querySelector('[data-action="delete"]')
  .addEventListener('click', removeInvoice);
menu.querySelector('[data-action="print"]')
  .addEventListener('click', () => window.print());
document.getElementById('print-invoice')
  .addEventListener('click', () => window.print());

load();
