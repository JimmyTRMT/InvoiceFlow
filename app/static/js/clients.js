// Client list, search, and the dialog used to create or edit a client.

import { ApiError, deleteJson, getJson, postJson, putJson } from './api.js';
import { showToast } from './ui.js';

const SEARCH_DELAY = 250;
const FIELDS = ['name', 'email', 'company', 'address'];

const searchInput = document.getElementById('client-search');
const tableWrapper = document.getElementById('clients-table');
const tableBody = document.getElementById('clients-body');
const emptyState = document.getElementById('clients-empty');
const listError = document.getElementById('clients-error');
const rowTemplate = document.getElementById('client-row-template');

const dialog = document.getElementById('client-dialog');
const form = document.getElementById('client-form');
const dialogTitle = document.getElementById('client-dialog-title');
const submitButton = document.getElementById('client-submit');
const formError = document.getElementById('client-form-error');

const confirmDialog = document.getElementById('confirm-dialog');
const confirmMessage = document.getElementById('confirm-message');

let editingId = null;
let searchTimer = null;

function messageOf(error, fallback) {
  return error instanceof ApiError ? error.message : fallback;
}

function clearFieldErrors() {
  formError.hidden = true;
  FIELDS.forEach((name) => {
    form.querySelector(`[data-error="${name}"]`).hidden = true;
    form.elements[name].removeAttribute('aria-invalid');
  });
}

// Put the server messages back next to the inputs that caused them.
function showFormError(error) {
  clearFieldErrors();
  const fields = error instanceof ApiError ? error.fields : {};
  Object.entries(fields).forEach(([name, text]) => {
    const holder = form.querySelector(`[data-error="${name}"]`);
    if (!holder) {
      return;
    }
    holder.textContent = text;
    holder.hidden = false;
    form.elements[name].setAttribute('aria-invalid', 'true');
  });
  formError.textContent = messageOf(error, 'The client could not be saved.');
  formError.hidden = false;
}

function openForm(client) {
  editingId = client ? client.id : null;
  dialogTitle.textContent = client ? 'Edit client' : 'New client';
  submitButton.textContent = client ? 'Save changes' : 'Create client';
  clearFieldErrors();
  FIELDS.forEach((name) => {
    form.elements[name].value = client ? client[name] || '' : '';
  });
  dialog.showModal();
  form.elements.name.focus();
}

// Resolve once the dialog closes, whichever button or key closed it.
function askConfirmation(message) {
  confirmMessage.textContent = message;
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

async function removeClient(client) {
  const accepted = await askConfirmation(
    `${client.name} will be removed for good.`
  );
  if (!accepted) {
    return;
  }
  try {
    await deleteJson(`/clients/${client.id}`);
    showToast('Client deleted.');
    await loadClients();
  } catch (error) {
    showToast(
      messageOf(error, 'The client could not be deleted.'),
      'error'
    );
  }
}

function buildRow(client) {
  const row = rowTemplate.content.firstElementChild.cloneNode(true);
  const field = (name) => row.querySelector(`[data-field="${name}"]`);

  field('name').textContent = client.name;
  field('company').textContent = client.company || '';
  field('email').textContent = client.email;
  field('address').textContent = client.address || '';

  row.querySelector('[data-action="edit"]')
    .addEventListener('click', () => openForm(client));
  row.querySelector('[data-action="delete"]')
    .addEventListener('click', () => removeClient(client));
  return row;
}

function renderClients(clients, search) {
  tableBody.replaceChildren(...clients.map(buildRow));
  const isEmpty = clients.length === 0;
  tableWrapper.hidden = isEmpty;
  emptyState.hidden = !isEmpty;
  emptyState.textContent = search
    ? `No client matches ${search}.`
    : 'No client yet. Add the first one to start invoicing.';
}

async function loadClients() {
  const search = searchInput.value.trim();
  try {
    const clients = await getJson(
      `/clients?search=${encodeURIComponent(search)}`
    );
    listError.hidden = true;
    renderClients(clients, search);
  } catch (error) {
    listError.textContent = messageOf(
      error,
      'The client list could not be loaded.'
    );
    listError.hidden = false;
    tableBody.replaceChildren();
    tableWrapper.hidden = true;
    emptyState.hidden = true;
  }
}

async function submitForm(event) {
  event.preventDefault();
  const payload = Object.fromEntries(
    FIELDS.map((name) => [name, form.elements[name].value])
  );

  submitButton.disabled = true;
  try {
    if (editingId === null) {
      await postJson('/clients', payload);
      showToast('Client created.');
    } else {
      await putJson(`/clients/${editingId}`, payload);
      showToast('Client updated.');
    }
    dialog.close();
    await loadClients();
  } catch (error) {
    showFormError(error);
  } finally {
    submitButton.disabled = false;
  }
}

document.getElementById('client-new')
  .addEventListener('click', () => openForm(null));
document.getElementById('client-cancel')
  .addEventListener('click', () => dialog.close());
form.addEventListener('submit', submitForm);

searchInput.addEventListener('input', () => {
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(loadClients, SEARCH_DELAY);
});

loadClients();
