export const formatCurrency = (amount) => {
  const value = Number(amount || 0);
  const safeValue = Number.isFinite(value) ? value : 0;
  return `\u20B9${safeValue.toLocaleString('en-IN')}`;
};

