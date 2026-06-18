import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../auth/AuthContext';
import {
  getDoctorPatients, getPatientReadings, getPatientAlerts,
  getLatestReport, generateReport, resolveAlert
} from '../api/client';
import GlucoseChart from '../components/GlucoseChart';
import RiskBadge from '../components/RiskBadge';
import AlertLog from '../components/AlertLog';
import ReportCard from '../components/ReportCard';

export default function DoctorDashboard() {
  const { user, logout } = useAuth();
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patientReadings, setPatientReadings] = useState([]);
  const [patientAlerts, setPatientAlerts] = useState([]);
  const [patientReport, setPatientReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [reportGenerating, setReportGenerating] = useState(false);
  const [activeView, setActiveView] = useState('list'); // 'list' | 'detail'
  const [detailTab, setDetailTab] = useState('overview');

  const fetchPatients = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await getDoctorPatients();
      setPatients(data);
    } catch (err) {
      console.error('Failed to fetch patients:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchPatients(); }, [fetchPatients]);

  const openPatient = async (patient) => {
    setSelectedPatient(patient);
    setActiveView('detail');
    setDetailLoading(true);
    setDetailTab('overview');
    try {
      const [readingsRes, alertsRes] = await Promise.all([
        getPatientReadings(patient.id, 7),
        getPatientAlerts(patient.id),
      ]);
      setPatientReadings(readingsRes.data);
      setPatientAlerts(alertsRes.data);
      try {
        const reportRes = await getLatestReport(patient.id);
        setPatientReport(reportRes.data);
      } catch {
        setPatientReport(null);
      }
    } catch (err) {
      console.error('Failed to fetch patient details:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await resolveAlert(alertId);
      setPatientAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, resolved: true } : a))
      );
      // Refresh patient list to update open_alerts count
      fetchPatients();
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedPatient) return;
    setReportGenerating(true);
    try {
      const { data } = await generateReport(selectedPatient.id);
      setPatientReport(data);
    } catch (err) {
      console.error('Failed to generate report:', err);
    } finally {
      setReportGenerating(false);
    }
  };

  const totalAlerts = patients.reduce((acc, p) => acc + p.open_alerts, 0);
  const criticalCount = patients.filter(p => p.risk_badge === 'CRITICAL' || p.risk_badge === 'HIGH').length;

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">⚕</span>
          <span className="brand-name">Chronic</span>
        </div>

        <div className="sidebar-doctor-stats">
          <div className="ds-stat">
            <span className="ds-value">{patients.length}</span>
            <span className="ds-label">Patients</span>
          </div>
          <div className="ds-stat">
            <span className="ds-value" style={{ color: totalAlerts > 0 ? '#ef4444' : '#10b981' }}>
              {totalAlerts}
            </span>
            <span className="ds-label">Open Alerts</span>
          </div>
          <div className="ds-stat">
            <span className="ds-value" style={{ color: criticalCount > 0 ? '#f59e0b' : '#10b981' }}>
              {criticalCount}
            </span>
            <span className="ds-label">High Risk</span>
          </div>
        </div>

        {activeView === 'detail' && (
          <button
            id="back-to-list"
            className="nav-item"
            onClick={() => { setActiveView('list'); setSelectedPatient(null); }}
          >
            <span className="nav-icon">←</span>
            <span>Back to Patients</span>
          </button>
        )}

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">{user.name[0]}</div>
            <div>
              <p className="user-name">{user.name}</p>
              <p className="user-role">Doctor</p>
            </div>
          </div>
          <button id="logout-btn" className="btn-logout" onClick={logout}>Sign Out</button>
        </div>
      </aside>

      <main className="main-content">
        {loading ? (
          <div className="loading-screen"><div className="loader" /></div>
        ) : activeView === 'list' ? (
          <div className="tab-content">
            <div className="page-header">
              <h2>Patient Overview</h2>
              <p className="page-sub">Sorted by risk level — critical patients appear first.</p>
            </div>

            <div className="patient-grid">
              {patients.length === 0 ? (
                <div className="empty-state">
                  <p>No patients assigned yet.</p>
                </div>
              ) : patients.map((patient) => (
                <div
                  key={patient.id}
                  id={`patient-card-${patient.id}`}
                  className={`patient-card ${patient.risk_badge === 'CRITICAL' || patient.risk_badge === 'HIGH' ? 'flagged' : ''}`}
                  onClick={() => openPatient(patient)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && openPatient(patient)}
                >
                  <div className="patient-card-header">
                    <div className="patient-avatar">{patient.name[0]}</div>
                    <div>
                      <p className="patient-name">{patient.name}</p>
                      <p className="patient-email">{patient.email}</p>
                    </div>
                    <RiskBadge level={patient.risk_badge} />
                  </div>
                  <div className="patient-card-stats">
                    <div className="pc-stat">
                      <span className="pc-label">Latest Glucose</span>
                      <span
                        className="pc-value"
                        style={{
                          color: patient.latest_glucose > 300 ? '#ef4444'
                            : patient.latest_glucose > 180 ? '#f59e0b'
                            : '#10b981'
                        }}
                      >
                        {patient.latest_glucose?.toFixed(1) ?? '—'} mg/dL
                      </span>
                    </div>
                    <div className="pc-stat">
                      <span className="pc-label">Last Reading</span>
                      <span className="pc-value">{patient.latest_date ?? '—'}</span>
                    </div>
                    <div className="pc-stat">
                      <span className="pc-label">Open Alerts</span>
                      <span
                        className="pc-value"
                        style={{ color: patient.open_alerts > 0 ? '#ef4444' : '#94a3b8' }}
                      >
                        {patient.open_alerts}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Detail View */
          <div className="tab-content">
            {detailLoading ? (
              <div className="loading-screen"><div className="loader" /></div>
            ) : (
              <>
                <div className="detail-header">
                  <div className="detail-patient-info">
                    <div className="detail-avatar">{selectedPatient?.name[0]}</div>
                    <div>
                      <h2>{selectedPatient?.name}</h2>
                      <p>{selectedPatient?.email}</p>
                    </div>
                    <RiskBadge level={selectedPatient?.risk_badge} size="lg" />
                  </div>
                  <button
                    id="generate-report-btn"
                    className="btn-secondary"
                    onClick={handleGenerateReport}
                    disabled={reportGenerating}
                  >
                    {reportGenerating ? <span className="spinner" /> : '⚡ Generate Report Now'}
                  </button>
                </div>

                {/* Detail tabs */}
                <div className="detail-tabs">
                  {[
                    { id: 'overview', label: '📊 Overview' },
                    { id: 'alerts',   label: `🔔 Alerts (${patientAlerts.filter(a => !a.resolved).length})` },
                    { id: 'report',   label: '📋 Report' },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      id={`detail-tab-${tab.id}`}
                      className={`detail-tab-btn ${detailTab === tab.id ? 'active' : ''}`}
                      onClick={() => setDetailTab(tab.id)}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {detailTab === 'overview' && (
                  <>
                    <div className="card">
                      <h3 className="card-title">7-Day Glucose History</h3>
                      <GlucoseChart readings={patientReadings} height={260} />
                    </div>
                    <div className="readings-table card">
                      <h3 className="card-title">Reading Log</h3>
                      <table id="readings-table">
                        <thead>
                          <tr>
                            <th>Date</th>
                            <th>Glucose</th>
                            <th>Weight</th>
                            <th>Sleep</th>
                            <th>Exercise</th>
                            <th>Medication</th>
                          </tr>
                        </thead>
                        <tbody>
                          {patientReadings.length === 0 ? (
                            <tr><td colSpan="6" className="empty-row">No readings in past 7 days</td></tr>
                          ) : [...patientReadings].reverse().map((r) => (
                            <tr key={r.id}>
                              <td>{r.date}</td>
                              <td style={{
                                color: r.glucose_mg_dl > 300 ? '#ef4444'
                                  : r.glucose_mg_dl > 180 ? '#f59e0b' : '#10b981',
                                fontWeight: 600
                              }}>
                                {r.glucose_mg_dl} mg/dL
                              </td>
                              <td>{r.weight_kg ? `${r.weight_kg} kg` : '—'}</td>
                              <td>{r.sleep_hrs ? `${r.sleep_hrs} hrs` : '—'}</td>
                              <td>{r.exercise_min ? `${r.exercise_min} min` : '—'}</td>
                              <td>{r.medication_taken ? '✅' : '❌'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}

                {detailTab === 'alerts' && (
                  <div className="card">
                    <h3 className="card-title">Alert History</h3>
                    <AlertLog
                      alerts={patientAlerts}
                      onResolve={handleResolveAlert}
                      showResolve={true}
                    />
                  </div>
                )}

                {detailTab === 'report' && (
                  <ReportCard report={patientReport} isDoctor={true} />
                )}
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
