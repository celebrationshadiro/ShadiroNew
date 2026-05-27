import { MetadataRoute } from 'next';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://shadiro.com';

  // Fetch active vendors list from the backend database dynamically
  let vendors = [];
  try {
    const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';
    const res = await fetch(`${backendUrl}/api/vendors?limit=1000`, { next: { revalidate: 3600 } });
    if (res.ok) {
      const json = await res.json();
      if (json.success && json.data && json.data.items) {
        vendors = json.data.items;
      }
    }
  } catch (e) {
    console.error('Failed to generate dynamic sitemap vendors list:', e);
  }

  const vendorUrls = vendors.map((v: any) => ({
    url: `${baseUrl}/vendors/${v.id}`,
    lastModified: v.updated_at || new Date().toISOString(),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }));

  // Categories & Cities mappings to support static index crawls
  const categories = ['photography', 'catering', 'decoration', 'venue', 'music', 'makeup', 'mehendi', 'transport'];
  const cities = ['mumbai', 'delhi', 'bangalore', 'chennai', 'pune', 'hyderabad', 'kolkata', 'jaipur'];
  
  const categoryUrls: MetadataRoute.Sitemap = [];
  for (const city of cities) {
    for (const cat of categories) {
      categoryUrls.push({
        url: `${baseUrl}/vendors/${city}/${cat}`,
        lastModified: new Date().toISOString(),
        changeFrequency: 'daily' as const,
        priority: 0.9,
      });
    }
  }

  return [
    {
      url: baseUrl,
      lastModified: new Date().toISOString(),
      changeFrequency: 'always' as const,
      priority: 1.0,
    },
    {
      url: `${baseUrl}/grocery`,
      lastModified: new Date().toISOString(),
      changeFrequency: 'always' as const,
      priority: 0.9,
    },
    ...categoryUrls,
    ...vendorUrls,
  ];
}
