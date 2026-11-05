import { NavLink, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface HeaderProps {
  apiUrl: string;
}

export const Header = ({ apiUrl }: HeaderProps) => {
  const { user, logout } = useAuth();
  return (
    <header className="w-full border-b border-[#EAEAEA] bg-white/90 backdrop-blur-sm sticky top-0 z-40">
      <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Brand identity */}
        <Link to="/dashboard" className="flex items-center gap-3 group">
          <div className="w-7 h-7 rounded-md bg-[#111111] text-white flex items-center justify-center font-mono text-xs font-semibold group-hover:bg-[#333333] transition-colors">
            TM
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-semibold text-base text-[#111111] tracking-tight">TalentMatch</span>
            <span className="text-xs text-[#787774] font-mono hidden sm:inline">v1.5 · Paso 5</span>
          </div>
        </Link>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-2">
          <NavLink
            to="/dashboard"
            end
            className={({ isActive }) =>
              `text-xs font-medium px-3 py-1.5 rounded-md transition-all ${
                isActive
                  ? 'bg-[#F4F4F2] text-[#111111] font-semibold'
                  : 'text-[#666666] hover:text-[#111111] hover:bg-[#F9F9F8]'
              }`
            }
          >
            Dashboard
          </NavLink>

          <NavLink
            to="/job-offers"
            className={({ isActive }) =>
              `text-xs font-medium px-3 py-1.5 rounded-md transition-all ${
                isActive
                  ? 'bg-[#F4F4F2] text-[#111111] font-semibold'
                  : 'text-[#666666] hover:text-[#111111] hover:bg-[#F9F9F8]'
              }`
            }
          >
            Ofertas Laborales
          </NavLink>

          <NavLink
            to="/system-status"
            className={({ isActive }) =>
              `text-xs font-medium px-3 py-1.5 rounded-md transition-all ${
                isActive
                  ? 'bg-[#F4F4F2] text-[#111111] font-semibold'
                  : 'text-[#666666] hover:text-[#111111] hover:bg-[#F9F9F8]'
              }`
            }
          >
            Estado del Sistema
          </NavLink>

          {/* Right Swagger API link */}
          <div className="hidden md:flex items-center gap-2 pl-2 ml-2 border-l border-[#EAEAEA]">
            {user && <span className="text-[11px] text-[#666666]">{user.email}</span>}
            <button type="button" onClick={logout} className="text-xs text-[#555555] hover:text-[#111111]">Salir</button>
            <a
              href={`${apiUrl}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-[#555555] hover:text-[#111111] font-mono px-2.5 py-1 rounded border border-[#EAEAEA] hover:border-[#CCCCCC] transition-all"
            >
              Swagger Docs ↗
            </a>
          </div>
        </nav>
      </div>
    </header>
  );
};
