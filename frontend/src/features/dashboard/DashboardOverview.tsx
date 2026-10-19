import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { AuthModal } from '../auth/AuthModal';
import {
  BrainCircuit,
  Flame,
  Scale,
  Sparkles,
  ArrowRight,
  CheckCircle,
  Lightbulb,
} from 'lucide-react';

export const DashboardOverview: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  const [authModalOpen, setAuthModalOpen] = useState(false);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Hero Welcome */}
      <div className="relative overflow-hidden p-6 sm:p-10 rounded-3xl glass-panel border border-brand-500/20 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="max-w-2xl relative z-10 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" /> Reciprocal Peer Teaching
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight font-sans leading-tight">
            Learn What You Lack.
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-indigo-300">
              Master What You Teach.
            </span>
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            EduMeet pairs you with a student who has complementary strengths. If you are strong in DSA and weak in DBMS, you teach them DSA for 30 minutes, they teach you DBMS for 30 minutes, then you exchange peer quizzes.
          </p>

          <div className="flex flex-wrap gap-4 pt-2">
            {!isAuthenticated ? (
              <button
                onClick={() => setAuthModalOpen(true)}
                className="px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-sm transition-all shadow-lg shadow-brand-500/25 flex items-center gap-2 cursor-pointer"
              >
                Join EduMeet Network <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <Link
                to="/profile"
                className="px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-sm transition-all shadow-lg shadow-brand-500/25 flex items-center gap-2"
              >
                Customize Learning Profile <ArrowRight className="w-4 h-4" />
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Motivation & Private Progress Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Weekly Streak Card */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Weekly Consistency</span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">1 Week Streak</div>
            <p className="text-xs text-slate-400 mt-1">
              At least 1 completed reciprocal session per week. No high-anxiety daily streaks.
            </p>
          </div>
          <div className="pt-2 flex items-center gap-2 text-xs text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5" /> 1 Streak Freeze Available
          </div>
        </div>

        {/* Private Fairness Meter Card */}
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

        {/* Diagnostic Assessment Status */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Diagnostic Readiness</span>
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <BrainCircuit className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">Diagnostic Bank</div>
            <p className="text-xs text-slate-400 mt-1">
              Take a low-stakes 10-question evaluation to unlock topic-level peer matching.
            </p>
          </div>
          <div className="pt-2">
            <span className="inline-flex items-center gap-1.5 text-xs text-purple-300 font-medium">
              Coming in Phase 2
            </span>
          </div>
        </div>
      </div>

      {/* How It Works 3-Step Walkthrough */}
      <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-6">
        <h2 className="text-xl font-bold text-white font-sans flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-amber-400" />
          The EduMeet Reciprocal Model
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="w-7 h-7 rounded-lg bg-brand-600/20 border border-brand-500/30 text-brand-300 flex items-center justify-center font-bold text-xs">
              1
            </div>
            <h3 className="font-semibold text-white text-sm">Complementary Pairing</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              If student A is strong in Graphs and weak in Indexing, and student B is strong in Indexing and weak in Graphs, the graph matching engine pairs them up.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 flex items-center justify-center font-bold text-xs">
              2
            </div>
            <h3 className="font-semibold text-white text-sm">Synchronized 1-Hour Session</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              25 minutes: Teacher A teaches Topic A.<br />
              25 minutes: Teacher B teaches Topic B.<br />
              10 minutes: Exchange peer-made test questions.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="w-7 h-7 rounded-lg bg-emerald-600/20 border border-emerald-500/30 text-emerald-300 flex items-center justify-center font-bold text-xs">
              3
            </div>
            <h3 className="font-semibold text-white text-sm">Growth Without Ranking</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              No leaderboards or public competition. Your skill progression and mistake journal are private, shared only with your session partner.
            </p>
          </div>
        </div>
      </div>

      <AuthModal isOpen={authModalOpen} onClose={() => setAuthModalOpen(false)} />
    </div>
  );
};
