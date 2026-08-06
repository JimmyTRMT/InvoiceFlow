// Thin client over the JSON API.

export class ApiError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ApiError';
  }
}

// Read an endpoint and turn every possible failure into one error type.
export async function getJson(path) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      headers: { Accept: 'application/json' },
    });
  } catch (error) {
    throw new ApiError('The server could not be reached.');
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError((payload && payload.message) || 'The request failed.');
  }
  return payload;
}
