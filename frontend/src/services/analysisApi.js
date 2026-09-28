/**
 * API service for communicating with backend news verification endpoints.
 */

export async function analyzeClaimApi({ title, text }) {
  const apiBaseUrl = import.meta.env.VITE_API_URL || '';
  const res = await fetch(`${apiBaseUrl}/api/analyze`, {
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

export async function analyzeClaimStreamApi({ title, text, onProgress }) {
  const apiBaseUrl = import.meta.env.VITE_API_URL || '';
  const res = await fetch(`${apiBaseUrl}/api/analyze/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ title, text }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Analysis request failed.');
  }
  if (!res.body) throw new Error('Streaming is unavailable in this browser.');

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let completedResult = null;

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const events = buffer.split('\n\n');
    buffer = events.pop() || '';

    for (const eventText of events) {
      const dataLine = eventText.split('\n').find((line) => line.startsWith('data: '));
      if (!dataLine) continue;
      const payload = JSON.parse(dataLine.slice(6));
      onProgress?.(payload);
      if (payload.event === 'analysis_completed') completedResult = payload.result;
      if (payload.event === 'analysis_failed') throw new Error(payload.error || 'Analysis failed.');
    }
    if (done) break;
  }

  if (!completedResult) throw new Error('Analysis stream ended before a result was received.');
  return completedResult;
}
