import React from 'react';

/** Shared Threat Intel logo used by the landing, auth, and app shells. */
export function BrandLogo({ size = 26, className = '' }) {
  return (
    <span
      className={className}
      aria-hidden="true"
      style={{
        display: 'block',
        width: size,
        height: size,
        overflow: 'hidden',
        borderRadius: Math.max(4, size * 0.18),
        flex: '0 0 auto',
      }}
    >
      <img
        src="/sentinel_forge_logo.jpg"
        alt=""
        width={size * 1.5}
        height={size * 1.5}
        style={{
          display: 'block',
          maxWidth: 'none',
          transform: 'translate(-16.6667%, -16.6667%)',
          objectFit: 'cover',
        }}
      />
    </span>
  );
}
