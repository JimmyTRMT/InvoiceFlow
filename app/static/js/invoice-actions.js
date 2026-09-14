import { ApiError, deleteJson, getJson, postJson, putJson } from './api.js';
import { askConfirmation, showToast } from './ui.js';

export const NEXT_STATUS = {
  draft: { value: 'sent', label: 'Mark as sent' },
  sent: { value: 'paid', label: 'Mark as paid' },
};

export const REVERT_STATUS = {
  sent: { value: 'draft', label: 'Move back to draft' },
  paid: { value: 'sent', label: 'Reopen as unpaid' },
};

export function reportFailure(error, fallback) {
  showToast(error instanceof ApiError ? error.message : fallback, 'error');
}

// PUT replaces the whole invoice, so every field has to travel even when
// only one of them changes.
function fullPayload(invoice, overrides) {
  return {
    client_id: invoice.client_id,
    issue_date: invoice.issue_date,
    due_date: invoice.due_date,
    status: invoice.status,
    tax_rate: invoice.tax_rate,
    notes: invoice.notes || '',
    line_items: invoice.line_items.map((item) => ({
      description: item.description,
      quantity: item.quantity,
      unit_price: item.unit_price,
    })),
    ...overrides,
  };
}

function isoDate(date) {
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 10);
}

// The copy keeps the original payment delay but starts from today.
function shiftedDates(invoice) {
  const issued = new Date(`${invoice.issue_date}T00:00:00`);
  const due = new Date(`${invoice.due_date}T00:00:00`);
  const today = new Date();
  const copyDue = new Date(today.getTime() + (due - issued));
  return { issue_date: isoDate(today), due_date: isoDate(copyDue) };
}

// The list payload carries no line items, so the full invoice is read
// back before anything is rewritten from it.
export function loadFull(invoice) {
  return invoice.line_items ? Promise.resolve(invoice)
    : getJson(`/invoices/${invoice.id}`);
}

export async function changeStatus(invoice, status) {
  // Only this move has its own endpoint, which stamps the payment date.
  if (status === 'paid') {
    return postJson(`/invoices/${invoice.id}/mark-paid`);
  }
  const full = await loadFull(invoice);
  return putJson(`/invoices/${invoice.id}`, fullPayload(full, { status }));
}

export async function duplicate(invoice) {
  const full = await loadFull(invoice);
  return postJson('/invoices', fullPayload(full, {
    status: 'draft',
    ...shiftedDates(full),
  }));
}

export function confirmDelete(invoice) {
  return askConfirmation({
    title: 'Delete this invoice',
    message: `${invoice.number} and all of its lines will be removed.`,
    confirmLabel: 'Delete invoice',
  });
}

export function remove(invoice) {
  return deleteJson(`/invoices/${invoice.id}`);
}
