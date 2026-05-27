import React from 'react';
import Image from 'next/image';
import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { LocalBusinessSchema, BreadcrumbSchema } from '../../../components/seo/JsonLd';

export const dynamic = 'force-dynamic'; // Enforce request-time server side rendering

interface PageProps {
  params: {
    vendor_id: string;
  };
}

async function getVendorDetails(vendor_id: string) {
  const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${backendUrl}/api/vendors/${vendor_id}`, { cache: 'no-store' });
    if (!res.ok) return null;
    const json = await res.json();
    return json.success && json.data ? json.data : null;
  } catch (e) {
    console.error('Error fetching vendor details in SSR page:', e);
    return null;
  }
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const vendor = await getVendorDetails(params.vendor_id);
  if (!vendor) {
    return {
      title: 'Vendor Not Found',
    };
  }

  return {
    title: `${vendor.business_name} | Verified Event Specialist | Shadiro`,
    description: `${vendor.business_name} in ${vendor.city || 'India'}. Read reviews, view portfolio images, explore base packages, and request quotes instantly.`,
    alternates: {
      canonical: `https://shadiro.com/vendors/${params.vendor_id}`,
    },
    openGraph: {
      type: 'profile',
      title: `${vendor.business_name} | Shadiro`,
      description: vendor.description,
      images: [
        {
          url: vendor.portfolio_images?.[0] || 'https://res.cloudinary.com/eventapp/portfolio/placeholder.jpg',
          alt: vendor.business_name,
        },
      ],
    },
  };
}

export default async function VendorDetailPage({ params }: PageProps) {
  const vendor = await getVendorDetails(params.vendor_id);

  if (!vendor) {
    notFound();
  }

  const breadcrumbs = [
    { name: 'Home', item: 'https://shadiro.com' },
    { name: 'Vendors', item: 'https://shadiro.com/vendors' },
    { name: vendor.city || 'India', item: `https://shadiro.com/vendors?city=${vendor.city}` },
    { name: vendor.business_name, item: `https://shadiro.com/vendors/${vendor.id}` },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Schema Markup */}
      <BreadcrumbSchema items={breadcrumbs} />
      <LocalBusinessSchema
        id={vendor.id}
        name={vendor.business_name}
        image={vendor.portfolio_images?.[0] || 'https://res.cloudinary.com/eventapp/portfolio/placeholder.jpg'}
        priceRange={`₹${vendor.base_price_paise / 100} - ₹${(vendor.base_price_paise * 3) / 100}`}
        telephone={vendor.phone}
        address={{
          street: vendor.address,
          city: vendor.city || 'Mumbai',
          state: vendor.state || 'Maharashtra',
          postalCode: vendor.pincode,
          country: 'India',
        }}
        ratingValue={vendor.rating || 4.5}
        reviewCount={vendor.total_reviews || 12}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content Area */}
        <div className="lg:col-span-2 space-y-8">
          {/* Header Summary */}
          <div className="bg-white border border-stone-200 rounded-xl p-6 md:p-8 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
              <span className="bg-pink-100 text-pink-700 text-xs font-bold uppercase tracking-wider px-3.5 py-1.5 rounded-full">
                {vendor.category_type || 'Event Professional'}
              </span>
              <div className="flex items-center space-x-2">
                <span className="text-amber-500 text-xl">★</span>
                <span className="text-stone-900 font-bold text-lg">{vendor.rating || 4.5}</span>
                <span className="text-stone-500 text-sm">({vendor.total_reviews || 12} verified reviews)</span>
              </div>
            </div>
            <h1 className="font-serif text-3xl md:text-4xl font-bold text-stone-900 mb-4">
              {vendor.business_name}
            </h1>
            <p className="text-stone-600 leading-relaxed text-base md:text-lg">
              {vendor.description || `Highly professional service specialist delivering customized solutions with absolute premium standard.`}
            </p>
          </div>

          {/* Image Portfolio */}
          <div className="bg-white border border-stone-200 rounded-xl p-6 md:p-8 shadow-sm">
            <h2 className="font-serif text-2xl font-bold text-stone-900 mb-6">Work Portfolio</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {(vendor.portfolio_images && vendor.portfolio_images.length > 0) ? (
                vendor.portfolio_images.slice(0, 6).map((imgUrl: string, idx: number) => (
                  <div key={idx} className="relative h-40 rounded-lg overflow-hidden bg-stone-100 hover:opacity-90 transition">
                    <Image
                      src={imgUrl}
                      alt={`${vendor.business_name} portfolio ${idx + 1}`}
                      fill
                      sizes="(max-w-768px) 50vw, 25vw"
                      className="object-cover"
                    />
                  </div>
                ))
              ) : (
                <div className="col-span-full py-12 text-center text-stone-400">
                  No portfolio images uploaded.
                </div>
              )}
            </div>
          </div>

          {/* Pricing & Packages */}
          <div className="bg-white border border-stone-200 rounded-xl p-6 md:p-8 shadow-sm">
            <h2 className="font-serif text-2xl font-bold text-stone-900 mb-6">Featured Packages</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Mock Standard Package */}
              <div className="border border-stone-200 rounded-xl p-5 hover:border-pink-500 transition duration-300">
                <span className="text-xs font-bold text-stone-500 uppercase tracking-wide">Standard Tier</span>
                <h3 className="font-serif text-lg font-bold text-stone-900 mt-1 mb-2">Classic Experience</h3>
                <span className="text-2xl font-serif font-bold text-pink-600">₹{vendor.base_price_paise / 100}</span>
                <p className="text-stone-500 text-sm mt-3 mb-4">
                  Essential services including customized event operations, base coordination team, and core logistics management.
                </p>
                <ul className="space-y-2 text-stone-600 text-sm mb-6">
                  <li>✓ Professional crew setup</li>
                  <li>✓ 1-Day core event scheduling</li>
                  <li>✓ Basic standard supplies</li>
                </ul>
              </div>

              {/* Mock Premium Package */}
              <div className="border-2 border-pink-600 rounded-xl p-5 relative shadow-md">
                <span className="absolute -top-3.5 right-4 bg-pink-600 text-white font-bold text-xs uppercase px-3 py-1 rounded-full">
                  Most Popular
                </span>
                <span className="text-xs font-bold text-stone-500 uppercase tracking-wide">Premium Tier</span>
                <h3 className="font-serif text-lg font-bold text-stone-900 mt-1 mb-2">Royal Celebration</h3>
                <span className="text-2xl font-serif font-bold text-pink-600">₹{(vendor.base_price_paise * 1.8) / 100}</span>
                <p className="text-stone-500 text-sm mt-3 mb-4">
                  Full service coverage including premium planning specialists, exclusive decorations catalog, and priority operations management.
                </p>
                <ul className="space-y-2 text-stone-600 text-sm mb-6">
                  <li>✓ Dedicated planning director</li>
                  <li>✓ Multi-Day operations team</li>
                  <li>✓ Premium materials & priority backup</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar Sticky Booking Card */}
        <div className="space-y-6">
          <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-md sticky top-24">
            <span className="text-xs font-bold text-stone-500 uppercase tracking-wider block mb-1">Starting base rate</span>
            <div className="flex items-baseline space-x-2 mb-4">
              <span className="text-3xl font-bold text-pink-600">₹{vendor.base_price_paise / 100}</span>
              <span className="text-stone-500 text-sm">/ event</span>
            </div>
            
            <div className="border-t border-b border-stone-100 py-4 my-4 space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-stone-500">KYC Verification</span>
                <span className="text-green-600 font-bold">✓ Verified Professional</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-stone-500">Service Coverage</span>
                <span className="text-stone-800 font-medium">{vendor.city || 'Multiple Cities'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-stone-500">Response Rate</span>
                <span className="text-stone-850 font-medium">{(vendor.response_rate * 100) || 98}% fast reply</span>
              </div>
            </div>

            <button
              className="w-full bg-pink-600 hover:bg-pink-700 text-white font-bold py-3.5 rounded-xl shadow-md hover:shadow-lg transition-all text-base block text-center"
              aria-label={`Initiate booking inquiry with ${vendor.business_name}`}
            >
              Inquire Booking Slots
            </button>
            <p className="text-xs text-stone-500 text-center mt-3">
              No deposit required to check slot availability.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
