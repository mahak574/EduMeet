import React, { useState, useEffect } from 'react';
import {
  Brain,
  Calendar,
  CheckCircle,
  Sparkles,
  Loader2,
  Check,
} from 'lucide-react';
import { reviewApi, MistakeItem, ReviewScheduleItem } from '../../services/reviewApi';
import { format } from 'date-fns';
import { useAuthStore } from '../../stores/authStore';
import { AuthModal } from '../auth/AuthModal';
import { LogIn } from 'lucide-react';

export const MistakeJournalView: React.FC = () => {
  const { user, isAuthenticated } = useAuthStore();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [mistakes, setMistakes] = useState<MistakeItem[]>([]);
  const [dueSchedules, setDueSchedules] = useState<ReviewScheduleItem[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchData = async () => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    try {
      const [mList, dueList] = await Promise.all([
        reviewApi.getMistakes(),
        reviewApi.getDueReviewSchedules(),
      ]);
      setMistakes(mList);
      setDueSchedules(dueList);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleResolve = async (id: string) => {
    try {
      await reviewApi.resolveMistake(id);
      setMistakes((prev) =>
        prev.map((m) => (m.id === id ? { ...m, resolved: true } : m))
      );
      setActionMessage('Mistake marked as resolved!');
      setTimeout(() => setActionMessage(null), 3000);
    } catch {
      // ignore
    }
  };

  const handleEvaluateSchedule = async (scheduleId: string, quality: number) => {
    try {
      await reviewApi.evaluateReview(scheduleId, quality);
      setDueSchedules((prev) => prev.filter((s) => s.id !== scheduleId));
      setActionMessage(`Review logged (Quality ${quality}/5). Next review date recalculated using SuperMemo-2.`);
      setTimeout(() => setActionMessage(null), 4000);
    } catch {
      // ignore
    }
  };

  const filteredMistakes = mistakes.filter((m) => {
    if (selectedSubject !== 'all' && m.subject_slug !== selectedSubject) return false;
    return true;
  });

  const getTagBadge = (tag: string) => {
    switch (tag) {
      case 'didnt_know_concept':
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">Concept Gap</span>;
      case 'silly_mistake':
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">Silly Slip</span>;
      case 'ran_out_of_time':
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">Time Out</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">Wording</span>;
    }
  };

  if (isLoading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-brand-400" />
        <p className="text-xs">Loading Spaced Repetition Journal...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-300 text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" /> Spaced Repetition (SuperMemo-2)
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Mistake Journal & Memory Queue
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Every incorrect answer from diagnostics, peer quizzes, and pre/post checks is scheduled for review using mathematical spacing intervals.
          </p>
        </div>

        {!isAuthenticated && (
          <button
            onClick={() => setAuthModalOpen(true)}
            className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer shadow-md shadow-brand-500/20 shrink-0"
          >
            <LogIn className="w-4 h-4" /> Log In to Sync Journal
          </button>
        )}
      </div>

      {actionMessage && (
        <div className="p-3 rounded-xl bg-brand-500/20 border border-brand-500/40 text-brand-300 text-xs text-center font-medium animate-in fade-in">
          {actionMessage}
        </div>
      )}

      {/* 1. DUE TODAY SPACED REPETITION FLASHCARDS */}
      {dueSchedules.length > 0 && (
        <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-amber-500/30 bg-gradient-to-br from-amber-950/20 via-slate-900/60 to-slate-950/60 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/30">
                <Brain className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  Spaced Reviews Due Today ({dueSchedules.length})
                </h3>
                <p className="text-xs text-slate-400">
                  Rate your recall difficulty to compute the next interval (I = I_prev × EF).
                </p>
              </div>
            </div>

            <span className="text-xs font-mono font-bold text-amber-300 bg-amber-500/10 px-3 py-1 rounded-xl border border-amber-500/20">
              SM-2 Active
            </span>
          </div>

          {/* Active Review Card */}
          {dueSchedules[0] && (
            <div className="p-5 rounded-2xl bg-slate-900/90 border border-white/10 space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Subtopic: <strong className="text-white capitalize">{dueSchedules[0].subtopic_slug.replace(/-/g, ' ')}</strong></span>
                <span>Repetition: <strong className="text-brand-300 font-mono">#{dueSchedules[0].repetition_number}</strong></span>
              </div>

              <div className="space-y-1">
                <span className="text-[11px] uppercase font-bold text-slate-500">Subject</span>
                <p className="text-sm font-bold text-white uppercase">{dueSchedules[0].subject_slug}</p>
              </div>

              {/* SM-2 Recall Feedback Buttons */}
              <div className="space-y-2 pt-2 border-t border-white/10">
                <span className="text-[11px] font-semibold text-slate-400">How easily did you recall this concept?</span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <button
                    onClick={() => handleEvaluateSchedule(dueSchedules[0].id, 1)}
                    className="p-2.5 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 hover:bg-rose-900/40 text-xs font-semibold transition-all cursor-pointer"
                  >
                    1 - Blackout (Reset)
                  </button>
                  <button
                    onClick={() => handleEvaluateSchedule(dueSchedules[0].id, 3)}
                    className="p-2.5 rounded-xl bg-amber-950/40 border border-amber-500/30 text-amber-300 hover:bg-amber-900/40 text-xs font-semibold transition-all cursor-pointer"
                  >
                    3 - Hard (Recalled)
                  </button>
                  <button
                    onClick={() => handleEvaluateSchedule(dueSchedules[0].id, 4)}
                    className="p-2.5 rounded-xl bg-blue-950/40 border border-blue-500/30 text-blue-300 hover:bg-blue-900/40 text-xs font-semibold transition-all cursor-pointer"
                  >
                    4 - Good (Smooth)
                  </button>
                  <button
                    onClick={() => handleEvaluateSchedule(dueSchedules[0].id, 5)}
                    className="p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-900/40 text-xs font-semibold transition-all cursor-pointer"
                  >
                    5 - Perfect (Instant)
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 2. MISTAKE JOURNAL LIST */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-white tracking-tight">Mistake History</h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
              {filteredMistakes.length} logged
            </span>
          </div>

          {/* Subject Filter Tabs */}
          <div className="flex gap-2 flex-wrap">
            {Array.from(
              new Set(['all', ...mistakes.map((m) => m.subject_slug), ...(user?.subjects_studied || [])])
            ).filter(Boolean).map((subj) => (
              <button
                key={subj}
                onClick={() => setSelectedSubject(subj)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer uppercase tracking-wider ${
                  selectedSubject === subj
                    ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30 shadow-md'
                    : 'text-slate-400 hover:text-white bg-slate-900/30'
                }`}
              >
                {subj.replace(/-/g, ' ')}
              </button>
            ))}
          </div>
        </div>

        {filteredMistakes.length === 0 ? (
          <div className="py-12 text-center text-slate-500 space-y-2">
            <CheckCircle className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="text-sm font-medium text-slate-400">No mistakes logged for this category!</p>
            <p className="text-xs">Take diagnostics or complete peer sessions to populate your learning journal.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredMistakes.map((m) => (
              <div
                key={m.id}
                className={`p-4 rounded-2xl border transition-all space-y-3 ${
                  m.resolved
                    ? 'bg-slate-900/40 border-white/5 opacity-75'
                    : 'bg-slate-900/80 border-white/10 hover:border-white/20'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-bold text-white uppercase">{m.subject_slug}</span>
                    <span className="text-slate-500">•</span>
                    <span className="text-xs text-brand-300 font-medium capitalize">
                      {m.topic_slug.replace(/-/g, ' ')}
                    </span>
                    {getTagBadge(m.user_mistake_tag)}
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
                      <Calendar className="w-3 h-3" /> {format(new Date(m.created_at), 'MMM d, yyyy')}
                    </span>
                    {!m.resolved ? (
                      <button
                        onClick={() => handleResolve(m.id)}
                        className="px-2.5 py-1 rounded-lg border border-white/10 hover:bg-emerald-500/10 text-emerald-400 text-[11px] font-semibold flex items-center gap-1 transition-all cursor-pointer"
                      >
                        <Check className="w-3 h-3" /> Mark Resolved
                      </button>
                    ) : (
                      <span className="text-[11px] font-bold text-emerald-400 flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" /> Resolved
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed font-sans">{m.question_prompt}</p>

                {m.learner_notes && (
                  <div className="p-2.5 rounded-xl bg-slate-950/60 border border-white/5 text-[11px] text-slate-400">
                    <strong className="text-slate-300">Notes:</strong> {m.learner_notes}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => {
          setAuthModalOpen(false);
          fetchData();
        }}
      />
    </div>
  );
};
