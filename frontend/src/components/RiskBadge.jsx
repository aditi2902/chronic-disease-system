const BADGE_CONFIG = {
  LOW:      { bg: 'var(--badge-low-bg)',      color: 'var(--badge-low-color)',      icon: '●' },
  MEDIUM:   { bg: 'var(--badge-medium-bg)',   color: 'var(--badge-medium-color)',   icon: '●' },
  HIGH:     { bg: 'var(--badge-high-bg)',      color: 'var(--badge-high-color)',     icon: '▲' },
  CRITICAL: { bg: 'var(--badge-critical-bg)', color: 'var(--badge-critical-color)', icon: '⚠' },
  'NO DATA':{ bg: 'var(--badge-nodata-bg)',   color: 'var(--badge-nodata-color)',   icon: '—' },
};

export default function RiskBadge({ level, size = 'md' }) {
  const cfg = BADGE_CONFIG[level] || BADGE_CONFIG['NO DATA'];
  return (
    <span
      className={`risk-badge risk-badge-${size}`}
      style={{ background: cfg.bg, color: cfg.color }}
    >
      <span className="badge-icon">{cfg.icon}</span>
      {level}
    </span>
  );
}
