import { Helmet } from 'react-helmet-async';

/**
 * Dynamic meta tags component for SEO.
 * Updates page title, description, and social sharing tags.
 */
export default function MetaTags({
  title = 'Adajoon - Free Live TV & Radio Streaming',
  description = 'Stream thousands of free live TV channels and radio stations from around the world. No registration required.',
  image = 'https://adajoon.com/og-image.jpg',
  url,
  type = 'website',
}) {
  const fullUrl = url || (typeof window !== 'undefined' ? window.location.href : 'https://adajoon.com');
  
  return (
    <Helmet>
      {/* Primary Meta Tags */}
      <title>{title}</title>
      <meta name="title" content={title} />
      <meta name="description" content={description} />

      {/* Open Graph / Facebook */}
      <meta property="og:type" content={type} />
      <meta property="og:url" content={fullUrl} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={image} />
      <meta property="og:site_name" content="Adajoon" />

      {/* Twitter */}
      <meta property="twitter:card" content="summary_large_image" />
      <meta property="twitter:url" content={fullUrl} />
      <meta property="twitter:title" content={title} />
      <meta property="twitter:description" content={description} />
      <meta property="twitter:image" content={image} />

      {/* Canonical URL */}
      <link rel="canonical" href={fullUrl} />
    </Helmet>
  );
}

/**
 * Meta tags for TV channel page
 */
export function ChannelMetaTags({ channel }) {
  if (!channel) return <MetaTags />;
  
  const title = `Watch ${channel.name} Live - Free Streaming on Adajoon`;
  const description = `Stream ${channel.name} live and free. ${channel.categories ? `Category: ${channel.categories}. ` : ''}${channel.country ? `Country: ${channel.country}. ` : ''}Watch now on Adajoon.`;
  const url = `https://adajoon.com/tv/channel/${channel.id}`;
  const image = channel.logo || 'https://adajoon.com/og-image.jpg';
  
  return <MetaTags title={title} description={description} url={url} image={image} type="video.other" />;
}

/**
 * Meta tags for radio station page
 */
export function RadioMetaTags({ station }) {
  if (!station) return <MetaTags />;
  
  const title = `Listen to ${station.name} Online - Free Radio on Adajoon`;
  const description = `Stream ${station.name} live and free. ${station.tags ? `Genre: ${station.tags}. ` : ''}${station.country ? `Country: ${station.country}. ` : ''}Listen now on Adajoon.`;
  const url = `https://adajoon.com/radio/station/${station.id}`;
  const image = station.favicon || station.logo || 'https://adajoon.com/og-image.jpg';
  
  return <MetaTags title={title} description={description} url={url} image={image} type="music.radio_station" />;
}

/**
 * Meta tags for browse/category pages
 */
export function BrowseMetaTags({ mode, category, country, query }) {
  let title = mode === 'radio' ? 'Browse Radio Stations' : 'Browse TV Channels';
  let description = mode === 'radio' 
    ? 'Discover and stream thousands of free online radio stations from around the world.'
    : 'Watch thousands of free live TV channels from around the world.';
  
  if (query) {
    title = `${query} - Search Results on Adajoon`;
    description = `Search results for "${query}". ${description}`;
  } else if (category) {
    title = `${category} ${mode === 'radio' ? 'Radio Stations' : 'TV Channels'} - Adajoon`;
    description = `Browse ${category} ${mode === 'radio' ? 'radio stations' : 'TV channels'} and stream for free.`;
  } else if (country) {
    title = `${country} ${mode === 'radio' ? 'Radio' : 'TV'} - Adajoon`;
    description = `Stream ${mode === 'radio' ? 'radio stations' : 'TV channels'} from ${country} live and free.`;
  }
  
  return <MetaTags title={title} description={description} />;
}
