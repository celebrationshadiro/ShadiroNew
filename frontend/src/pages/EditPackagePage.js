import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { packages as packagesApi, servicesApi, vendorProfile } from '../lib/api';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { PackageForm } from '../components/PackageForm';
import { toast } from 'sonner';

const EditPackagePage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [packageData, setPackageData] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const pkgRes = await packagesApi.getById(id);
        setPackageData(pkgRes.data);
        const vendorRes = await vendorProfile.getMyVendor();
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
        toast.error('Failed to load package');
      } finally {
        setLoading(false);
      }
    };
    if (id) load();
  }, [id]);

  const handleSubmit = async (payload) => {
    setSaving(true);
    try {
      await packagesApi.update(id, payload);
      toast.success('Package updated');
      navigate('/vendor-dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update package');
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

  if (!packageData) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <Card className="p-8 text-center bg-white rounded-2xl max-w-md">
          <p className="text-stone-600 mb-4">Package not found.</p>
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
            <h1 className="text-3xl font-bold">Edit Package</h1>
            <p className="text-stone-600">Update pricing, services, and items.</p>
          </div>
          <Button variant="ghost" onClick={() => navigate('/vendor-dashboard')}>Back</Button>
        </div>
        <PackageForm initialData={packageData} items={items} onSubmit={handleSubmit} submitting={saving} />
      </div>
    </div>
  );
};

export default EditPackagePage;
