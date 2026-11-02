// Pure calculation primitives. Never turn synthetic examples into published NBA estimates.
export function impliedProbability(decimalOdds) {
  if (!Number.isFinite(decimalOdds) || decimalOdds <= 1) throw new RangeError('decimal odds must exceed 1');
  return 1 / decimalOdds;
}
export function expectedReturn(probability, decimalOdds) {
  if (!Number.isFinite(probability) || probability < 0 || probability > 1) throw new RangeError('invalid probability');
  impliedProbability(decimalOdds);
  return probability * decimalOdds - 1; // net per unit stake, before additional costs
}
export function correlation(xs, ys) {
  if (!Array.isArray(xs) || !Array.isArray(ys) || xs.length !== ys.length || xs.length < 3 ||
      [...xs, ...ys].some(x => !Number.isFinite(x))) throw new RangeError('invalid paired samples');
  const mx = xs.reduce((a,b) => a+b,0)/xs.length;
  const my = ys.reduce((a,b) => a+b,0)/ys.length;
  const cov = xs.reduce((s,x,i) => s+(x-mx)*(ys[i]-my),0);
  const vx = xs.reduce((s,x) => s+(x-mx)**2,0);
  const vy = ys.reduce((s,y) => s+(y-my)**2,0);
  if (vx === 0 || vy === 0) return null; // undefined, not zero
  return cov / Math.sqrt(vx*vy);
}
export function jointHitRate(pairedOutcomes) {
  if (!Array.isArray(pairedOutcomes) || pairedOutcomes.length < 1 || pairedOutcomes.some(pair =>
    !Array.isArray(pair) || pair.length !== 2 || pair.some(v => typeof v !== 'boolean')))
    throw new RangeError('invalid paired outcomes');
  return pairedOutcomes.filter(([a,b]) => a && b).length / pairedOutcomes.length;
}
export function releaseGate(record) {
  const fields = ['authorizedData','sourceUrls','pregameCutoff','injuryResolved','settlementKnown',
    'executableOdds','calibratedHoldout','incrementalSkill','dependenceValidated','loggedBeforeOutcome','riskBounded'];
  return fields.every(key => record?.[key] === true);
}
