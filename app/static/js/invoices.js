import { ApiError, getJson } from './api.js';
import {
  NEXT_STATUS,
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

const INVOICE_PATH = '/invoices/';

const statusFilter = document.getElementById('status-filter');
const clientFilter = document.getElementById('client-filter');
const tableWrapper = document.getElementById('invoices-table');
const tableBody = document.getElementById('invoices-body');
const emptyState = document.getElementById('invoices-empty');
const errorBanner = document.getElementById('invoices-error');
const summary = document.getElementById('invoices-summary');
const rowTemplate = document.getElementById('invoice-row-template');

const statusButtons = Array.from(
  statusFilter.querySelectorAll('[data-status]')
);

// The only place the current view is stored; the controls follow it.
const filters = { status: '', client: '' };

function currentQuery() {
  const params = new URLSearchParams();
  if (filters.status) {
    params.set('status', filters.status);
  }
  if (filters.client) {
    params.set('client_id', filters.client);
  }
  return params.toString();
}

// Keep the filters in the address bar so a view can be linked to.
function updateAddress() {
  const query = currentQuery();
  const { pathname } = window.location;
  window.history.replaceState(
    null,
    '',
    query ? `${pathname}?${query}` : pathname
  );
}

function selectStatus(status) {
  filters.status = status;
  statusButtons.forEach((button) => {
    button.setAttribute(
      'aria-pressed',
      String(button.dataset.status === status)
    );
  });
}

// Run one row action, then read the list back so every row reflects it.
async function runAction(work, failure) {
  try {
    const message = await work();
    await loadInvoices();
    if (message) {
      showToast(message);
    }
  } catch (error) {
    reportFailure(error, failure);
  }
}

function wireMenu(row, invoice) {
  const menu = row.querySelector('[data-row-menu]');
  const item = (name) => menu.querySelector(`[data-action="${name}"]`);
  setupMenu(menu);

  const next = NEXT_STATUS[invoice.status];
  const advance = item('advance');
  advance.hidden = !next;
  if (next) {
    advance.textContent = next.label;
    advance.addEventListener('click', () => runAction(
      async () => {
        await changeStatus(invoice, next.value);
        return `${invoice.number} moved to ${next.value}.`;
      },
      'The invoice could not be updated.'
    ));
  }

  item('edit').href = `${INVOICE_PATH}${invoice.id}/edit`;

  item('duplicate').addEventListener('click', () => runAction(
    async () => `Copied to ${(await duplicate(invoice)).number}.`,
    'The invoice could not be duplicated.'
  ));

  item('delete').addEventListener('click', async () => {
    if (await confirmDelete(invoice)) {
      runAction(
        async () => {
          await remove(invoice);
          return `${invoice.number} deleted.`;
        },
        'The invoice could not be deleted.'
      );
    }
  });
}

function buildRow(invoice) {
  const row = rowTemplate.content.firstElementChild.cloneNode(true);
  const field = (name) => row.querySelector(`[data-field="${name}"]`);

  const link = field('link');
  link.textContent = invoice.number;
  link.href = `${INVOICE_PATH}${invoice.id}`;
  field('client').textContent = invoice.client ? invoice.client.name : '';
  field('issue-date').textContent = formatDate(invoice.issue_date);
  field('due-date').textContent = formatDate(invoice.due_date);
  field('total').textContent = formatMoney(invoice.total);
  applyStatus(field('status'), invoice.effective_status);
  wireMenu(row, invoice);
  return row;
}

// Summed in cents so a long list cannot drift by a rounding step.
function renderSummary(invoices) {
  if (invoices.length === 0) {
    summary.textContent = 'No result.';
    return;
  }
  const cents = invoices.reduce(
    (running, invoice) => running + Math.round(invoice.total * 100),
    0
  );
  const label = invoices.length === 1 ? 'invoice' : 'invoices';
  summary.textContent =
    `${invoices.length} ${label} - ${formatMoney(cents / 100)}`;
}

function renderInvoices(invoices) {
  tableBody.replaceChildren(...invoices.map(buildRow));
  const isEmpty = invoices.length === 0;
  tableWrapper.hidden = isEmpty;
  emptyState.hidden = !isEmpty;
  emptyState.textContent = currentQuery()
    ? 'No invoice matches these filters.'
    : 'No invoice yet. Create your first one and it will show up here.';
  renderSummary(invoices);
}

function showError(error) {
  errorBanner.textContent =
    error instanceof ApiError
      ? error.message
      : 'The invoice list could not be loaded.';
  errorBanner.hidden = false;
  tableBody.replaceChildren();
  tableWrapper.hidden = true;
  emptyState.hidden = true;
  summary.textContent = '';
}

async function loadInvoices() {
  const query = currentQuery();
  try {
    const invoices = await getJson(query ? `/invoices?${query}` : '/invoices');
    errorBanner.hidden = true;
    renderInvoices(invoices);
  } catch (error) {
    showError(error);
  }
}

async function loadClients() {
  try {
    const clients = await getJson('/clients');
    clients.forEach((client) => {
      const option = document.createElement('option');
      option.value = String(client.id);
      option.textContent = client.company
        ? `${client.name} (${client.company})`
        : client.name;
      clientFilter.append(option);
    });
    // A select cannot hold a value it has no option for, so an unknown
    // id coming from the address bar drops back to every client.
    clientFilter.value = filters.client;
    filters.client = clientFilter.value;
    updateAddress();
  } catch (error) {
    // The list itself still works, so the filter is simply left disabled.
    clientFilter.disabled = true;
  }
}

function readAddress() {
  const params = new URLSearchParams(window.location.search);
  const status = params.get('status') || '';
  if (statusButtons.some((button) => button.dataset.status === status)) {
    selectStatus(status);
  }
  filters.client = params.get('client_id') || '';
}

statusFilter.addEventListener('click', (event) => {
  const button = event.target.closest('[data-status]');
  if (!button || button.dataset.status === filters.status) {
    return;
  }
  selectStatus(button.dataset.status);
  updateAddress();
  loadInvoices();
});

clientFilter.addEventListener('change', () => {
  filters.client = clientFilter.value;
  updateAddress();
  loadInvoices();
});

// Both requests go out together, unless a client id from the address
// bar has to be checked against the options before it is used.
async function start() {
  readAddress();
  updateAddress();
  const clientsReady = loadClients();
  if (filters.client) {
    await clientsReady;
  }
  loadInvoices();
}

start();
