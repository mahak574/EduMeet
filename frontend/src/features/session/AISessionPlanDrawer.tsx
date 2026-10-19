import React, { useEffect, useState } from 'react';
import { BookOpen, Check, Copy, Loader2, Sparkles, X } from 'lucide-react';
import { apiClient } from '../../api/client';
import { APIResponse } from '../../types';

interface LessonPhaseGuide {
  phase_name: string;
  duration_minutes: number;
  objectives: string[];
  discussion_prompts: string[];
  checklist: string[];
}

interface TopicPlan {
  topic_name: string;
  subject_slug: string;
  subtopic_slug: string;
  teacher_name: string;
  learner_name: string;
  phases: LessonPhaseGuide[];
  starter_code_or_query?: string;
}

interface SessionPlanResponse {
  session_id: string;
  is_llm_generated: boolean;
  ai_consent_mutual: boolean;
  plan_teacher_a: TopicPlan;
  plan_teacher_b: TopicPlan;
  general_guidelines: string[];
  notice?: string;
}

interface AISessionPlanDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  onInsertCode?: (code: string) => void;
}

export const AISessionPlanDrawer: React.FC<AISessionPlanDrawerProps> = ({
  isOpen,
  onClose,
  sessionId,
  onInsertCode,
}) => {
  const [plan, setPlan] = useState<SessionPlanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedPlanTab, setSelectedPlanTab] = useState<'teacher_a' | 'teacher_b'>('teacher_a');
  const [copiedCode, setCopiedCode] = useState(false);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (isOpen && !plan) {
      loadPlan();
    }
  }, [isOpen, sessionId]);

  const loadPlan = async () => {
    setLoading(true);
    try {
      const res = await apiClient<APIResponse<SessionPlanResponse>>(`/ai/session-plan/${sessionId}`);
      if (res?.success && res.data) {
        setPlan(res.data);
      }
    } catch (err) {
      console.error('Failed to load session plan:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const currentTopicPlan = plan ? (selectedPlanTab === 'teacher_a' ? plan.plan_teacher_a : plan.plan_teacher_b) : null;

  const handleCopyCode = () => {
    if (!currentTopicPlan?.starter_code_or_query) return;
    navigator.clipboard.writeText(currentTopicPlan.starter_code_or_query);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
    if (onInsertCode) {
      onInsertCode(currentTopicPlan.starter_code_or_query);
    }
  };

  const toggleCheck = (id: string) => {
    setCheckedItems((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-xl bg-slate-900/95 border-l border-white/10 backdrop-blur-xl z-50 flex flex-col shadow-2xl animate-slide-left">
      {/* Header */}
      <div className="p-5 border-b border-white/10 flex items-center justify-between shrink-0 bg-slate-900/80">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-brand-500/20 text-brand-300 border border-brand-500/30">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm">Pedagogical Lesson Blueprint</h3>
            <p className="text-[11px] text-slate-400">
              {plan?.is_llm_generated ? 'AI Dynamic Blueprint' : 'Deterministic Curriculum Blueprint'}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5 custom-scrollbar">
        {loading ? (
          <div className="h-64 flex flex-col items-center justify-center space-y-3 text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
            <span className="text-xs">Generating pedagogical blueprint...</span>
          </div>
        ) : plan ? (
          <>
            {/* Notice / Mode Banner */}
            <div className="p-3.5 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-xs text-brand-300 leading-relaxed flex items-start gap-2">
              <BookOpen className="w-4 h-4 shrink-0 mt-0.5 text-brand-400" />
              <span>{plan.notice || 'Use this structured guide during your 20-minute teaching phase.'}</span>
            </div>

            {/* Teacher Selection Tabs */}
            <div className="grid grid-cols-2 p-1 rounded-2xl bg-slate-800/80 border border-white/5">
              <button
                onClick={() => setSelectedPlanTab('teacher_a')}
                className={`py-2 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  selectedPlanTab === 'teacher_a'
                    ? 'bg-brand-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Part 1: {plan.plan_teacher_a.teacher_name}
              </button>
              <button
                onClick={() => setSelectedPlanTab('teacher_b')}
                className={`py-2 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  selectedPlanTab === 'teacher_b'
                    ? 'bg-brand-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Part 2: {plan.plan_teacher_b.teacher_name}
              </button>
            </div>

            {currentTopicPlan && (
              <div className="space-y-4">
                <div className="p-4 rounded-2xl bg-slate-800/50 border border-white/5">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-brand-400 block mb-1">
                    Teaching Subject & Topic
                  </span>
                  <h4 className="text-base font-bold text-white">{currentTopicPlan.topic_name}</h4>
                  <p className="text-xs text-slate-400 mt-1">
                    Teacher: <span className="text-slate-200 font-semibold">{currentTopicPlan.teacher_name}</span> • Learner: <span className="text-slate-200 font-semibold">{currentTopicPlan.learner_name}</span>
                  </p>
                </div>

                {/* Starter Code Snippet */}
                {currentTopicPlan.starter_code_or_query && (
                  <div className="p-4 rounded-2xl bg-slate-950/70 border border-white/10 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-300">Starter Code / Query</span>
                      <button
                        onClick={handleCopyCode}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
                      >
                        {copiedCode ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        {copiedCode ? 'Copied to Editor' : 'Copy Code'}
                      </button>
                    </div>
                    <pre className="p-3 rounded-xl bg-slate-900 text-xs font-mono text-brand-300 overflow-x-auto max-h-40 custom-scrollbar border border-white/5">
                      {currentTopicPlan.starter_code_or_query}
                    </pre>
                  </div>
                )}

                {/* Lesson Phases */}
                <div className="space-y-3">
                  <h5 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Teaching Sequence (25 Minutes Total)
                  </h5>
                  {currentTopicPlan.phases.map((ph, idx) => (
                    <div key={idx} className="p-4 rounded-2xl bg-slate-800/40 border border-white/5 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-brand-500/20 text-brand-400 border border-brand-500/30 flex items-center justify-center text-[11px]">
                            {idx + 1}
                          </span>
                          {ph.phase_name}
                        </span>
                        <span className="text-[11px] text-slate-400 font-medium">{ph.duration_minutes} min</span>
                      </div>

                      {/* Objectives */}
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Key Objectives</span>
                        <ul className="space-y-1">
                          {ph.objectives.map((obj, i) => (
                            <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                              <span className="w-1 h-1 rounded-full bg-brand-400 mt-2 shrink-0" />
                              <span>{obj}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Prompts */}
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Discussion Prompts</span>
                        <ul className="space-y-1">
                          {ph.discussion_prompts.map((prm, i) => (
                            <li key={i} className="text-xs text-amber-300/90 italic flex items-start gap-2">
                              <span>"</span>
                              <span>{prm}"</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Interactive Checklist */}
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Checklist</span>
                        <div className="space-y-1.5">
                          {ph.checklist.map((item, i) => {
                            const itemId = `${idx}-${i}`;
                            const isChecked = !!checkedItems[itemId];
                            return (
                              <button
                                key={i}
                                onClick={() => toggleCheck(itemId)}
                                className={`w-full text-left p-2 rounded-xl text-xs flex items-center gap-2.5 transition-colors cursor-pointer ${
                                  isChecked ? 'bg-emerald-500/10 text-emerald-300' : 'bg-slate-900/40 text-slate-300 hover:bg-slate-900/80'
                                }`}
                              >
                                <span className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 ${
                                  isChecked ? 'bg-emerald-500 border-emerald-400 text-slate-950' : 'border-white/20'
                                }`}>
                                  {isChecked && <Check className="w-3 h-3 stroke-[3]" />}
                                </span>
                                <span className={isChecked ? 'line-through text-slate-400' : ''}>{item}</span>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
};
