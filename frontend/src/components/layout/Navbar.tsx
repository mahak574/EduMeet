import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { AuthModal } from '../../features/auth/AuthModal';
import {
  GraduationCap,
  LogOut,
  User as UserIcon,
  Sparkles,
  ShieldCheck,
  ChevronDown,
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuthStore();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-40 w-full glass-panel border-b border-white/10 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-brand-500/25 group-hover:scale-105 transition-transform">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xl font-extrabold tracking-tight text-white font-sans flex items-center gap-1.5">
                EduMeet
                <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-brand-500/20 text-brand-300 border border-brand-500/30">
                  Global
                </span>
              </span>
              <p className="text-[10px] text-slate-400 -mt-1 hidden sm:block">
                Reciprocal Peer Teaching Network
              </p>
            </div>
          </Link>

          {/* Right Navigation / Auth Area */}
          <div className="flex items-center gap-3">
            {isAuthenticated && user ? (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 p-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-700/70 transition-all cursor-pointer"
                >
                  <div className="w-7 h-7 rounded-lg bg-brand-600/30 border border-brand-500/40 flex items-center justify-center text-brand-300 font-bold text-xs uppercase">
                    {user.full_name ? user.full_name.charAt(0) : user.email.charAt(0)}
                  </div>
                  <span className="text-xs font-medium text-slate-200 hidden md:block max-w-[120px] truncate">
                    {user.full_name || user.email.split('@')[0]}
                  </span>
                  {user.is_verified_student && (
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 hidden sm:block" />
                  )}
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                </button>

                {userMenuOpen && (
                  <div
                    onClick={() => setUserMenuOpen(false)}
                    className="absolute right-0 mt-2 w-48 rounded-xl glass-panel border border-white/10 shadow-2xl py-1 text-xs text-slate-200 z-50 animate-in fade-in zoom-in-95 duration-150"
                  >
                    <div className="px-3 py-2 border-b border-white/10">
                      <p className="font-semibold text-white truncate">{user.full_name || 'Student'}</p>
                      <p className="text-[11px] text-slate-400 truncate">{user.email}</p>
                    </div>
                    <Link
                      to="/profile"
                      className="flex items-center gap-2 px-3 py-2 hover:bg-white/5 transition-colors"
                    >
                      <UserIcon className="w-4 h-4 text-slate-400" /> Profile & Settings
                    </Link>
                    <button
                      onClick={logout}
                      className="w-full text-left flex items-center gap-2 px-3 py-2 text-red-300 hover:bg-red-500/10 transition-colors cursor-pointer"
                    >
                      <LogOut className="w-4 h-4" /> Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => setAuthModalOpen(true)}
                className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-xs sm:text-sm transition-all shadow-md shadow-brand-500/25 flex items-center gap-2 cursor-pointer"
              >
                <Sparkles className="w-4 h-4" /> Get Started / Sign In
              </button>
            )}
          </div>
        </div>
      </header>

      <AuthModal isOpen={authModalOpen} onClose={() => setAuthModalOpen(false)} />
    </>
  );
};
