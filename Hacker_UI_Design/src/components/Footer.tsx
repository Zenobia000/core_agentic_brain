import { useState, useEffect } from 'react';

export function Footer() {
  const [showCursor, setShowCursor] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setShowCursor((prev) => !prev);
    }, 530);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-4 border-t border-[#00ff00] px-4 py-2">
      <span className="text-[#00ff00] text-glow">manus&gt;</span>
      <div className="flex-1 relative">
        <input
          type="text"
          className="w-full bg-transparent text-[#00ff00] outline-none placeholder-[#00ff00] placeholder-opacity-40 text-glow"
          placeholder=""
        />
        {showCursor && (
          <div className="absolute left-0 top-0 h-5 w-2 bg-[#00ff00] animate-pulse" />
        )}
      </div>
      <span className="text-[#00ff00] opacity-60 text-glow">Ctrl+P for commands</span>
    </div>
  );
}
