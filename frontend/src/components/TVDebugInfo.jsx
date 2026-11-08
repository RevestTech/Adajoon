import { useDevice } from "../hooks/useDevice";

export default function TVDebugInfo() {
  const device = useDevice();

  if (!device.isTV) return null;

  return (
    <div className="tv-debug-info">
      <div className="tv-debug-badge">TV Mode</div>
      <div className="tv-debug-details">
        <div>Platform: {device.tvPlatform || 'Unknown'}</div>
        <div>Screen: {device.screenSize.width}x{device.screenSize.height}</div>
        <div>Use remote control arrows to navigate</div>
        <div>Press BACK button to go back</div>
      </div>
    </div>
  );
}
