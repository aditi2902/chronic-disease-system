import { AuthProvider, useAuth } from './auth/AuthContext';
import Login from './pages/Login';
import PatientDashboard from './pages/PatientDashboard';
import DoctorDashboard from './pages/DoctorDashboard';

function AppRouter() {
  const { user, isLoggedIn } = useAuth();

  if (!isLoggedIn) return <Login />;
  if (user.role === 'doctor') return <DoctorDashboard />;
  return <PatientDashboard />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}
