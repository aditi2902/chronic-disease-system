import { useState, useEffect } from 'react';
import { loginUser, registerDoctor, registerPatient, getDoctorsList } from '../api/client';
import { useAuth } from '../auth/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const [isRegistering, setIsRegistering] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'patient', doctor_id: '' });
  const [doctors, setDoctors] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchDoctors = async () => {
    try {
      const { data } = await getDoctorsList();
      setDoctors(data);
      if (data.length > 0 && !form.doctor_id) {
        setForm(prev => ({ ...prev, doctor_id: data[0].id.toString() }));
      }
    } catch (err) {
      console.error('Error fetching doctors:', err);
    }
  };

  useEffect(() => {
    if (isRegistering && form.role === 'patient') {
      fetchDoctors();
    }
  }, [isRegistering, form.role]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      if (isRegistering) {
        if (form.role === 'doctor') {
          const { data } = await registerDoctor(form.name, form.email, form.password);
          login(data);
        } else {
          if (!form.doctor_id) {
            throw new Error('Please select a doctor. If no doctor exists, please sign up as a doctor first.');
          }
          const { data } = await registerPatient(form.name, form.email, form.password, parseInt(form.doctor_id, 10));
          login(data);
        }
      } else {
        const { data } = await loginUser(form.email, form.password, form.role);
        login(data);
      }
    } catch (err) {
      if (err.response?.data?.detail) {
        const details = err.response.data.detail;
        if (Array.isArray(details)) {
          setError(details.map(d => d.msg).join(', '));
        } else {
          setError(details);
        }
      } else {
        setError(err.message || 'Authentication failed. Check inputs.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (role) => {
    setIsRegistering(false);
    if (role === 'doctor') {
      setForm({ email: 'doctor@chronic.dev', password: 'doctor123', role: 'doctor' });
    } else if (role === 'alice') {
      setForm({ email: 'alice@chronic.dev', password: 'patient123', role: 'patient' });
    } else if (role === 'bob') {
      setForm({ email: 'bob@chronic.dev', password: 'patient123', role: 'patient' });
    } else if (role === 'carol') {
      setForm({ email: 'carol@chronic.dev', password: 'patient123', role: 'patient' });
    }
  };

  return (
    <div className="login-page">
      <div className="login-bg-orb orb-1" />
      <div className="login-bg-orb orb-2" />
      <div className="login-bg-orb orb-3" />

      <div className="login-card">
        <div className="login-logo">
          <div className="logo-icon">⚕</div>
          <h1 className="logo-name">Chronic</h1>
          <p className="logo-tagline">Diabetic Patient Monitoring System</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit} id="login-form">
          <div className="form-group">
            <label htmlFor="login-role">Role</label>
            <div className="role-toggle">
              <button
                type="button"
                id="role-patient"
                className={`role-btn ${form.role === 'patient' ? 'active' : ''}`}
                onClick={() => setForm({ ...form, role: 'patient' })}
              >
                Patient
              </button>
              <button
                type="button"
                id="role-doctor"
                className={`role-btn ${form.role === 'doctor' ? 'active' : ''}`}
                onClick={() => setForm({ ...form, role: 'doctor' })}
              >
                Doctor
              </button>
            </div>
          </div>

          {isRegistering && (
            <div className="form-group">
              <label htmlFor="login-name">Full Name</label>
              <input
                id="login-name"
                name="name"
                type="text"
                value={form.name || ''}
                onChange={handleChange}
                placeholder="John Doe"
                required
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              placeholder="your@email.com"
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </div>

          {isRegistering && form.role === 'patient' && (
            <div className="form-group">
              <label htmlFor="login-doctor">Primary Doctor</label>
              {doctors.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '6px' }}>
                  No doctors registered yet. Please register a doctor first.
                </div>
              ) : (
                <select
                  id="login-doctor"
                  name="doctor_id"
                  value={form.doctor_id}
                  onChange={handleChange}
                  required
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.1)',
                    background: 'rgba(255,255,255,0.05)',
                    color: 'white',
                    outline: 'none',
                    fontSize: '14px'
                  }}
                >
                  {doctors.map(doc => (
                    <option key={doc.id} value={doc.id} style={{ background: '#0b1628', color: 'white' }}>
                      {doc.name}
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          {error && <div className="form-error">{error}</div>}

          <button
            id="login-submit"
            type="submit"
            className="btn-primary btn-full"
            disabled={loading}
          >
            {loading ? <span className="spinner" /> : (isRegistering ? 'Sign Up' : 'Sign In')}
          </button>
        </form>

        <div className="auth-toggle-link" style={{ textAlign: 'center', marginTop: '20px', fontSize: '14px' }}>
          {isRegistering ? (
            <span>
              Already have an account?{' '}
              <button
                type="button"
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-blue)',
                  cursor: 'pointer',
                  fontWeight: '600',
                  padding: 0,
                  fontSize: 'inherit',
                  fontFamily: 'inherit'
                }}
                onClick={() => {
                  setIsRegistering(false);
                  setForm({ name: '', email: '', password: '', role: 'patient', doctor_id: '' });
                  setError('');
                }}
              >
                Sign In
              </button>
            </span>
          ) : (
            <span>
              Don't have an account?{' '}
              <button
                type="button"
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-blue)',
                  cursor: 'pointer',
                  fontWeight: '600',
                  padding: 0,
                  fontSize: 'inherit',
                  fontFamily: 'inherit'
                }}
                onClick={() => {
                  setIsRegistering(true);
                  setForm({ name: '', email: '', password: '', role: 'patient', doctor_id: '' });
                  setError('');
                }}
              >
                Sign Up
              </button>
            </span>
          )}
        </div>

        {!isRegistering && (
          <div className="demo-section">
            <p className="demo-label">Quick Demo Login</p>
            <div className="demo-buttons">
              <button className="demo-btn" onClick={() => fillDemo('doctor')} id="demo-doctor">
                Dr. Mitchell
              </button>
              <button className="demo-btn demo-green" onClick={() => fillDemo('alice')} id="demo-alice">
                Alice (Controlled)
              </button>
              <button className="demo-btn demo-yellow" onClick={() => fillDemo('bob')} id="demo-bob">
                Bob (Trend ↑)
              </button>
              <button className="demo-btn demo-red" onClick={() => fillDemo('carol')} id="demo-carol">
                Carol (Critical)
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
