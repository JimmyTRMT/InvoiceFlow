import { ApiError, getJson, postJson } from './api.js';
import { formatMoney } from './ui.js';

const INVOICE_PATH = '/invoices/';
const DEFAULT_DUE_DAYS = 30;
const LINE_ERROR = /^line_items\[(\d+)\]\.(\w+)$/;

const form = document.getElementById('invoice-form');
const clientSelect = document.getElementById('invoice-client');
const issueDateInput = document.getElementById('invoice-issue-date');
const dueDateInput = document.getElementById('invoice-due-date');
const taxRateInput = document.getElementById('invoice-tax-rate');
const submitButton = document.getElementById('invoice-submit');
const linesContainer = document.getElementById('line-items');
const lineTemplate = document.getElementById('line-item-template');
const formError = document.getElementById('invoice-error');
const noClients = document.getElementById('no-clients');

function rows() {
  return Array.from(linesContainer.children);
}

function field(row, name) {
  return row.querySelector(`[data-field="${name}"]`);
}

function toCents(value) {
  const number = Number.parseFloat(value);
  return Number.isFinite(number) ? Math.round(number * 100) : 0;
}

function setTotal(name, cents) {
  const holder = document.querySelector(`[data-total="${name}"]`);
  holder.textContent = formatMoney(cents / 100);
}

// Integer arithmetic on cents, exactly like the server, so the preview
// and the saved invoice can never disagree by a rounding step.
function recalculate() {
  let subtotalCents = 0;

  rows().forEach((row) => {
    const quantity = toCents(field(row, 'quantity').value);
    const unitPrice = toCents(field(row, 'unit_price').value);
    const amountCents = Math.round((quantity * unitPrice) / 100);
    subtotalCents += amountCents;
    field(row, 'amount').textContent = formatMoney(amountCents / 100);
  });

  const rateCents = toCents(taxRateInput.value);
  const taxCents = Math.round((subtotalCents * rateCents) / 10000);

  setTotal('subtotal', subtotalCents);
  setTotal('tax', taxCents);
  setTotal('total', subtotalCents + taxCents);
  document.querySelector('[data-total="rate"]').textContent =
    `(${rateCents / 100}%)`;
}

function removeRow(row) {
  row.remove();
  // The API refuses an invoice with no line, so never leave the list empty.
  if (linesContainer.children.length === 0) {
    addRow();
    return;
  }
  recalculate();
}

function addRow(focus = false) {
  const row = lineTemplate.content.firstElementChild.cloneNode(true);
  row.querySelector('[data-action="remove"]')
    .addEventListener('click', () => removeRow(row));
  linesContainer.append(row);
  if (focus) {
    field(row, 'description').focus();
  }
  recalculate();
}

// A line with neither a description nor a price was never filled in.
function isBlankRow(row) {
  return field(row, 'description').value.trim() === ''
    && field(row, 'unit_price').value.trim() === '';
}

function clearErrors() {
  formError.hidden = true;
  form.querySelectorAll('[data-error]').forEach((holder) => {
    holder.hidden = true;
  });
  form.querySelectorAll('[aria-invalid]').forEach((input) => {
    input.removeAttribute('aria-invalid');
  });
}

function markError(holder, input, message) {
  if (!holder) {
    return;
  }
  holder.textContent = message;
  holder.hidden = false;
  if (input) {
    input.setAttribute('aria-invalid', 'true');
  }
}

// Server keys look like line_items[1].quantity, so send each message
// back to the exact row that produced it.
function applyServerErrors(error, sentRows) {
  const fields = error instanceof ApiError ? error.fields : {};

  Object.entries(fields).forEach(([key, message]) => {
    const line = key.match(LINE_ERROR);
    if (!line) {
      markError(
        form.querySelector(`[data-error="${key}"]`),
        form.querySelector(`[name="${key}"]`),
        message
      );
      return;
    }
    const row = sentRows[Number(line[1])];
    if (row) {
      markError(
        row.querySelector(`[data-error="${line[2]}"]`),
        field(row, line[2]),
        message
      );
    }
  });
}

function showFormError(error, fallback) {
  formError.textContent =
    error instanceof ApiError ? error.message : fallback;
  formError.hidden = false;
}

// Build the value from the local calendar day, not from the UTC one.
function isoDate(date) {
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 10);
}

function applyDefaultDates() {
  const today = new Date();
  const due = new Date(today);
  due.setDate(due.getDate() + DEFAULT_DUE_DAYS);
  issueDateInput.value = isoDate(today);
  dueDateInput.value = isoDate(due);
}

async function loadClients() {
  try {
    const clients = await getJson('/clients');
    if (clients.length === 0) {
      noClients.hidden = false;
      clientSelect.disabled = true;
      submitButton.disabled = true;
      return;
    }
    clientSelect.replaceChildren(...clients.map((client) => {
      const option = document.createElement('option');
      option.value = String(client.id);
      option.textContent = client.company
        ? `${client.name} (${client.company})`
        : client.name;
      return option;
    }));
  } catch (error) {
    showFormError(error, 'The client list could not be loaded.');
    submitButton.disabled = true;
  }
}

async function submitForm(event) {
  event.preventDefault();
  clearErrors();

  const sentRows = rows().filter((row) => !isBlankRow(row));
  const payload = {
    client_id: clientSelect.value,
    issue_date: issueDateInput.value,
    due_date: dueDateInput.value,
    status: form.elements.status.value,
    tax_rate: taxRateInput.value,
    notes: form.elements.notes.value,
    line_items: sentRows.map((row) => ({
      description: field(row, 'description').value,
      quantity: field(row, 'quantity').value,
      unit_price: field(row, 'unit_price').value,
    })),
  };

  submitButton.disabled = true;
  try {
    const invoice = await postJson('/invoices', payload);
    window.location.assign(`${INVOICE_PATH}${invoice.id}`);
  } catch (error) {
    applyServerErrors(error, sentRows);
    showFormError(error, 'The invoice could not be saved.');
  } finally {
    submitButton.disabled = false;
  }
}

document.getElementById('add-line')
  .addEventListener('click', () => addRow(true));
form.addEventListener('submit', submitForm);
form.addEventListener('input', recalculate);

applyDefaultDates();
addRow();
loadClients();
