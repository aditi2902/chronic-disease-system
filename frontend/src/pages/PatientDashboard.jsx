import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../auth/AuthContext';
import { submitReading, getMyReadings, getMyAlerts, getLatestReport } from '../api/client';
import GlucoseChart from '../components/GlucoseChart';
import AlertLog from '../components/AlertLog';
import ReportCard from '../components/ReportCard';

const today = () => new Date().toISOString().split('T')[0];

export default function PatientDashboard() {
  const { user, logout } = useAuth();
  const [readings, setReadings] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [report, setReport] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitResult, setSubmitResult] = useState(null);

  const [form, setForm] = useState({
    date: today(),
    glucose_mg_dl: '',
    weight_kg: '',
    sleep_hrs: '',
    exercise_min: '',
    medication_taken: false,
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [readingsRes, alertsRes] = await Promise.all([
        getMyReadings(7),
        getMyAlerts(),
      ]);
      setReadings(readingsRes.data);
      setAlerts(alertsRes.data);
      try {
        const reportRes = await getLatestReport(user.user_id);
        setReport(reportRes.data);
      } catch {
        setReport(null);
      }
    } catch (err) {
      console.error('Error fetching patient data:', err);
    } finally {
      setLoading(false);
    }
  }, [user.user_id]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((f) => ({ ...f, [name]: type === 'checkbox' ? checked : value }));
    setSubmitResult(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitLoading(true);
    setSubmitResult(null);
    try {
      const payload = {
        date: form.date,
        glucose_mg_dl: parseFloat(form.glucose_mg_dl),
        weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
        sleep_hrs: form.sleep_hrs ? parseFloat(form.sleep_hrs) : null,
        exercise_min: form.exercise_min ? parseFloat(form.exercise_min) : null,
        medication_taken: form.medication_taken,
      };
      const { data } = await submitReading(payload);
      setSubmitResult({ type: 'success', data });
      setForm({ ...form, glucose_mg_dl: '', weight_kg: '', sleep_hrs: '', exercise_min: '', medication_taken: false });
      fetchData();
    } catch (err) {
      const detail = err.response?.data?.detail || 'Submission failed. Please try again.';
      setSubmitResult({ type: 'error', message: detail });
    } finally {
      setSubmitLoading(false);
    }
  };

  const latestReading = readings[readings.length - 1];
  const glucoseStatus = latestReading
    ? latestReading.glucose_mg_dl > 300 ? { label: 'CRITICAL', color: '#ef4444' }
    : latestReading.glucose_mg_dl > 180 ? { label: 'ELEVATED', color: '#f59e0b' }
    : { label: 'NORMAL', color: '#10b981' }
    : null;

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">⚕</span>
          <span className="brand-name">Chronic</span>
        </div>
        <nav className="sidebar-nav">
          {[
            { id: 'dashboard', icon: '📊', label: 'Dashboard' },
            { id: 'log',       icon: '✏️', label: 'Log Reading' },
            { id: 'alerts',    icon: '🔔', label: `Alerts ${alerts.filter(a => !a.resolved).length > 0 ? `(${alerts.filter(a=>!a.resolved).length})` : ''}` },
            { id: 'report',    icon: '📋', label: 'Weekly Report' },
          ].map((item) => (
            <button
              key={item.id}
              id={`nav-${item.id}`}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">{user.name[0]}</div>
            <div>
              <p className="user-name">{user.name}</p>
              <p className="user-role">Patient</p>
            </div>
          </div>
          <button id="logout-btn" className="btn-logout" onClick={logout}>Sign Out</button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {loading ? (
          <div className="loading-screen"><div className="loader" /></div>
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <div className="tab-content">
                <div className="page-header">
                  <h2>Good {getGreeting()}, {user.name.split(' ')[0]}! 👋</h2>
                  <p className="page-sub">Here's your glucose overview for the past 7 days.</p>
                </div>

                {/* Stats row */}
                <div className="stats-row">
                  <div className="stat-card">
                    <span className="stat-card-label">Latest Glucose</span>
                    {latestReading ? (
                      <>
                        <span className="stat-card-value" style={{ color: glucoseStatus.color }}>
                          {latestReading.glucose_mg_dl.toFixed(1)}
                        </span>
                        <span className="stat-card-unit">mg/dL</span>
                        <span className="stat-card-badge" style={{ background: glucoseStatus.color + '22', color: glucoseStatus.color }}>
                          {glucoseStatus.label}
                        </span>
                      </>
                    ) : <span className="stat-card-empty">No data</span>}
                  </div>
                  <div className="stat-card">
                    <span className="stat-card-label">Open Alerts</span>
                    <span className="stat-card-value" style={{ color: alerts.filter(a => !a.resolved).length > 0 ? '#ef4444' : '#10b981' }}>
                      {alerts.filter(a => !a.resolved).length}
                    </span>
                    <span className="stat-card-unit">active</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-card-label">Readings This Week</span>
                    <span className="stat-card-value">{readings.length}</span>
                    <span className="stat-card-unit">of 7 days</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-card-label">Risk Score</span>
                    <span className="stat-card-value" style={{ color: report?.risk_score > 66 ? '#ef4444' : report?.risk_score > 33 ? '#f59e0b' : '#10b981' }}>
                      {report?.risk_score ?? '—'}
                    </span>
                    <span className="stat-card-unit">{report ? '/100' : 'no report'}</span>
                  </div>
                </div>

                <div className="chart-section card">
                  <h3 className="card-title">7-Day Glucose Trend</h3>
                  <GlucoseChart readings={readings} height={280} />
                </div>

                {/* Quick log CTA if no reading today */}
                {!readings.find(r => r.date === today()) && (
                  <div className="cta-banner">
                    <span>📝</span>
                    <div>
                      <strong>Log today's reading</strong>
                      <p>You haven't logged a reading for today yet.</p>
                    </div>
                    <button className="btn-primary" onClick={() => setActiveTab('log')}>
                      Log Now
                    </button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'log' && (
              <div className="tab-content">
                <div className="page-header">
                  <h2>Log Daily Reading</h2>
                  <p className="page-sub">Record your health metrics for today.</p>
                </div>
                <div className="card log-card">
                  <form id="reading-form" onSubmit={handleSubmit}>
                    <div className="log-grid">
                      <div className="form-group">
                        <label htmlFor="log-date">Date</label>
                        <input
                          id="log-date" name="date" type="date"
                          value={form.date} onChange={handleFormChange} required
                        />
                      </div>
                      <div className="form-group highlight-input">
                        <label htmlFor="log-glucose">
                          Glucose (mg/dL) <span className="required">*</span>
                        </label>
                        <input
                          id="log-glucose" name="glucose_mg_dl" type="number"
                          step="0.1" min="1" max="1000"
                          value={form.glucose_mg_dl} onChange={handleFormChange}
                          placeholder="e.g. 120" required
                          className="input-large"
                        />
                        {form.glucose_mg_dl && (
                          <div className="glucose-preview" style={{
                            color: form.glucose_mg_dl > 300 ? '#ef4444'
                              : form.glucose_mg_dl > 180 ? '#f59e0b' : '#10b981'
                          }}>
                            {form.glucose_mg_dl > 300 ? '⚠ CRITICAL range'
                              : form.glucose_mg_dl > 180 ? '↑ Elevated'
                              : '✓ Normal range'}
                          </div>
                        )}
                      </div>
                      <div className="form-group">
                        <label htmlFor="log-weight">Weight (kg)</label>
                        <input id="log-weight" name="weight_kg" type="number"
                          step="0.1" value={form.weight_kg} onChange={handleFormChange}
                          placeholder="e.g. 70.5"
                        />
                      </div>
                      <div className="form-group">
                        <label htmlFor="log-sleep">Sleep (hours)</label>
                        <input id="log-sleep" name="sleep_hrs" type="number"
                          step="0.5" min="0" max="24"
                          value={form.sleep_hrs} onChange={handleFormChange}
                          placeholder="e.g. 7.5"
                        />
                      </div>
                      <div className="form-group">
                        <label htmlFor="log-exercise">Exercise (minutes)</label>
                        <input id="log-exercise" name="exercise_min" type="number"
                          min="0" value={form.exercise_min} onChange={handleFormChange}
                          placeholder="e.g. 30"
                        />
                      </div>
                      <div className="form-group medication-group">
                        <label>Medication Taken</label>
                        <label className="toggle-label" htmlFor="log-medication">
                          <input
                            id="log-medication" name="medication_taken" type="checkbox"
                            checked={form.medication_taken} onChange={handleFormChange}
                            className="toggle-input"
                          />
                          <div className="toggle-track">
                            <div className="toggle-thumb" />
                          </div>
                          <span>{form.medication_taken ? 'Yes ✓' : 'No'}</span>
                        </label>
                      </div>
                    </div>

                    {submitResult && (
                      <div className={`submit-result ${submitResult.type}`}>
                        {submitResult.type === 'success' ? (
                          <>
                            <span>✅ Reading logged successfully!</span>
                            {submitResult.data.alert && (
                              <span className="alert-notice">
                                ⚠ Alert triggered: {submitResult.data.alert.severity}
                              </span>
                            )}
                          </>
                        ) : (
                          <span>❌ {submitResult.message}</span>
                        )}
                      </div>
                    )}

                    <button
                      id="submit-reading"
                      type="submit"
                      className="btn-primary btn-submit"
                      disabled={submitLoading}
                    >
                      {submitLoading ? <span className="spinner" /> : 'Submit Reading'}
                    </button>
                  </form>
                </div>
              </div>
            )}

            {activeTab === 'alerts' && (
              <div className="tab-content">
                <div className="page-header">
                  <h2>My Alerts</h2>
                  <p className="page-sub">
                    {alerts.filter(a => !a.resolved).length} open · {alerts.filter(a => a.resolved).length} resolved
                  </p>
                </div>
                <div className="card">
                  <AlertLog alerts={alerts} />
                </div>
              </div>
            )}

            {activeTab === 'report' && (
              <div className="tab-content">
                <div className="page-header">
                  <h2>Weekly Report</h2>
                  <p className="page-sub">AI-generated summary of your past 7 days.</p>
                </div>
                <ReportCard report={report} isDoctor={false} />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  return 'evening';
}
