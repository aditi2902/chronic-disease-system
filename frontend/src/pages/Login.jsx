import { useState } from 'react';
import { loginUser } from '../api/client';
import { useAuth } from '../auth/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const [form, setForm] = useState({ email: '', password: '', role: 'patient' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await loginUser(form.email, form.password, form.role);
      login(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (role) => {
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

          {error && <div className="form-error">{error}</div>}

          <button
            id="login-submit"
            type="submit"
            className="btn-primary btn-full"
            disabled={loading}
          >
            {loading ? <span className="spinner" /> : 'Sign In'}
          </button>
        </form>

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
      </div>
    </div>
  );
}
