/**
 * API service for communicating with backend news verification endpoints.
 */

export async function analyzeClaimApi({ title, text }) {
  const res = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, text }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Analysis request failed.');
  }

  return await res.json();
}
