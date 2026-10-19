import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Timer,
  AlertTriangle,
  CheckCircle2,
  X,
  Sparkles,
  ArrowRight,
  BrainCircuit,
  ShieldAlert,
} from 'lucide-react';
import { quizApi, CurrentQuestion, QuizResult } from '../../services/quizApi';

interface DiagnosticQuizModalProps {
  isOpen: boolean;
  onClose: () => void;
  subjectSlug: 'dsa' | 'dbms';
  onComplete?: () => void;
}

export const DiagnosticQuizModal: React.FC<DiagnosticQuizModalProps> = ({
  isOpen,
  onClose,
  subjectSlug,
  onComplete,
}) => {
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<CurrentQuestion | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState<number>(60);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [tabWarning, setTabWarning] = useState<string | null>(null);
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);

  const startTimeRef = useRef<number>(Date.now());
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize or start diagnostic attempt
  const initQuiz = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    setQuizResult(null);
    try {
      const data = await quizApi.startQuiz(subjectSlug);
      setAttemptId(data.attempt_id);
      loadNextQuestion(data.attempt_id);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.message || err.response?.data?.detail || 'Failed to start diagnostic.');
      setIsLoading(false);
    }
  }, [subjectSlug]);

  // Load current question
  const loadNextQuestion = async (aId: string) => {
    try {
      const q = await quizApi.getCurrentQuestion(aId);
      setCurrentQuestion(q);
      setSelectedOption(null);
      setTimeLeft(60);
      startTimeRef.current = Date.now();
      setIsLoading(false);
    } catch (err: any) {
      if (err.response?.status === 400 || err.response?.data?.detail?.includes('completed')) {
        // Fetch results
        fetchResult(aId);
      } else {
        setErrorMsg(err.response?.data?.detail || 'Failed to load question.');
        setIsLoading(false);
      }
    }
  };

  const fetchResult = async (aId: string) => {
    setIsLoading(true);
    try {
      const res = await quizApi.getQuizResult(aId);
      setQuizResult(res);
      onComplete?.();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load results.');
    } finally {
      setIsLoading(false);
    }
  };

  // Submit answer
  const handleSubmit = useCallback(
    async (optionId: string | null = selectedOption) => {
      if (!attemptId || isLoading) return;
      setIsLoading(true);
      const elapsed = Math.min(65, (Date.now() - startTimeRef.current) / 1000);

      try {
        const resp = await quizApi.submitAnswer(attemptId, optionId, elapsed);
        if (resp.is_completed) {
          fetchResult(attemptId);
        } else {
          loadNextQuestion(attemptId);
        }
      } catch (err: any) {
        setErrorMsg(err.response?.data?.detail || 'Submission failed.');
        setIsLoading(false);
      }
    },
    [attemptId, selectedOption, isLoading]
  );

  // Anti-cheat tab visibility change listener
  useEffect(() => {
    if (!isOpen || !attemptId || quizResult) return;

    const handleVisibilityChange = async () => {
      if (document.hidden) {
        try {
          const resp = await quizApi.recordTabSwitch(attemptId);
          setTabWarning(resp.message);
          if (resp.auto_submitted_due_to_violations) {
            fetchResult(attemptId);
          }
        } catch {
          // ignore error
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isOpen, attemptId, quizResult]);

  // 60-second Question Countdown
  useEffect(() => {
    if (!isOpen || !currentQuestion || quizResult || isLoading) return;

    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current!);
          handleSubmit(null); // Time out
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isOpen, currentQuestion, quizResult, isLoading, handleSubmit]);

  useEffect(() => {
    if (isOpen) {
      initQuiz();
    } else {
      setAttemptId(null);
      setCurrentQuestion(null);
      setQuizResult(null);
      setErrorMsg(null);
      setTabWarning(null);
    }
  }, [isOpen, initQuiz]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-wide uppercase">
                {subjectSlug.toUpperCase()} Diagnostic Assessment
              </h2>
              <p className="text-xs text-slate-400">
                Calibrating your private skill matrix via Bayesian evaluation
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-white/10 text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switch Alert Banner */}
        {tabWarning && (
          <div className="px-6 py-2.5 bg-amber-500/10 border-b border-amber-500/20 flex items-center gap-2 text-amber-300 text-xs">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{tabWarning}</span>
          </div>
        )}

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {errorMsg ? (
            <div className="p-6 text-center space-y-4">
              <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-2xl inline-block">
                <AlertTriangle className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-white">Assessment Notice</h3>
              <p className="text-slate-300 text-sm max-w-md mx-auto">{errorMsg}</p>
              <button
                onClick={onClose}
                className="px-6 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium transition-colors"
              >
                Close
              </button>
            </div>
          ) : quizResult ? (
            /* Results Screen */
            <div className="space-y-6 animate-in fade-in duration-300">
              <div className="text-center space-y-2">
                <div className="inline-flex p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-extrabold text-white">Diagnostic Completed!</h3>
                <p className="text-xs text-slate-400">
                  Topic mastery has been updated in your private profile.
                </p>
              </div>

              {/* Topic Breakdown Bars */}
              <div className="space-y-3 bg-slate-800/40 p-4 rounded-2xl border border-white/5">
                <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
                  Topic Mastery Calibration
                </h4>
                <div className="space-y-3 pt-1">
                  {quizResult.topic_scores.map((t) => (
                    <div key={t.topic_slug} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-200 capitalize font-medium">
                          {t.topic_slug.replace(/-/g, ' ')}
                        </span>
                        <span className="text-brand-300 font-bold">{t.score.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                        <div
                          className="h-2 rounded-full bg-gradient-to-r from-brand-500 to-indigo-400 transition-all duration-700"
                          style={{ width: `${Math.min(100, Math.max(5, t.score))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="text-center pt-2">
                <button
                  onClick={onClose}
                  className="px-8 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-sm transition-all shadow-lg shadow-brand-500/25"
                >
                  View Learning Matrix
                </button>
              </div>
            </div>
          ) : currentQuestion ? (
            /* Question Screen */
            <div className="space-y-6">
              {/* Progress & Countdown Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-400">
                    Question {currentQuestion.current_index + 1} of {currentQuestion.total_questions}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-brand-500/10 text-brand-300 border border-brand-500/20">
                    {currentQuestion.topic_slug.replace(/-/g, ' ')}
                  </span>
                </div>

                {/* Circular Timer Indicator */}
                <div
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold font-mono transition-colors ${
                    timeLeft <= 10
                      ? 'bg-red-500/20 text-red-400 border border-red-500/30 animate-pulse'
                      : timeLeft <= 20
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'bg-slate-800 text-slate-200 border border-white/10'
                  }`}
                >
                  <Timer className="w-3.5 h-3.5" />
                  <span>{timeLeft}s</span>
                </div>
              </div>

              {/* Question Prompt */}
              <div className="space-y-3">
                <h3 className="text-base sm:text-lg font-medium text-slate-100 leading-snug">
                  {currentQuestion.prompt_text}
                </h3>

                {currentQuestion.code_snippet && (
                  <pre className="p-4 rounded-2xl bg-slate-950 border border-white/10 font-mono text-xs text-brand-300 overflow-x-auto leading-relaxed">
                    {currentQuestion.code_snippet}
                  </pre>
                )}
              </div>

              {/* Multiple Choice Options */}
              <div className="space-y-2.5">
                {currentQuestion.options.map((opt) => {
                  const isSelected = selectedOption === opt.id;
                  return (
                    <button
                      key={opt.id}
                      onClick={() => setSelectedOption(opt.id)}
                      className={`w-full p-4 rounded-2xl text-left transition-all border flex items-center justify-between cursor-pointer ${
                        isSelected
                          ? 'bg-brand-500/15 border-brand-400 text-white shadow-lg shadow-brand-500/10'
                          : 'bg-slate-800/40 border-white/5 hover:border-white/20 text-slate-300 hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold font-mono transition-colors ${
                            isSelected
                              ? 'bg-brand-500 text-white'
                              : 'bg-slate-800 text-slate-400 border border-white/10'
                          }`}
                        >
                          {opt.id}
                        </span>
                        <span className="text-sm font-medium">{opt.text}</span>
                      </div>
                      {isSelected && <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0" />}
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-400 space-y-3">
              <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-sm">Preparing diagnostic question bank...</p>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        {currentQuestion && !quizResult && !errorMsg && (
          <div className="px-6 py-4 border-t border-white/10 bg-slate-900/50 flex justify-between items-center">
            <span className="text-[11px] text-slate-500 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-brand-400" /> Auto-advances when timer expires
            </span>
            <button
              onClick={() => handleSubmit(selectedOption)}
              disabled={isLoading || !selectedOption}
              className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 disabled:pointer-events-none text-white text-sm font-medium transition-all shadow-md shadow-brand-500/20 flex items-center gap-2 cursor-pointer"
            >
              Next Question <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
