export function ScanlineOverlay() {
  return (
    <div 
      className="pointer-events-none absolute inset-0 z-20 opacity-10"
      style={{
        backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, #00ff00 2px, #00ff00 4px)',
      }}
    />
  );
}
