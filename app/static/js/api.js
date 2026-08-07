// Thin client over the JSON API.

const CSRF_COOKIE = 'csrf_token';
const CSRF_HEADER = 'X-CSRF-Token';
const SAFE_METHODS = ['GET', 'HEAD'];

export class ApiError extends Error {
  constructor(message, fields) {
    super(message);
    this.name = 'ApiError';
    this.fields = fields || {};
  }
}

// The server compares this value with its own cookie on every write.
function readCsrfToken() {
  const pattern = new RegExp(`(?:^|;\\s*)${CSRF_COOKIE}=([^;]*)`);
  const match = document.cookie.match(pattern);
  return match ? decodeURIComponent(match[1]) : '';
}

// Send one request and turn every possible failure into one error type.
async function request(method, path, body) {
  const headers = { Accept: 'application/json' };
  const options = { method, headers };

  if (!SAFE_METHODS.includes(method)) {
    headers[CSRF_HEADER] = readCsrfToken();
  }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(`/api${path}`, options);
  } catch (error) {
    throw new ApiError('The server could not be reached.');
  }

  if (response.status === 204) {
    return null;
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(
      (payload && payload.message) || 'The request failed.',
      payload && payload.errors
    );
  }
  return payload;
}

export const getJson = (path) => request('GET', path);
export const postJson = (path, body) => request('POST', path, body);
export const putJson = (path, body) => request('PUT', path, body);
export const deleteJson = (path) => request('DELETE', path);
