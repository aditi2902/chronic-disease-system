import { format } from 'date-fns';

const SEVERITY_STYLE = {
  CRITICAL:    { icon: '🚨', color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
  HIGH:        { icon: '⚠️', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  TREND_ALERT: { icon: '📈', color: '#a78bfa', bg: 'rgba(167,139,250,0.12)' },
  OK:          { icon: '✓',  color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
};

export default function AlertLog({ alerts, onResolve, showResolve = false }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="alert-log-empty">
        <span>🎉</span>
        <p>No alerts on record</p>
      </div>
    );
  }

  return (
    <div className="alert-log">
      {alerts.map((alert) => {
        const style = SEVERITY_STYLE[alert.severity] || SEVERITY_STYLE.OK;
        return (
          <div
            key={alert.id}
            className={`alert-item ${alert.resolved ? 'resolved' : 'active'}`}
            style={{ borderLeft: `3px solid ${alert.resolved ? '#374151' : style.color}` }}
          >
            <div className="alert-header">
              <span className="alert-icon">{style.icon}</span>
              <span
                className="alert-severity"
                style={{ color: alert.resolved ? '#6b7280' : style.color }}
              >
                {alert.severity}
              </span>
              <span className="alert-type-pill">{alert.alert_type}</span>
              {alert.resolved && <span className="resolved-tag">Resolved</span>}
            </div>
            <p className="alert-message">{alert.message}</p>
            <div className="alert-footer">
              <span className="alert-time">
                {format(new Date(alert.triggered_at), 'MMM d, yyyy · h:mm a')}
              </span>
              {showResolve && !alert.resolved && onResolve && (
                <button
                  className="btn-resolve"
                  onClick={() => onResolve(alert.id)}
                >
                  Mark Resolved
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
