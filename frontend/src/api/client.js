import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('chronic_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auth
export const loginUser = (email, password, role) =>
  api.post('/auth/login', { email, password, role });

export const registerDoctor = (name, email, password) =>
  api.post('/auth/register/doctor', { name, email, password });

export const registerPatient = (name, email, password, doctor_id) =>
  api.post('/auth/register/patient', { name, email, password, doctor_id });

export const getDoctorsList = () =>
  api.get('/auth/doctors');


// Readings
export const submitReading = (data) => api.post('/readings', data);
export const getMyReadings = (days = 7) => api.get(`/readings/me?days=${days}`);
export const getMyAlerts = () => api.get('/readings/me/alerts');

// Doctor
export const getDoctorPatients = () => api.get('/doctor/patients');
export const getPatientReadings = (patientId, days = 7) =>
  api.get(`/doctor/patients/${patientId}/readings?days=${days}`);
export const getPatientAlerts = (patientId) =>
  api.get(`/doctor/patients/${patientId}/alerts`);
export const resolveAlert = (alertId) =>
  api.patch(`/doctor/alerts/${alertId}/resolve`);

// Reports
export const getLatestReport = (patientId) =>
  api.get(`/reports/${patientId}/latest`);
export const generateReport = (patientId) =>
  api.post(`/reports/${patientId}/generate`);

export default api;
