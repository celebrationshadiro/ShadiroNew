import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { quotes as quotesApi, assistantApi } from '../lib/api';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from '../components/ui/sonner';

const toneOptions = [
  { value: 'formal', label: 'Formal' },
  { value: 'quick', label: 'Quick' },
  { value: 'concise', label: 'Concise' },
];

const VendorQuoteRespondPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [quote, setQuote] = useState(null);
  const [tone, setTone] = useState('formal');
  const [draftLoading, setDraftLoading] = useState(false);
  const [draftMeta, setDraftMeta] = useState(null);

  const [quotedPrice, setQuotedPrice] = useState('');
  const [responseMessage, setResponseMessage] = useState('');
  const [servicesOffered, setServicesOffered] = useState('');

  useEffect(() => {
    const loadQuote = async () => {
      setLoading(true);
      try {
        const res = await quotesApi.getAll();
        const found = res.data?.find((q) => q.id === id);
        if (!found) {
          toast.error('Quote not found');
        }
        setQuote(found || null);
        setServicesOffered((found?.requested_services || []).join(', '));
      } catch (err) {
        toast.error(err.response?.data?.detail || 'Failed to load quote');
      } finally {
        setLoading(false);
      }
    };
    loadQuote();
  }, [id]);

  const handleGenerateDraft = async () => {
    if (!quote) return;
    setDraftLoading(true);
    try {
      const res = await assistantApi.draftQuote({
        quote_id: quote.id,
        tone,
        requested_services: quote.requested_services || [],
      });
      const data = res.data;
      if (data?.draft) {
        setResponseMessage(data.draft);
      }
      if (!quotedPrice && data?.suggested_price) {
        setQuotedPrice(String(data.suggested_price));
      }
      setDraftMeta(data || null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate draft');
    } finally {
      setDraftLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!quote) return;
    if (!quotedPrice || Number.isNaN(Number(quotedPrice))) {
      toast.error('Please enter a valid price');
      return;
    }
    try {
      await quotesApi.respond(quote.id, {
        quote_id: quote.id,
        quoted_price: Number(quotedPrice),
        response_message: responseMessage || null,
        services_offered: servicesOffered
          ? servicesOffered.split(',').map((s) => s.trim()).filter(Boolean)
          : [],
      });
      toast.success('Quote response sent');
      navigate('/vendor-dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to respond to quote');
    }
  };

  if (loading) {
    return <div className="p-6">Loading quote...</div>;
  }

  if (!quote) {
    return (
      <div className="p-6">
        <p className="text-stone-600">Quote not found.</p>
        <Button className="mt-4" onClick={() => navigate('/vendor-dashboard')}>Back to Dashboard</Button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 md:px-8 py-10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-semibold">Respond to Quote</h1>
          <p className="text-stone-500">Quote ID: {quote.id.slice(0, 8)}</p>
        </div>
        <Button variant="outline" onClick={() => navigate('/vendor-dashboard')}>Back</Button>
      </div>

      <div className="grid gap-6">
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-3">Request Details</h2>
          <p className="text-stone-600">Services: {(quote.requested_services || []).join(', ') || 'Custom request'}</p>
          {quote.message && <p className="text-stone-600 mt-2">Message: {quote.message}</p>}
          {quote.attachments?.length ? (
            <div className="mt-4">
              <p className="text-sm font-medium text-stone-500">Attachments</p>
              <ul className="mt-2 space-y-1">
                {quote.attachments.map((file, idx) => (
                  <li key={`${file.url}-${idx}`} className="text-sm text-primary underline">
                    <a href={file.url} target="_blank" rel="noreferrer">{file.filename || 'Attachment'}</a>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </Card>

        <Card className="p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">Compose Response</h2>
              <p className="text-stone-500 text-sm">Use AI copilot or craft your own response.</p>
            </div>
            <div className="flex gap-3">
              <Select value={tone} onValueChange={setTone}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Tone" />
                </SelectTrigger>
                <SelectContent>
                  {toneOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button variant="outline" onClick={handleGenerateDraft} disabled={draftLoading}>
                {draftLoading ? 'Generating...' : 'Generate Draft'}
              </Button>
            </div>
          </div>

          {draftMeta && (
            <div className="mt-4 rounded-xl bg-stone-50 p-4 text-sm text-stone-600">
              <p className="font-medium text-stone-700">AI Reasoning</p>
              <p className="mt-1">{draftMeta.reasoning}</p>
              {draftMeta.upsells?.length ? (
                <p className="mt-2">Suggested add-ons: {draftMeta.upsells.join(', ')}</p>
              ) : null}
            </div>
          )}

          <div className="grid gap-4 mt-6">
            <div>
              <label className="text-sm font-medium text-stone-600">Quoted Price (INR)</label>
              <Input value={quotedPrice} onChange={(e) => setQuotedPrice(e.target.value)} placeholder="25000" className="mt-1" />
            </div>
            <div>
              <label className="text-sm font-medium text-stone-600">Services Offered</label>
              <Input value={servicesOffered} onChange={(e) => setServicesOffered(e.target.value)} placeholder="DJ, Lighting" className="mt-1" />
            </div>
            <div>
              <label className="text-sm font-medium text-stone-600">Response Message</label>
              <Textarea value={responseMessage} onChange={(e) => setResponseMessage(e.target.value)} placeholder="Write your response..." className="mt-1 min-h-[140px]" />
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <Button onClick={handleSubmit}>Send Response</Button>
            <Button variant="outline" onClick={() => setResponseMessage('')}>Clear</Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default VendorQuoteRespondPage;
