import React from 'react';

export default function ErrorMessage({ message }) {
  if (!message) return null;
  return <div className="error-panel"><strong>REQUEST ERROR</strong><p>{message}</p></div>;
}
