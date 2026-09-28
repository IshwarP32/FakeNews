import React from 'react';

export default function MLPrediction({ result }) {
  const prediction = result?.ml_prediction;
  if (!prediction) {
    return <section className="ml-panel ml-empty"><p>ML prediction will appear after verification.</p></section>;
  }

  return <section className="ml-panel">
    <div className="ml-panel-top"><div><p className="eyebrow">FAKE-NEWS PROBABILITY</p><strong>{prediction.fake_probability}%</strong></div><div className="probability-meta"><span>{prediction.prediction.toUpperCase()}</span><small>{prediction.learned_examples} LEARNED EXAMPLES</small></div></div>
    <div className="probability-bar"><span style={{ width: `${prediction.fake_probability}%` }} /></div>
    <div className="probability-legend"><span>0% REAL</span><span>BASELINE {prediction.baseline_fake_probability}%</span><span>100% FAKE</span></div>
  </section>;
}
