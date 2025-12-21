export type EvalDetail = {
  key: string;
  earned: number;
  max: number;
  note?: string;
};

export type EvalResult = {
  totalEarned: number;
  totalMax: number;
  details: EvalDetail[];
};

// Minimal, heuristic evaluator for Physics P1 friction question.
// This is not a grader; it estimates potential marks based on presence of key ideas.
export function evaluatePhysicsP1Answer(text: string): EvalResult {
  const t = (text || "").toLowerCase();

  // Method marks for forces (3): weight mg, normal, friction opposing
  const hasWeight = /\bmg\b|\bweight\b/.test(t);
  const hasNormal = /\bnormal\b|\bn\b(?![a-z])/.test(t);
  const hasFriction = /\bfriction\b|\bmu\b|\bμ\b/.test(t);
  let fbdEarned = [hasWeight, hasNormal, hasFriction].filter(Boolean).length;
  if (fbdEarned > 3) fbdEarned = 3;

  // Application of ΣF = ma (4): mentions Newton's second law, ΣF = ma, friction model f = μmg, final a = (F - μmg)/m
  const hasNewton2 = /newton|second\s+law/.test(t) || /f\s*=\s*ma|\u03a3f\s*=\s*ma|sigma\s*f\s*=\s*ma/.test(t);
  const hasFrictionModel = /f\s*=\s*μmg|f\s*=\s*mu\s*mg/.test(t);
  const hasFinalA = /a\s*=\s*\(\s*f\s*-\s*μ?mu?\s*mg\s*\)\s*\/\s*m|a\s*=\s*\(\s*f\s*-\s*mu\s*mg\s*\)\s*\/\s*m|a\s*=\s*\(\s*f\s*-\s*μmg\s*\)\s*\/\s*m|a\s*=\s*\(\s*f\s*-\s*mu\s*mg\s*\)\s*\/\s*m/.test(t)
    || /a\s*=\s*\(\s*f\s*-\s*μ?mg\s*\)\s*\/\s*m/.test(t)
    || /a\s*=\s*\(\s*f\s*-\s*μ?\s*mg\s*\)\s*\/\s*m/.test(t)
    || /a\s*=\s*\(\s*f\s*-\s*μ?mu?\s*mg\s*\)\s*\/\s*m/.test(t)
    || /a\s*=\s*\(\s*f\s*-\s*μ?\s*mg\s*\)\s*\/\s*m/.test(t)
    || /a\s*=\s*\(\s*f\s*-\s*mu\s*mg\s*\)\s*\/\s*m/.test(t)
    || /a\s*=\s*\(\s*f\s*-\s*μmg\s*\)\s*\/\s*m/.test(t)
    || /a\s*=\s*\(\s*f\s*-\s*mu\s*mg\s*\)\s*\/\s*m/.test(t)
    || /a\s*=\s*\(\s*f\s*-\s*μ\s*mg\s*\)\s*\/\s*m/.test(t)
    || /a\s*=\s*\(\s*f\s*-\s*mu\s*mg\s*\)\s*\/\s*m/.test(t)
    || /a\s*=\s*\(\s*f\s*-\s*μmg\s*\)\s*\/\s*m/.test(t);
  const hasSumF = /\u03a3\s*f\s*=\s*ma|sigma\s*f\s*=\s*ma|sum\s*f\s*=\s*ma|\bf\s*=\s*ma\b/.test(t);

  let appEarned = 0;
  if (hasNewton2) appEarned += 1;
  if (hasSumF) appEarned += 1;
  if (hasFrictionModel) appEarned += 1;
  if (hasFinalA || /a\s*=\s*\(\s*f\s*-\s*μ?mu?\s*mg\s*\)\s*\/\s*m|a\s*=\s*\(\s*f\s*-\s*mu\s*mg\s*\)\s*\/\s*m|a\s*=\s*\(\s*f\s*-\s*μmg\s*\)\s*\/\s*m/.test(t)) appEarned += 1;
  if (appEarned > 4) appEarned = 4;

  const details: EvalDetail[] = [
    { key: "Free-body diagram", earned: fbdEarned, max: 3, note: "Forces: weight mg, normal, friction" },
    { key: "Apply ΣF = ma", earned: appEarned, max: 4, note: "Use friction model and derive a = (F - μmg)/m" },
  ];

  const totalEarned = fbdEarned + appEarned;
  const totalMax = 7;

  return { totalEarned, totalMax, details };
}
