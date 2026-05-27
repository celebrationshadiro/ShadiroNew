import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { vendorProfile, packages as packagesApi, servicesApi } from '../lib/api';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { PackageForm } from '../components/PackageForm';
import { toast } from 'sonner';

const CreatePackagePage = () => {
  const navigate = useNavigate();
  const [vendor, setVendor] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const vendorRes = await vendorProfile.getMyVendor();
        setVendor(vendorRes.data);
        if (vendorRes.data?.id) {
          const itemsRes = await servicesApi.getVendorServiceItems(vendorRes.data.id);
          setItems(itemsRes.data?.items || []);
        }
      } catch (err) {
        const status = err?.response?.status;
        if (status === 404) {
          toast.error('Vendor profile not found. Please register as vendor first.');
          navigate('/vendor-register');
          return;
        }
        toast.error('Failed to load vendor profile');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSubmit = async (payload) => {
    if (!vendor?.id) return;
    setSaving(true);
    try {
      await packagesApi.create({
        ...payload,
        vendor_id: vendor.id,
      });
      toast.success('Package created');
      navigate('/vendor-dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create package');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-stone-500">Loading...</p>
      </div>
    );
  }

  if (!vendor) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <Card className="p-8 text-center bg-white rounded-2xl max-w-md">
          <p className="text-stone-600 mb-4">Vendor profile not found.</p>
          <Button onClick={() => navigate('/vendor-dashboard')}>Back to Dashboard</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-4xl mx-auto w-full px-4 md:px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Create Package</h1>
            <p className="text-stone-600">Build Basic, Standard, Premium, or Custom offerings.</p>
          </div>
          <Button variant="ghost" onClick={() => navigate('/vendor-dashboard')}>Back</Button>
        </div>
        <PackageForm initialData={{}} items={items} onSubmit={handleSubmit} submitting={saving} />
      </div>
    </div>
  );
};

export default CreatePackagePage;
