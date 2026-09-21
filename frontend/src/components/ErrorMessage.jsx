import React from 'react';

export default function ErrorMessage({ message }) {
  if (!message) return null;
  return (
    <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
      <span>⚠</span> {message}
    </div>
  );
}
