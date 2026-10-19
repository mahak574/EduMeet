import React, { useState } from 'react';
import {
  Sparkles,
  ShieldCheck,
  Clock,
  RotateCcw,
  PlayCircle,
  GraduationCap,
  ArrowRight,
  Code2,
  Terminal,
  BookOpen,
  ChevronDown,
} from 'lucide-react';
import { SkillMatrix } from '../dashboard/SkillMatrix';
import { DiagnosticQuizModal, MATH_GRADE_TRACKS } from './DiagnosticQuizModal';
import { useAuthStore } from '../../stores/authStore';
import { AuthModal } from '../auth/AuthModal';

export const PYTHON_MODULE_TRACKS = [
  {
    slug: 'python',
    topic: 'data-structures-and-types',
    title: 'Data Structures & Memory Gotchas',
    subtitle: 'Mutable default arguments, dict & list comprehensions, slicing references, and type immutability',
    icon: '🐍',
    tag: 'Python 3.x',
  },
  {
    slug: 'python',
    topic: 'functions-and-generators',
    title: 'Generators, Closures & Scope',
    subtitle: 'Iterators with yield from, closure LEGB scope binding, custom decorators, and lambda functions',
    icon: '⚡',
    tag: 'Core Python',
  },
  {
    slug: 'python',
    topic: 'oop-and-dunder-methods',
    title: 'OOP, Dunder Methods & Dataclasses',
    subtitle: 'Object model magic (__call__, __repr__), C3 MRO hierarchy, and dataclass frozen invariants',
    icon: '🧩',
    tag: 'Advanced OOP',
  },
  {
    slug: 'python',
    topic: 'concurrency-and-asyncio',
    title: 'Concurrency, AsyncIO & Event Loop',
    subtitle: 'Non-blocking I/O with asyncio.gather, coroutine task exception handling, and GIL thread safety',
    icon: '🚀',
    tag: 'Concurrency',
  },
];

export const DiagnosticHubPage: React.FC = () => {
  const { user } = useAuthStore();
  const [selectedSubject, setSelectedSubject] = useState<string>(
    user?.subjects_studied?.[0] || 'python'
  );
  const [quizModalOpen, setQuizModalOpen] = useState<boolean>(false);
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);
  const [showAllTracks, setShowAllTracks] = useState<boolean>(false);

  // Strictly dynamic subjects from user profile, fallback to 'python' if none chosen yet
  const userSubjects = user?.subjects_studied?.length ? user.subjects_studied : ['python'];
  const userHasMath = userSubjects.some((s) => s.toLowerCase().startsWith('math'));
  const userHasPython = userSubjects.some((s) => s.toLowerCase().includes('python') || s.toLowerCase().includes('coding'));

  const handleStartQuiz = (subject: string) => {
    setSelectedSubject(subject);
    setQuizModalOpen(true);
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
          Calibrate your personal mastery before entering peer matching. Diagnostic quizzes run 15–20 server-timed practical calculation questions with Bayesian IRT estimation. Scoring &ge;70% certifies you to teach; scores &lt;70% identify targeted learning goals.
        </p>

        {/* Quick Diagnostic Launchers for User's Active Subjects */}
        <div className="pt-2 flex flex-wrap gap-2.5">
          {userSubjects.map((subj) => (
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

      {/* Practical Python Section - Rendered if user studies Python/Coding */}
      {userHasPython && (
        <div className="glass-panel p-6 rounded-3xl border border-blue-500/30 bg-gradient-to-br from-blue-950/20 via-slate-900/60 to-slate-950/80 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <div className="inline-flex items-center gap-1.5 text-xs text-blue-300 font-semibold mb-1">
                <Terminal className="w-3.5 h-3.5" /> Practical Code Execution Modules
              </div>
              <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                Practical Python & Algorithmic Programming
              </h2>
              <p className="text-xs text-slate-300 leading-relaxed max-w-xl">
                Diagnostic questions contain authentic code snippets testing output prediction, mutable references, generators, closures, and async concurrency.
              </p>
            </div>
            <button
              onClick={() => handleStartQuiz('python')}
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs tracking-wide transition-all shadow-md shadow-blue-500/20 flex items-center gap-2 cursor-pointer self-start sm:self-auto"
            >
              <Code2 className="w-4 h-4" /> Start Python Diagnostic
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {PYTHON_MODULE_TRACKS.map((mod) => (
              <div
                key={mod.title}
                onClick={() => handleStartQuiz(mod.slug)}
                className="p-4 rounded-2xl bg-slate-900/70 hover:bg-blue-500/10 border border-white/10 hover:border-blue-500/40 text-left transition-all group flex flex-col justify-between space-y-2 cursor-pointer shadow-sm hover:shadow-blue-500/10"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xl">{mod.icon}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-blue-300 border border-white/10 font-semibold">
                      {mod.tag}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-white group-hover:text-blue-300 transition-colors">
                    {mod.title}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                    {mod.subtitle}
                  </p>
                </div>

                <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-blue-400 font-medium">
                  <span>Practical Code Assessment</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mathematics Grade & Professional Career Tracks - Rendered ONLY if user studies Maths OR explicitly expands it */}
      {(userHasMath || showAllTracks) ? (
        <div className="glass-panel p-6 rounded-3xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/20 via-slate-900/60 to-slate-950/80 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <div className="inline-flex items-center gap-1.5 text-xs text-emerald-300 font-semibold mb-1">
                <GraduationCap className="w-3.5 h-3.5" /> Multi-Grade Curriculum
              </div>
              <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                Practical Mathematics by Grade & Specialization
              </h2>
              <p className="text-xs text-slate-300 leading-relaxed max-w-xl">
                Mathematics questions are tailored to your academic level—from 1st class arithmetic and 12th class calculus to engineering differential equations and CA business finance.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
            {MATH_GRADE_TRACKS.map((track) => (
              <button
                key={track.slug}
                onClick={() => handleStartQuiz(track.slug)}
                className="p-4 rounded-2xl bg-slate-900/70 hover:bg-emerald-500/15 border border-white/10 hover:border-emerald-500/40 text-left transition-all group flex flex-col justify-between space-y-2 cursor-pointer shadow-sm hover:shadow-emerald-500/10"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xl">{track.icon}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-emerald-300 border border-white/10 font-semibold">
                      {track.grade}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">
                    {track.title}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed line-clamp-2">
                    {track.subtitle}
                  </p>
                </div>

                <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-emerald-400 font-medium">
                  <span>Start assessment</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-white/10 text-slate-300">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-semibold text-white">Looking for Mathematics or other grade tracks?</p>
              <p className="text-[11px] text-slate-400">Explore multi-grade elementary, senior secondary, and engineering tracks.</p>
            </div>
          </div>
          <button
            onClick={() => setShowAllTracks(true)}
            className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-xs text-slate-200 hover:text-white font-medium transition-all cursor-pointer flex items-center gap-1.5"
          >
            Show Mathematics Tracks <ChevronDown className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

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
