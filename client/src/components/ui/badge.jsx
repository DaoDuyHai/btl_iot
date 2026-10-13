import React from 'react';

/**
 * shadcn/ui Badge Primitive
 * Variants: default, secondary, destructive, outline, success, warning
 */
export function Badge({ 
  children, 
  variant = 'default', 
  className = '', 
  style = {},
  ...props 
}) {
  const variantStyles = {
    default: {
      background: '#fee2e2',
      color: '#991b1b',
      border: '1px solid #fecaca',
    },
    secondary: {
      background: '#f1f5f9',
      color: '#475569',
      border: '1px solid #e2e8f0',
    },
    destructive: {
      background: '#fef2f2',
      color: '#dc2626',
      border: '1px solid #fecaca',
    },
    success: {
      background: '#dcfce7',
      color: '#15803d',
      border: '1px solid #bbf7d0',
    },
    warning: {
      background: '#fffbeb',
      color: '#b45309',
      border: '1px solid #fde68a',
    },
    outline: {
      background: 'transparent',
      color: '#0f172a',
      border: '1px solid #cbd5e1',
    }
  }[variant] || {};

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '4px 10px',
        borderRadius: '9999px',
        fontSize: '12px',
        fontWeight: '700',
        letterSpacing: '0.2px',
        lineHeight: 1,
        ...variantStyles,
        ...style
      }}
      className={`shadcn-badge ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}

