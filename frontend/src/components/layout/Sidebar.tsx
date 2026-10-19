import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BrainCircuit,
  Users2,
  Video,
  FileSpreadsheet,
  User as UserIcon,
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, exact: true },
  { to: '/diagnostic', label: 'Diagnostic Quizzes', icon: BrainCircuit },
  { to: '/matching', label: 'Peer Matching', icon: Users2 },
  { to: '/sessions', label: 'Live Session Room', icon: Video },
  { to: '/mistakes', label: 'Mistake Journal', icon: FileSpreadsheet },
  { to: '/profile', label: 'Profile & Goals', icon: UserIcon },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 flex-shrink-0 hidden md:block border-r border-white/10 glass-panel min-h-[calc(100vh-4rem)] p-4 space-y-1">
      <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
        Navigation
      </div>
      {NAV_ITEMS.map((item) => {
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

      <div className="pt-8 px-3">
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
          <p className="font-semibold text-slate-300 mb-1">Core Principle:</p>
          Peer teaching without competition. No public leaderboards or rankings.
        </div>
      </div>
    </aside>
  );
};
