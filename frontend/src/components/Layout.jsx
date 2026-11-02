import { Link, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, Camera, ClipboardCheck, BarChart3, FileText,
  CreditCard, Users, ClipboardList, Settings, LogOut, Menu, X
} from 'lucide-react';
import { useState } from 'react';

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', roles: ['admin', 'plant_head', 'supervisor'] },
  { to: '/inspect', icon: Camera, label: 'Inspect', roles: ['admin', 'plant_head', 'supervisor'] },
  { to: '/review', icon: ClipboardCheck, label: 'Review Queue', roles: ['admin', 'plant_head'] },
  { to: '/batches', icon: BarChart3, label: 'Batches', roles: ['admin', 'plant_head', 'supervisor'] },
  { to: '/reports', icon: FileText, label: 'Reports', roles: ['admin', 'plant_head'] },
  { to: '/billing', icon: CreditCard, label: 'Billing', roles: ['admin', 'plant_head'] },
  { to: '/journey', icon: Users, label: 'Journey', roles: ['admin', 'plant_head'] },
  { to: '/validation', icon: ClipboardList, label: 'Validation', roles: ['admin'] },
  { to: '/models', icon: Settings, label: 'Models', roles: ['admin'] },
  { to: '/plants', icon: Settings, label: 'Plant Setup', roles: ['admin', 'plant_head'] },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const filtered = NAV.filter((n) => n.roles.includes(user?.role));

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-gray-50">
      {/* Mobile header */}
      <div className="md:hidden flex items-center justify-between bg-[#1a365d] text-white px-4 py-3">
        <span className="font-bold text-lg">VisionQC</span>
        <button onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside className={`${menuOpen ? 'block' : 'hidden'} md:block w-full md:w-56 bg-[#1a365d] text-white flex-shrink-0`}>
        <div className="hidden md:block px-4 py-5 border-b border-blue-800">
          <h1 className="text-xl font-bold">VisionQC</h1>
          <p className="text-blue-200 text-xs mt-1">AI Quality Inspection</p>
        </div>
        <nav className="py-2">
          {filtered.map((n) => {
            const Icon = n.icon;
            const active = location.pathname === n.to;
            return (
              <Link
                key={n.to}
                to={n.to}
                onClick={() => setMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                  active ? 'bg-blue-800 text-white' : 'text-blue-100 hover:bg-blue-800/50'
                }`}
              >
                <Icon size={18} />
                {n.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-blue-800 px-4 py-3 mt-auto">
          <p className="text-xs text-blue-200 truncate">{user?.full_name}</p>
          <p className="text-xs text-blue-300 capitalize">{user?.role?.replace('_', ' ')}</p>
          <button onClick={logout} className="flex items-center gap-2 text-xs text-blue-200 hover:text-white mt-2">
            <LogOut size={14} /> Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-4 md:p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
