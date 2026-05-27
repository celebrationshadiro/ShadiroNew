import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Plus } from 'lucide-react';

const PricingRulesTab = ({
  pricingRules,
  pricingSaving,
  onAddRule,
  onUpdateRule,
  onRemoveRule,
  onSaveRules,
}) => (
  <Card className="p-8 bg-white rounded-2xl">
    <div className="flex items-center justify-between gap-4 mb-6 flex-wrap">
      <div>
        <h2 className="text-2xl font-semibold">Pricing Rules</h2>
        <p className="text-stone-500 text-sm">Set seasonal and weekend multipliers for quote previews.</p>
      </div>
      <Button onClick={onAddRule} variant="outline" className="rounded-full">
        <Plus size={16} className="mr-2" /> Add Rule
      </Button>
    </div>

    {pricingRules.length === 0 ? (
      <p className="text-stone-500">No pricing rules configured yet.</p>
    ) : (
      <div className="space-y-4">
        {pricingRules.map((rule, index) => (
          <Card key={rule.id || index} className="p-4 border border-stone-100">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-stone-500">Label</label>
                <Input value={rule.label || ''} onChange={(e) => onUpdateRule(index, 'label', e.target.value)} placeholder="Peak season uplift" className="mt-1" />
              </div>
              <div>
                <label className="text-sm text-stone-500">Days of Week (comma)</label>
                <Input value={Array.isArray(rule.days_of_week) ? rule.days_of_week.join(', ') : rule.days_of_week || ''} onChange={(e) => onUpdateRule(index, 'days_of_week', e.target.value)} placeholder="sat, sun" className="mt-1" />
              </div>
              <div>
                <label className="text-sm text-stone-500">Start Date</label>
                <Input type="date" value={rule.start_date || ''} onChange={(e) => onUpdateRule(index, 'start_date', e.target.value)} className="mt-1" />
              </div>
              <div>
                <label className="text-sm text-stone-500">End Date</label>
                <Input type="date" value={rule.end_date || ''} onChange={(e) => onUpdateRule(index, 'end_date', e.target.value)} className="mt-1" />
              </div>
              <div>
                <label className="text-sm text-stone-500">Multiplier</label>
                <Input type="number" step="0.05" value={rule.multiplier ?? ''} onChange={(e) => onUpdateRule(index, 'multiplier', e.target.value)} placeholder="1.15" className="mt-1" />
              </div>
              <div>
                <label className="text-sm text-stone-500">Flat Fee (INR)</label>
                <Input type="number" value={rule.flat_fee ?? ''} onChange={(e) => onUpdateRule(index, 'flat_fee', e.target.value)} placeholder="0" className="mt-1" />
              </div>
            </div>
            <div className="flex justify-end mt-4">
              <Button variant="outline" onClick={() => onRemoveRule(index)}>Remove</Button>
            </div>
          </Card>
        ))}
      </div>
    )}

    <div className="flex justify-end mt-6">
      <Button onClick={onSaveRules} disabled={pricingSaving}>
        {pricingSaving ? 'Saving...' : 'Save Rules'}
      </Button>
    </div>
  </Card>
);

export default PricingRulesTab;
