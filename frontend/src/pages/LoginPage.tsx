import { FormEvent, useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      const destination = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(destination || '/dashboard', { replace: true });
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : 'No fue posible iniciar sesión');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex-1 flex items-center justify-center px-6 py-12 bg-[#FBFBFA]">
      <form onSubmit={handleSubmit} className="w-full max-w-sm bg-white border border-[#EAEAEA] rounded-xl p-8 space-y-5">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-[#787774]">TalentMatch</p>
          <h1 className="mt-2 text-2xl font-serif font-semibold">Iniciar sesión</h1>
          <p className="mt-2 text-sm text-[#666666]">Accede al panel de preselección.</p>
        </div>
        <label className="block text-sm">
          Correo
          <input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="mt-1 w-full border border-[#D1D1CF] rounded-md px-3 py-2" />
        </label>
        <label className="block text-sm">
          Contraseña
          <input required type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-1 w-full border border-[#D1D1CF] rounded-md px-3 py-2" />
        </label>
        {error && <p role="alert" className="text-sm text-[#9F2F2D]">{error}</p>}
        <button disabled={isSubmitting} className="w-full py-2.5 rounded-md bg-[#111111] text-white text-sm disabled:opacity-50">
          {isSubmitting ? 'Ingresando...' : 'Ingresar'}
        </button>
      </form>
    </main>
  );
}
