import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import InstallPrompt from '../components/InstallPrompt';

const IPHONE_SAFARI_UA =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1';
const IPAD_SAFARI_AS_MAC_UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15';
const CHROME_ON_IOS_UA =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/125.0.6422.80 Mobile/15E148 Safari/604.1';
const DESKTOP_MAC_SAFARI_UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15';
const ANDROID_CHROME_UA =
  'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36';

function setUserAgent(ua, maxTouchPoints = 0) {
  Object.defineProperty(window.navigator, 'userAgent', { value: ua, configurable: true });
  Object.defineProperty(window.navigator, 'maxTouchPoints', {
    value: maxTouchPoints,
    configurable: true,
  });
}

describe('InstallPrompt', () => {
  beforeEach(() => {
    localStorage.getItem.mockReturnValue(null);
    window.navigator.standalone = undefined;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows manual Share-sheet instructions on iPhone Safari (no beforeinstallprompt to wait for)', async () => {
    setUserAgent(IPHONE_SAFARI_UA);
    render(<InstallPrompt />);

    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());
    expect(screen.getByText(/Add to Home Screen/i)).toBeInTheDocument();
    expect(screen.queryByText('Install')).not.toBeInTheDocument();
  });

  it('treats iPadOS (UA reports as Mac, but touch-capable) as iOS Safari too', async () => {
    setUserAgent(IPAD_SAFARI_AS_MAC_UA, 5);
    render(<InstallPrompt />);

    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());
    expect(screen.getByText(/Add to Home Screen/i)).toBeInTheDocument();
  });

  it('does not show the iOS Share-sheet instructions in Chrome-on-iOS (cannot install PWAs there)', async () => {
    setUserAgent(CHROME_ON_IOS_UA);
    render(<InstallPrompt />);

    await new Promise((r) => setTimeout(r, 50));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('does not show anything on desktop Mac Safari (not a touch/mobile device)', async () => {
    setUserAgent(DESKTOP_MAC_SAFARI_UA, 0);
    render(<InstallPrompt />);

    await new Promise((r) => setTimeout(r, 50));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('still shows the real Install button on Android/Chrome via beforeinstallprompt', async () => {
    setUserAgent(ANDROID_CHROME_UA);
    render(<InstallPrompt />);

    const event = new Event('beforeinstallprompt', { cancelable: true });
    event.prompt = vi.fn();
    event.userChoice = Promise.resolve({ outcome: 'dismissed' });
    window.dispatchEvent(event);

    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());
    expect(screen.getByText('Install')).toBeInTheDocument();
    expect(screen.queryByText(/Add to Home Screen/i)).not.toBeInTheDocument();
  });

  it('shows nothing when already running standalone, even on iPhone Safari', async () => {
    setUserAgent(IPHONE_SAFARI_UA);
    window.navigator.standalone = true;
    render(<InstallPrompt />);

    await new Promise((r) => setTimeout(r, 50));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('shows nothing on iPhone Safari once previously dismissed', async () => {
    setUserAgent(IPHONE_SAFARI_UA);
    localStorage.getItem.mockReturnValue('1');
    render(<InstallPrompt />);

    await new Promise((r) => setTimeout(r, 50));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
