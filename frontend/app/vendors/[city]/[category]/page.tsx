import React from 'react';
import Image from 'next/image';
import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { LocalBusinessSchema, BreadcrumbSchema } from '../../../../components/seo/JsonLd';

export const revalidate = 21600; // Revalidate every 6 hours (ISR)

const VALID_CATEGORIES = ['photography', 'catering', 'decoration', 'venue', 'music', 'makeup', 'mehendi', 'transport'];
const VALID_CITIES = ['mumbai', 'delhi', 'bangalore', 'chennai', 'pune', 'hyderabad', 'kolkata', 'jaipur'];

interface PageParams {
  city: string;
  category: string;
}

export async function generateStaticParams() {
  const params: PageParams[] = [];
  for (const city of VALID_CITIES) {
    for (const category of VALID_CATEGORIES) {
      params.push({
        city: city,
        category: category,
      });
    }
  }
  return params;
}

export async function generateMetadata({ params }: { params: PageParams }): Promise<Metadata> {
  const city = params.city.charAt(0).toUpperCase() + params.city.slice(1);
  const category = params.category.charAt(0).toUpperCase() + params.category.slice(1);

  return {
    title: `Best ${category} in ${city} | Shadiro`,
    description: `Discover the top-rated professional ${category} services in ${city}. View verified pricing, packages, portfolios, reviews, and book directly.`,
    alternates: {
      canonical: `https://shadiro.com/vendors/${params.city}/${params.category}`,
    },
  };
}

async function getVendors(city: string, category: string) {
  const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';
  try {
    const res = await fetch(
      `${backendUrl}/api/vendors?category_id=cat-${category}&city=${city.charAt(0).toUpperCase() + city.slice(1)}`,
      { next: { revalidate: 21600 } }
    );
    if (!res.ok) return [];
    const json = await res.json();
    return json.success && json.data ? json.data : [];
  } catch (e) {
    console.error('Error fetching vendors in SSG page:', e);
    return [];
  }
}

export default async function CategoryListingPage({ params }: { params: PageParams }) {
  const city = params.city.toLowerCase();
  const category = params.category.toLowerCase();

  if (!VALID_CITIES.includes(city) || !VALID_CATEGORIES.includes(category)) {
    notFound();
  }

  const formattedCity = city.charAt(0).toUpperCase() + city.slice(1);
  const formattedCategory = category.charAt(0).toUpperCase() + category.slice(1);
  const vendors = await getVendors(city, category);

  const breadcrumbs = [
    { name: 'Home', item: 'https://shadiro.com' },
    { name: 'Vendors', item: 'https://shadiro.com/vendors' },
    { name: formattedCity, item: `https://shadiro.com/vendors/${city}` },
    { name: formattedCategory, item: `https://shadiro.com/vendors/${city}/${category}` },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Structural Schema Scripts */}
      <BreadcrumbSchema items={breadcrumbs} />
      {vendors.map((v: any) => (
        <LocalBusinessSchema
          key={v.id}
          id={v.id}
          name={v.business_name}
          image={v.portfolio_images?.[0] || 'https://res.cloudinary.com/eventapp/portfolio/placeholder.jpg'}
          priceRange={`₹${v.base_price_paise / 100} - ₹${(v.base_price_paise * 3) / 100}`}
          telephone={v.phone}
          address={{
            city: v.city || formattedCity,
            state: v.state || 'Maharashtra',
            country: 'India',
            postalCode: v.pincode,
          }}
          ratingValue={v.rating || 4.5}
          reviewCount={v.total_reviews || 12}
        />
      ))}

      {/* Hero Header */}
      <div className="mb-10 text-center md:text-left">
        <h1 className="font-serif text-3xl md:text-5xl font-bold text-stone-900 mb-4" id="listing-title">
          Best {formattedCategory} in {formattedCity} | Shadiro
        </h1>
        <p className="text-stone-600 text-lg max-w-3xl">
          Browse verified professional {category} profiles in {formattedCity}. Compare base rates, portfolios, and customer testimonials.
        </p>
      </div>

      {/* Grid List */}
      {vendors.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-xl p-12 text-center max-w-xl mx-auto my-12 shadow-sm">
          <span className="text-4xl mb-4 block">🏝️</span>
          <h2 className="text-xl font-bold mb-2">No Verified Vendors Found</h2>
          <p className="text-stone-500 mb-6">
            We are currently onboarding {category} professionals in {formattedCity}. Check back soon or browse nearby regions.
          </p>
          <a
            href="/vendors"
            className="inline-block bg-pink-600 hover:bg-pink-700 text-white font-medium px-6 py-3 rounded-lg transition"
            aria-label="Back to general listing"
          >
            Explore Other Categories
          </a>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" role="region" aria-labelledby="listing-title">
          {vendors.map((vendor: any) => (
            <article
              key={vendor.id}
              className="bg-white border border-stone-200 rounded-xl overflow-hidden hover:shadow-xl transition-all duration-300 flex flex-col group"
            >
              <div className="relative h-56 w-full bg-stone-100 overflow-hidden">
                <Image
                  src={vendor.portfolio_images?.[0] || 'https://res.cloudinary.com/eventapp/portfolio/placeholder.jpg'}
                  alt={vendor.business_name}
                  fill
                  sizes="(max-w-768px) 100vw, 33vw"
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                  priority={true}
                />
                {vendor.is_featured && (
                  <span className="absolute top-4 left-4 bg-amber-500 text-white font-bold text-xs uppercase px-3 py-1.5 rounded-full shadow-md z-10">
                    Featured
                  </span>
                )}
              </div>

              <div className="p-6 flex-grow flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-stone-500 uppercase tracking-wide">
                      {vendor.category_type || category}
                    </span>
                    <div className="flex items-center space-x-1.5">
                      <span className="text-amber-500 text-lg">★</span>
                      <span className="text-sm font-bold text-stone-800">{vendor.rating || 4.5}</span>
                      <span className="text-xs text-stone-500">({vendor.total_reviews || 12})</span>
                    </div>
                  </div>
                  <h3 className="font-serif text-xl font-bold text-stone-900 mb-2 group-hover:text-pink-600 transition">
                    {vendor.business_name}
                  </h3>
                  <p className="text-stone-600 text-sm line-clamp-2 mb-4">
                    {vendor.description || `Specialized in premium ${category} services for weddings and family milestone celebrations.`}
                  </p>
                </div>

                <div className="pt-4 border-t border-stone-100 flex items-center justify-between mt-auto">
                  <div>
                    <span className="text-xs text-stone-500 block uppercase font-medium">Starting from</span>
                    <span className="text-lg font-bold text-pink-600">
                      ₹{(vendor.base_price_paise || 5000000) / 100}
                    </span>
                  </div>
                  <a
                    href={`/vendors/${vendor.id}`}
                    className="bg-stone-900 hover:bg-pink-600 text-white font-semibold text-sm px-4 py-2.5 rounded-lg transition"
                    aria-label={`View profile details for ${vendor.business_name}`}
                  >
                    View Details
                  </a>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
