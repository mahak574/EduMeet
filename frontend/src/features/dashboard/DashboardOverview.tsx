import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { AuthModal } from '../auth/AuthModal';
import { PublicOverview } from '../overview/PublicOverview';
import { WeeklyStreakHeatmap } from './WeeklyStreakHeatmap';
import {
  BrainCircuit,
  Users2,
  Video,
  FileSpreadsheet,
  Scale,
  Sparkles,
  ArrowRight,
  User as UserIcon,
} from 'lucide-react';

export const DashboardOverview: React.FC = () => {
  const { user, isAuthenticated } = useAuthStore();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('signup');

  // 1. Logged-out visitors see ONLY the comprehensive Public Overview
  if (!isAuthenticated) {
    return (
      <>
        <PublicOverview
          onOpenAuth={(mode) => {
            setAuthMode(mode);
            setAuthModalOpen(true);
          }}
        />
        <AuthModal
          isOpen={authModalOpen}
          mode={authMode}
          onClose={() => setAuthModalOpen(false)}
        />
      </>
    );
  }

  // 2. Authenticated users see a concise summary & navigation hub (without duplicating full tab widgets)
  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Personalized Welcome Banner */}
      <div className="relative overflow-hidden p-6 sm:p-8 rounded-3xl glass-panel border border-brand-500/20 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="max-w-2xl relative z-10 space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" /> Welcome back, {user?.full_name || 'Student'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-sans">
            Your Reciprocal Learning Hub
          </h1>
          <p className="text-slate-300 text-xs sm:text-sm leading-relaxed">
            Every session is split equally: 25 minutes teaching what you know, 25 minutes learning what you lack, and 10 minutes peer quiz exchange.
          </p>

          {user?.subjects_studied && user.subjects_studied.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pt-2">
              <span className="text-xs text-slate-400">Active Subjects:</span>
              {user.subjects_studied.map((sub) => (
                <span
                  key={sub}
                  className="px-2.5 py-0.5 rounded-lg bg-slate-900 border border-slate-700 text-brand-300 text-xs font-medium uppercase tracking-wide"
                >
                  {sub}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Navigation Hub: Compact Quick-Actions to Dedicated Tabs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Diagnostic Quiz Card */}
        <div className="glass-panel p-5 rounded-2xl border border-white/10 flex flex-col justify-between space-y-4 hover:border-brand-500/40 transition-colors">
          <div className="space-y-2">
            <div className="w-9 h-9 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-white text-sm">Diagnostic Quiz</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Verify your actual topic skill level with adaptive diagnostic assessments.
            </p>
          </div>
          <Link
            to="/diagnostic"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-400 hover:text-brand-300 pt-2"
          >
            Open Diagnostic Quiz <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Peer Match Card */}
        <div className="glass-panel p-5 rounded-2xl border border-white/10 flex flex-col justify-between space-y-4 hover:border-brand-500/40 transition-colors">
          <div className="space-y-2">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center">
              <Users2 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-white text-sm">Match</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Discover complementary peers ready for live or scheduled reciprocal learning.
            </p>
          </div>
          <Link
            to="/matching"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300 pt-2"
          >
            Find a Learning Peer <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Sessions Card */}
        <div className="glass-panel p-5 rounded-2xl border border-white/10 flex flex-col justify-between space-y-4 hover:border-brand-500/40 transition-colors">
          <div className="space-y-2">
            <div className="w-9 h-9 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center">
              <Video className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-white text-sm">Sessions</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Join upcoming video/whiteboard rooms or view completed session transcripts.
            </p>
          </div>
          <Link
            to="/sessions"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-400 hover:text-blue-300 pt-2"
          >
            Go to Sessions <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Review Card */}
        <div className="glass-panel p-5 rounded-2xl border border-white/10 flex flex-col justify-between space-y-4 hover:border-brand-500/40 transition-colors">
          <div className="space-y-2">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-white text-sm">Review</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Review missed peer quiz items and reinforce learning through spaced repetition.
            </p>
          </div>
          <Link
            to="/mistakes"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-400 hover:text-emerald-300 pt-2"
          >
            Open Review Deck <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Weekly Streak Consistency Tracker */}
      <WeeklyStreakHeatmap />

      {/* Fairness Balance & Platform Principle Card */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Fairness Balance</span>
            <div className="p-2 rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20">
              <Scale className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">50% Taught : 50% Learned</div>
            <p className="text-xs text-slate-400 mt-1">
              Balanced reciprocal contribution. You give exactly as much knowledge as you receive.
            </p>
          </div>
          <div className="pt-2">
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden flex">
              <div className="bg-brand-500 h-2 w-1/2" title="Taught: 50%" />
              <div className="bg-indigo-400 h-2 w-1/2" title="Learned: 50%" />
            </div>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Learning Profile</span>
            <div className="p-2 rounded-xl bg-slate-800 text-slate-300 border border-slate-700">
              <UserIcon className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-xl font-bold text-white truncate">{user?.full_name || 'Active Student'}</div>
            <p className="text-xs text-slate-400 mt-1">
              Timezone: {user?.timezone || 'UTC'} • Teaching Style: {user?.preferences?.preferred_teaching_style || 'Example Heavy'}
            </p>
          </div>
          <div className="pt-2">
            <Link
              to="/profile"
              className="inline-flex items-center gap-1.5 text-xs text-brand-300 hover:text-brand-200 font-medium"
            >
              Update Preferences & Subjects →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
