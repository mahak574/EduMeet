import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import {
  LayoutDashboard,
  BrainCircuit,
  Users2,
  Video,
  FileSpreadsheet,
  User as UserIcon,
  ShieldCheck,
} from 'lucide-react';

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  exact?: boolean;
}

const AUTHENTICATED_NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, exact: true },
  { to: '/diagnostic', label: 'Diagnostic Quiz', icon: BrainCircuit },
  { to: '/matching', label: 'Match', icon: Users2 },
  { to: '/sessions', label: 'Sessions', icon: Video },
  { to: '/mistakes', label: 'Review', icon: FileSpreadsheet },
  { to: '/profile', label: 'Profile', icon: UserIcon },
];

const PUBLIC_NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, exact: true },
];

export const Sidebar: React.FC = () => {
  const { isAuthenticated } = useAuthStore();

  // Logged-out visitors see ONLY the Overview tab. Protected tabs are completely hidden.
  const navItems = isAuthenticated ? AUTHENTICATED_NAV_ITEMS : PUBLIC_NAV_ITEMS;

  return (
    <aside className="w-64 flex-shrink-0 hidden md:flex flex-col justify-between border-r border-white/10 glass-panel min-h-[calc(100vh-4rem)] p-4 space-y-1">
      <div>
        <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          {isAuthenticated ? 'Workspace' : 'Explore'}
        </div>
        <div className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.exact}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-brand-500/15 text-brand-300 border border-brand-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </div>
              </NavLink>
            );
          })}
        </div>
      </div>

      <div className="pt-8 px-2 space-y-3">
        <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 leading-relaxed space-y-1.5">
          <div className="flex items-center gap-1.5 font-semibold text-slate-300">
            <ShieldCheck className="w-3.5 h-3.5 text-brand-400" />
            <span>Reciprocal Teaching</span>
          </div>
          <p>
            Learn by teaching. 25 minutes teaching, 25 minutes learning, 10 minutes peer quiz. No public leaderboards.
          </p>
        </div>
      </div>
    </aside>
  );
};
