interface GrowwLogoProps {
  size?: number;
  showWordmark?: boolean;
  className?: string;
}

export function GrowwLogo({ size = 32, showWordmark = false, className = "" }: GrowwLogoProps) {
  return (
    <span className={`groww-logo ${className}`.trim()} aria-label="Groww">
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden
      >
        <rect width="32" height="32" rx="9" fill="url(#groww-logo-gradient)" />
        <path
          d="M9 21L14.5 14.5L18.5 18.5L23 11"
          stroke="white"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M20 11H23V14"
          stroke="white"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <defs>
          <linearGradient id="groww-logo-gradient" x1="4" y1="4" x2="28" y2="28">
            <stop stopColor="#5367F5" />
            <stop offset="1" stopColor="#3948D5" />
          </linearGradient>
        </defs>
      </svg>
      {showWordmark && <span className="groww-logo-wordmark">groww</span>}
    </span>
  );
}
