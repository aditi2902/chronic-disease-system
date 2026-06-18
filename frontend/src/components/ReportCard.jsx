import { format } from 'date-fns';
import RiskBadge from './RiskBadge';

function getRiskLevel(score) {
  if (score === null || score === undefined) return 'NO DATA';
  if (score >= 66) return 'HIGH';
  if (score >= 33) return 'MEDIUM';
  return 'LOW';
}

export default function ReportCard({ report, isDoctor = false }) {
  if (!report) {
    return (
      <div className="report-card report-empty">
        <div className="report-empty-icon">📊</div>
        <h3>No Weekly Report Yet</h3>
        <p>Reports are generated every Sunday, or a doctor can trigger one manually.</p>
      </div>
    );
  }

  const riskLevel = getRiskLevel(report.risk_score);
  let stats = {};
  try {
    stats = JSON.parse(report.json_stats);
  } catch {}

  const summary = isDoctor ? report.doctor_summary : report.llm_summary;

  return (
    <div className="report-card">
      <div className="report-header">
        <div>
          <h3 className="report-title">Weekly Health Report</h3>
          <p className="report-week">
            Week of {format(new Date(report.week_start), 'MMMM d, yyyy')}
          </p>
        </div>
        <div className="report-risk-block">
          <RiskBadge level={riskLevel} size="lg" />
          {report.risk_score !== null && (
            <span className="risk-score-number">{report.risk_score}/100</span>
          )}
        </div>
      </div>

      <div className="report-stats-grid">
        <div className="stat-chip">
          <span className="stat-label">Avg Glucose</span>
          <span className="stat-value">{stats.avg_glucose ?? '—'} mg/dL</span>
        </div>
        <div className="stat-chip">
          <span className="stat-label">Max Glucose</span>
          <span className="stat-value" style={{ color: stats.max_glucose > 300 ? '#ef4444' : stats.max_glucose > 180 ? '#f59e0b' : 'inherit' }}>
            {stats.max_glucose ?? '—'} mg/dL
          </span>
        </div>
        <div className="stat-chip">
          <span className="stat-label">Adherence</span>
          <span className="stat-value">{stats.adherence_pct !== undefined ? `${(stats.adherence_pct * 100).toFixed(0)}%` : '—'}</span>
        </div>
        <div className="stat-chip">
          <span className="stat-label">Trend Slope</span>
          <span
            className="stat-value"
            style={{ color: stats.trend_slope > 5 ? '#ef4444' : stats.trend_slope > 0 ? '#f59e0b' : '#10b981' }}
          >
            {stats.trend_slope !== undefined ? `${stats.trend_slope > 0 ? '+' : ''}${stats.trend_slope} mg/dL/day` : '—'}
          </span>
        </div>
        <div className="stat-chip">
          <span className="stat-label">Avg Sleep</span>
          <span className="stat-value">{stats.avg_sleep_hrs ?? '—'} hrs</span>
        </div>
        <div className="stat-chip">
          <span className="stat-label">Avg Exercise</span>
          <span className="stat-value">{stats.avg_exercise_min ?? '—'} min</span>
        </div>
      </div>

      {summary && (
        <div className="report-summary">
          <h4>{isDoctor ? '🩺 Clinical Note' : '💬 Your Weekly Summary'}</h4>
          <p>{summary}</p>
        </div>
      )}
    </div>
  );
}
