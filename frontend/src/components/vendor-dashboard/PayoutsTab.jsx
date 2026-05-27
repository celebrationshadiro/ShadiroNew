import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';

const formatCurrency = (amount) => {
  const value = Number(amount || 0);
  return `₹${value.toLocaleString('en-IN')}`;
};

const PayoutsTab = ({
  earnings,
  payouts,
  payoutAmount,
  payoutSubmitting,
  onPayoutAmountChange,
  onRequestPayout,
}) => (
  <>
    <Card className="p-6 bg-white rounded-2xl border border-stone-100 mb-6">
      <h2 className="text-xl font-semibold mb-2">Request Payout</h2>
      <p className="text-sm text-stone-600 mb-4">
        Available balance: {formatCurrency(earnings?.payout_balance || 0)} · Withdrawn total: {formatCurrency(earnings?.withdrawn_total || 0)}
      </p>
      <div className="flex flex-col md:flex-row gap-3">
        <Input type="number" placeholder="Enter amount" value={payoutAmount} onChange={(e) => onPayoutAmountChange(e.target.value)} />
        <Button onClick={onRequestPayout} disabled={payoutSubmitting}>
          {payoutSubmitting ? 'Submitting...' : 'Request Payout'}
        </Button>
      </div>
    </Card>

    <Card className="p-6 bg-white rounded-2xl border border-stone-100">
      <h3 className="text-lg font-semibold mb-4">Payout History</h3>
      {payouts.length === 0 ? (
        <p className="text-sm text-stone-500">No payout requests yet.</p>
      ) : (
        <div className="space-y-3">
          {payouts.map((p) => (
            <div key={p.id} className="flex items-center justify-between border-b border-stone-100 pb-2">
              <div>
                <p className="font-medium">{formatCurrency(p.amount)}</p>
                <p className="text-xs text-stone-500">{new Date(p.requested_at || Date.now()).toLocaleString()}</p>
              </div>
              <span className="text-xs uppercase tracking-wide text-stone-600">{p.status}</span>
            </div>
          ))}
        </div>
      )}
    </Card>
  </>
);

export default PayoutsTab;
