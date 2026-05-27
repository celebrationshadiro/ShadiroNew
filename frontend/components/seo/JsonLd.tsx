import React from 'react';

interface JsonLdProps {
  schema: Record<string, any>;
}

export default function JsonLd({ schema }: JsonLdProps) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

interface AddressObject {
  street?: string;
  city: string;
  state?: string;
  postalCode?: string;
  country: string;
}

export function LocalBusinessSchema({
  id,
  name,
  image,
  priceRange,
  telephone,
  address,
  ratingValue,
  reviewCount,
}: {
  id: string;
  name: string;
  image: string;
  priceRange: string;
  telephone?: string;
  address: AddressObject;
  ratingValue?: number;
  reviewCount?: number;
}) {
  const schema: Record<string, any> = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "@id": `https://shadiro.com/vendors/${id}`,
    "name": name,
    "image": image,
    "priceRange": priceRange,
    "telephone": telephone || "",
    "address": {
      "@type": "PostalAddress",
      "streetAddress": address.street || "",
      "addressLocality": address.city,
      "addressRegion": address.state || "",
      "postalCode": address.postalCode || "",
      "addressCountry": address.country,
    },
  };

  if (ratingValue !== undefined && reviewCount !== undefined && reviewCount > 0) {
    schema["aggregateRating"] = {
      "@type": "AggregateRating",
      "ratingValue": ratingValue,
      "reviewCount": reviewCount,
      "bestRating": "5",
      "worstRating": "1",
    };
  }

  return <JsonLd schema={schema} />;
}

export function EventSchema({
  name,
  startDate,
  endDate,
  locationName,
  address,
  description,
  image,
}: {
  name: string;
  startDate: string;
  endDate?: string;
  locationName: string;
  address: AddressObject;
  description: string;
  image?: string;
}) {
  const schema: Record<string, any> = {
    "@context": "https://schema.org",
    "@type": "Event",
    "name": name,
    "startDate": startDate,
    "location": {
      "@type": "Place",
      "name": locationName,
      "address": {
        "@type": "PostalAddress",
        "streetAddress": address.street || "",
        "addressLocality": address.city,
        "addressRegion": address.state || "",
        "postalCode": address.postalCode || "",
        "addressCountry": address.country,
      }
    },
    "description": description,
  };

  if (endDate) {
    schema["endDate"] = endDate;
  }
  if (image) {
    schema["image"] = image;
  }

  return <JsonLd schema={schema} />;
}

export function BreadcrumbSchema({
  items,
}: {
  items: { name: string; item: string }[];
}) {
  const schema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": items.map((item, index) => ({
      "@type": "ListItem",
      "position": index + 1,
      "name": item.name,
      "item": item.item,
    })),
  };

  return <JsonLd schema={schema} />;
}

export function ItemListSchema({
  items,
}: {
  items: { name: string; url: string; image?: string; price?: number; currency?: string }[];
}) {
  const schema = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "itemListElement": items.map((item, index) => {
      const element: Record<string, any> = {
        "@type": "ListItem",
        "position": index + 1,
        "name": item.name,
        "url": item.url,
      };
      if (item.image) {
        element["image"] = item.image;
      }
      if (item.price !== undefined) {
        element["offers"] = {
          "@type": "Offer",
          "price": item.price,
          "priceCurrency": item.currency || "INR",
        };
      }
      return element;
    }),
  };

  return <JsonLd schema={schema} />;
}
