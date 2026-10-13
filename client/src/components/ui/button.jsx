import React from 'react';

/**
 * shadcn/ui Button Primitive
 * Variants: default (PTIT Red), secondary, destructive, outline, ghost
 */
export function Button({ 
  children, 
  variant = 'default', 
  size = 'default', 
  className = '', 
  disabled = false,
  style = {},
  ...props 
}) {
  const variantStyles = {
    default: {
      background: 'linear-gradient(135deg, #b91c1c 0%, #dc2626 100%)',
      color: '#ffffff',
      border: 'none',
      boxShadow: '0 4px 12px rgba(185, 28, 28, 0.25)',
    },
    secondary: {
      background: '#f1f5f9',
      color: '#334155',
      border: '1px solid #e2e8f0',
    },
    destructive: {
      background: '#dc2626',
      color: '#ffffff',
      border: 'none',
      boxShadow: '0 4px 12px rgba(220, 38, 38, 0.3)',
    },
    outline: {
      background: 'transparent',
      color: '#0f172a',
      border: '1px solid #e2e8f0',
    },
    success: {
      background: 'linear-gradient(135deg, #15803d 0%, #16a34a 100%)',
      color: '#ffffff',
      border: 'none',
      boxShadow: '0 4px 12px rgba(22, 163, 74, 0.25)',
    },
    ghost: {
      background: 'transparent',
      color: '#475569',
      border: 'none',
    }
  }[variant] || {};

  const sizeStyles = {
    sm: { padding: '6px 12px', fontSize: '12px', borderRadius: '8px' },
    default: { padding: '10px 18px', fontSize: '14px', borderRadius: '12px' },
    lg: { padding: '14px 24px', fontSize: '16px', borderRadius: '14px' },
  }[size] || {};

  return (
    <button
      disabled={disabled}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        fontWeight: '700',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
        userSelect: 'none',
        ...variantStyles,
        ...sizeStyles,
        ...style
      }}
      className={`shadcn-btn ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

