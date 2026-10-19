import React, { useState } from 'react';
import {
  Sparkles,
  ShieldCheck,
  Clock,
  RotateCcw,
  PlayCircle,
} from 'lucide-react';
import { SkillMatrix } from '../dashboard/SkillMatrix';
import { DiagnosticQuizModal } from './DiagnosticQuizModal';
import { useAuthStore } from '../../stores/authStore';
import { AuthModal } from '../auth/AuthModal';

export const DiagnosticHubPage: React.FC = () => {
  const { user, isAuthenticated } = useAuthStore();
  const [selectedSubject, setSelectedSubject] = useState<string>('python');
  const [quizModalOpen, setQuizModalOpen] = useState<boolean>(false);
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);

  const subjects = Array.from(
    new Set([...(user?.subjects_studied || []), 'python', 'dsa', 'dbms'])
  ).filter(Boolean);

  const handleStartQuiz = (subject: string) => {
    setSelectedSubject(subject);
    if (!isAuthenticated) {
      setAuthModalOpen(true);
    } else {
      setQuizModalOpen(true);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in max-w-5xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-brand-500/20 bg-gradient-to-br from-brand-950/20 via-slate-900/60 to-slate-950/60 space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-300 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" /> Diagnostic Assessment Engine
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Adaptive Skill Diagnostics & Calibration
        </h1>
        <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
          Calibrate your personal mastery before entering peer matching. Diagnostic quizzes run 15–20 server-timed questions with Bayesian IRT estimation. Scoring ≥70% certifies you to teach that topic; scores &lt;70% identify targeted learning goals.
        </p>

        {/* Quick Diagnostic Launchers */}
        <div className="pt-2 flex flex-wrap gap-3">
          {subjects.map((subj) => (
            <button
              key={subj}
              onClick={() => handleStartQuiz(subj)}
              className="px-4 py-2 rounded-xl bg-slate-900/80 hover:bg-brand-600/20 border border-white/10 hover:border-brand-500/40 text-slate-200 hover:text-white text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer"
            >
              <PlayCircle className="w-3.5 h-3.5 text-brand-400" />
              Assess <span className="uppercase">{subj.replace(/-/g, ' ')}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Interactive Skill Matrix */}
      <div id="skill-matrix">
        <SkillMatrix />
      </div>

      {/* Integrity & Protocol Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
          <div className="p-2 rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20 w-fit">
            <Clock className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-white text-sm">60-Second Server Timer</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Every question has a strict 60-second client/server countdown with automated progression to ensure real-time recall speed.
          </p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 w-fit">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-white text-sm">Anti-Cheat Tab Deterrence</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Window blur and tab-switching are actively monitored. Exceeding 2 violations triggers automated quiz submission.
          </p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
          <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 w-fit">
            <RotateCcw className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-white text-sm">7-Day Interval Protection</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            A 7-day cooldown applies between attempts with a maximum 3-attempt quota per subject to prevent question memorization.
          </p>
        </div>
      </div>

      {/* Active Modal */}
      <DiagnosticQuizModal
        isOpen={quizModalOpen}
        onClose={() => setQuizModalOpen(false)}
        subjectSlug={selectedSubject}
      />

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
      />
    </div>
  );
};
