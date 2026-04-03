/**
 * Static prerendering script for SEO-critical pages.
 * Generates static HTML for marketing and content pages.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';
const OUTPUT_DIR = path.join(__dirname, 'dist', 'prerendered');

/**
 * Fetch data from API.
 */
async function fetchApi(endpoint) {
  try {
    const response = await fetch(`${API_URL}${endpoint}`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error(`Failed to fetch ${endpoint}:`, error);
    return null;
  }
}

/**
 * Generate HTML template with meta tags.
 */
function generateHtml(title, description, url, imageUrl = null) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  
  <!-- Primary Meta Tags -->
  <title>${title}</title>
  <meta name="title" content="${title}" />
  <meta name="description" content="${description}" />
  
  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website" />
  <meta property="og:url" content="${url}" />
  <meta property="og:title" content="${title}" />
  <meta property="og:description" content="${description}" />
  ${imageUrl ? `<meta property="og:image" content="${imageUrl}" />` : ''}
  
  <!-- Twitter -->
  <meta property="twitter:card" content="summary_large_image" />
  <meta property="twitter:url" content="${url}" />
  <meta property="twitter:title" content="${title}" />
  <meta property="twitter:description" content="${description}" />
  ${imageUrl ? `<meta property="twitter:image" content="${imageUrl}" />` : ''}
  
  <!-- Redirect to main app -->
  <meta http-equiv="refresh" content="0;url=${url}" />
  <link rel="canonical" href="${url}" />
</head>
<body>
  <h1>${title}</h1>
  <p>${description}</p>
  <p>Redirecting to app...</p>
  <script>window.location.href = "${url}";</script>
</body>
</html>`;
}

/**
 * Prerender channel pages.
 */
async function prerenderChannels() {
  console.log('Fetching top channels...');
  const channels = await fetchApi('/api/channels?limit=100');
  
  if (!channels || !Array.isArray(channels)) {
    console.error('Failed to fetch channels');
    return;
  }
  
  const channelDir = path.join(OUTPUT_DIR, 'tv', 'channel');
  fs.mkdirSync(channelDir, { recursive: true });
  
  // Generate HTML for each channel
  for (const channel of channels.slice(0, 50)) {  // Top 50 channels
    const title = `${channel.name} - Live TV | Adajoon`;
    const description = `Watch ${channel.name} live stream. ${channel.categories || 'Entertainment'} from ${channel.country || 'around the world'}.`;
    const url = `https://adajoon.com/tv/channel/${channel.id}`;
    const imageUrl = channel.logo;
    
    const html = generateHtml(title, description, url, imageUrl);
    const filePath = path.join(channelDir, `${channel.id}.html`);
    
    fs.writeFileSync(filePath, html);
  }
  
  console.log(`✓ Prerendered ${Math.min(50, channels.length)} channel pages`);
}

/**
 * Prerender radio station pages.
 */
async function prerenderRadio() {
  console.log('Fetching top radio stations...');
  const stations = await fetchApi('/api/radio?limit=100');
  
  if (!stations || !Array.isArray(stations)) {
    console.error('Failed to fetch radio stations');
    return;
  }
  
  const radioDir = path.join(OUTPUT_DIR, 'radio', 'station');
  fs.mkdirSync(radioDir, { recursive: true });
  
  // Generate HTML for each station
  for (const station of stations.slice(0, 50)) {  // Top 50 stations
    const title = `${station.name} - Live Radio | Adajoon`;
    const description = `Listen to ${station.name} online. ${station.tags || 'Music'} from ${station.country || 'around the world'}.`;
    const url = `https://adajoon.com/radio/station/${station.id}`;
    const imageUrl = station.favicon;
    
    const html = generateHtml(title, description, url, imageUrl);
    const filePath = path.join(radioDir, `${station.id}.html`);
    
    fs.writeFileSync(filePath, html);
  }
  
  console.log(`✓ Prerendered ${Math.min(50, stations.length)} radio station pages`);
}

/**
 * Prerender category pages.
 */
async function prerenderCategories() {
  console.log('Fetching categories...');
  const categories = await fetchApi('/api/categories');
  
  if (!categories || !Array.isArray(categories)) {
    console.error('Failed to fetch categories');
    return;
  }
  
  const categoryDir = path.join(OUTPUT_DIR, 'category');
  fs.mkdirSync(categoryDir, { recursive: true });
  
  for (const category of categories) {
    const title = `${category.name} Channels - Live TV | Adajoon`;
    const description = `Watch live ${category.name} channels from around the world. ${category.channel_count || 0} channels available.`;
    const url = `https://adajoon.com/?cat=${encodeURIComponent(category.id)}`;
    
    const html = generateHtml(title, description, url);
    const filePath = path.join(categoryDir, `${category.id}.html`);
    
    fs.writeFileSync(filePath, html);
  }
  
  console.log(`✓ Prerendered ${categories.length} category pages`);
}

/**
 * Main prerender function.
 */
async function prerender() {
  console.log('Starting prerender...');
  console.log(`API URL: ${API_URL}`);
  console.log(`Output: ${OUTPUT_DIR}`);
  
  // Clean output directory
  if (fs.existsSync(OUTPUT_DIR)) {
    fs.rmSync(OUTPUT_DIR, { recursive: true });
  }
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  
  // Prerender pages
  await prerenderChannels();
  await prerenderRadio();
  await prerenderCategories();
  
  console.log('✓ Prerendering complete!');
}

// Run prerender
prerender().catch((error) => {
  console.error('Prerender failed:', error);
  process.exit(1);
});
