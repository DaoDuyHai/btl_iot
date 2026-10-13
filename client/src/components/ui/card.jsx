import React from 'react';

/**
 * shadcn/ui Card Primitives
 * Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
 */
export function Card({ children, className = '', style = {}, ...props }) {
  return (
    <div
      style={{
        background: '#ffffff',
        borderRadius: '16px',
        border: '1px solid #e2e8f0',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
        overflow: 'hidden',
        ...style
      }}
      className={`shadcn-card ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '', style = {}, ...props }) {
  return (
    <div
      style={{
        padding: '20px 24px 12px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        ...style
      }}
      className={`shadcn-card-header ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({ children, className = '', style = {}, ...props }) {
  return (
    <h3
      style={{
        fontSize: '18px',
        fontWeight: '800',
        color: '#0f172a',
        margin: 0,
        ...style
      }}
      className={`shadcn-card-title ${className}`}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({ children, className = '', style = {}, ...props }) {
  return (
    <p
      style={{
        fontSize: '13px',
        color: '#64748b',
        margin: 0,
        ...style
      }}
      className={`shadcn-card-description ${className}`}
      {...props}
    >
      {children}
    </p>
  );
}

export function CardContent({ children, className = '', style = {}, ...props }) {
  return (
    <div
      style={{
        padding: '12px 24px 20px 24px',
        ...style
      }}
      className={`shadcn-card-content ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardFooter({ children, className = '', style = {}, ...props }) {
  return (
    <div
      style={{
        padding: '12px 24px 20px 24px',
        display: 'flex',
        alignItems: 'center',
        borderTop: '1px solid #f1f5f9',
        ...style
      }}
      className={`shadcn-card-footer ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

