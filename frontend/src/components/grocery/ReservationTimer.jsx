import React, { useEffect, useMemo, useState } from 'react';

function toSeconds(expiresAt) {
  if (!expiresAt) return 0;
  const exp = new Date(expiresAt).getTime();
  if (Number.isNaN(exp)) return 0;
  const left = Math.floor((exp - Date.now()) / 1000);
  return Math.max(0, left);
}

function formatMMSS(totalSeconds) {
  const s = Math.max(0, Number(totalSeconds || 0));
  const mm = String(Math.floor(s / 60)).padStart(2, '0');
  const ss = String(s % 60).padStart(2, '0');
  return `${mm}:${ss}`;
}

export default function ReservationTimer({
  expiresAt,
  onExpire,
}) {
  const [secondsLeft, setSecondsLeft] = useState(toSeconds(expiresAt));
  const warning = secondsLeft > 0 && secondsLeft <= 120;

  useEffect(() => {
    setSecondsLeft(toSeconds(expiresAt));
    if (!expiresAt) return undefined;
    const id = setInterval(() => {
      setSecondsLeft((prev) => {
        const next = Math.max(0, prev - 1);
        if (prev > 0 && next === 0 && typeof onExpire === 'function') onExpire();
        return next;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [expiresAt, onExpire]);

  const panelClass = useMemo(
    () =>
      warning
        ? 'border-red-300 bg-red-50 text-red-700'
        : 'border-emerald-200 bg-emerald-50 text-emerald-700',
    [warning],
  );

  return (
    <div className={`rounded-lg border p-3 ${panelClass}`}>
      <p className="text-xs uppercase tracking-wide text-stone-600">Reservation Timer</p>
      <p className="text-2xl font-semibold">{formatMMSS(secondsLeft)}</p>
      {warning ? <p className="text-xs">Lock expire hone wala hai</p> : null}
      {secondsLeft === 0 ? <p className="text-xs">Time expired - items released</p> : null}
    </div>
  );
}

