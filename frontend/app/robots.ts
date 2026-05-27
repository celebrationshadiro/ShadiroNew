import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://shadiro.com';

  return {
    rules: {
      userAgent: '*',
      allow: [
        '/',
        '/vendors/',
        '/vendors/*/*',
        '/events/',
        '/grocery/',
        '/grocery/*',
      ],
      disallow: [
        '/dashboard/',
        '/checkout/',
        '/chat/',
        '/api/',
        '/_next/',
      ],
    },
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
