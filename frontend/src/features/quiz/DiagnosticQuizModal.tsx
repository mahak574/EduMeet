import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import {
  Timer,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  X,
  ArrowRight,
  BrainCircuit,
  ShieldAlert,
  LogIn,
  GraduationCap,
  ChevronRight,
  RotateCcw,
  Lightbulb,
  Code2,
  Award,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { User } from '../../types';
import { quizApi, CurrentQuestion, QuizResult } from '../../services/quizApi';
import { useAuthStore } from '../../stores/authStore';
import { AuthModal } from '../auth/AuthModal';

export const MATH_GRADE_TRACKS = [
  {
    slug: 'maths-elementary',
    title: 'Class 1–5 (Primary School)',
    grade: 'Primary',
    subtitle: 'Practical arithmetic, word problems, basic fractions, 2D/3D shapes & measurement units',
    icon: '🎒',
    topics: ['Arithmetic Word Problems', 'Fractions & Decimals', 'Perimeter & Shapes', 'Units of Measure'],
  },
  {
    slug: 'maths-high-school',
    title: 'Class 6–10 (Secondary School)',
    grade: 'Secondary',
    subtitle: 'Linear equations, quadratics, percentages & profit-loss, trigonometry & surface areas',
    icon: '🏫',
    topics: ['Algebra & Linear Equations', 'Trigonometry & Heights', 'Percentages & Profit-Loss', 'Coordinate Geometry'],
  },
  {
    slug: 'maths-class-11-12',
    title: 'Class 11–12 (Higher Secondary)',
    grade: 'Senior Sec',
    subtitle: 'Differential & integral calculus, matrices, determinants, vectors & 3D coordinate geometry',
    icon: '📐',
    topics: ['Differential Calculus', 'Integral Calculus', 'Matrices & Determinants', 'Vectors & 3D Space'],
  },
  {
    slug: 'maths-engineering',
    title: 'Engineering & Higher Tech (STEM)',
    grade: 'B.Tech / STEM',
    subtitle: 'Multivariable calculus, linear algebra, eigenvalues, differential equations & numerical methods',
    icon: '⚙️',
    topics: ['Multivariable Calculus', 'Eigenvalues & Vectors', 'Differential Equations', 'Numerical Methods'],
  },
  {
    slug: 'maths-commerce-ca',
    title: 'Commerce, CA & Business Finance',
    grade: 'CA / Commerce',
    subtitle: 'Time value of money, compound interest annuities, marginal business calculus & statistics',
    icon: '📊',
    topics: ['Time Value of Money & Annuities', 'Marginal Revenue & Cost', 'Linear Programming & LPP', 'Correlation & Indices'],
  },
  {
    slug: 'maths',
    title: 'General Quantitative Aptitude',
    grade: 'General',
    subtitle: 'Real-world commercial arithmetic, ratios, work & time, percentages, simple & compound interest',
    icon: '⚡',
    topics: ['Commercial Arithmetic', 'Percentages & Ratios', 'Work & Time Equations', 'Mensuration & Averages'],
  },
];

interface DiagnosticQuizModalProps {
  isOpen: boolean;
  onClose: () => void;
  subjectSlug: string;
  onComplete?: () => void;
}

export const DiagnosticQuizModal: React.FC<DiagnosticQuizModalProps> = ({
  isOpen,
  onClose,
  subjectSlug,
  onComplete,
}) => {
  const { isAuthenticated, user, updateUser } = useAuthStore();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<CurrentQuestion | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState<number>(60);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [tabWarning, setTabWarning] = useState<string | null>(null);
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);
  const [reviewFilter, setReviewFilter] = useState<'all' | 'wrong' | 'correct'>('all');

  // Age confirmation state for unconfirmed users
  const [ageChecked, setAgeChecked] = useState<boolean>(false);
  const [isConfirmingAge, setIsConfirmingAge] = useState<boolean>(false);

  // Math level selection state
  const isGenericMath = subjectSlug.toLowerCase() === 'maths' || subjectSlug.toLowerCase() === 'mathematics';
  const isAnyMath = subjectSlug.toLowerCase().startsWith('math');
  const [activeSlug, setActiveSlug] = useState<string>(subjectSlug);
  const [showLevelPicker, setShowLevelPicker] = useState<boolean>(isGenericMath);

  const startTimeRef = useRef<number>(Date.now());
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize or start diagnostic attempt
  const startAssessment = useCallback(async (slugToStart: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    setQuizResult(null);

    try {
      const data = await quizApi.startQuiz(slugToStart);
      setAttemptId(data.attempt_id);
      loadNextQuestion(data.attempt_id);
    } catch (err: any) {
      setErrorMsg(err.message || err.detail || 'Failed to start diagnostic.');
      setIsLoading(false);
    }
  }, []);

  const handleConfirmAgeAndStart = async () => {
    setIsConfirmingAge(true);
    try {
      const updated = await apiClient<User>('/users/me', {
        method: 'PATCH',
        body: JSON.stringify({ age_confirmed: true }),
      });
      if (user) {
        updateUser({ ...user, ...updated, age_confirmed: true });
      }
      setErrorMsg(null);
      await startAssessment(activeSlug);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update age confirmation.');
    } finally {
      setIsConfirmingAge(false);
    }
  };

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
      if (err.status === 400 || err.message?.toLowerCase().includes('completed')) {
        fetchResult(aId);
      } else {
        setErrorMsg(err.message || 'Failed to load question.');
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
      setErrorMsg(err.message || 'Failed to load results.');
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

  // Anti-cheat tab visibility detection
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && attemptId && !quizResult) {
        quizApi
          .recordTabSwitch(attemptId)
          .then((res) => {
            if (res.auto_submitted_due_to_violations) {
              fetchResult(attemptId);
            } else {
              setTabWarning(
                `Warning: Tab-switching is monitored. ${res.tab_switch_count}/2 violations detected.`
              );
            }
          })
          .catch(() => {});
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [attemptId, quizResult]);

  // Server-synchronized 60-second countdown timer
  useEffect(() => {
    if (!isOpen || !currentQuestion || quizResult || isLoading) return;

    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current!);
          handleSubmit(null);
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
      setActiveSlug(subjectSlug);
      if (isGenericMath) {
        setShowLevelPicker(true);
      } else {
        setShowLevelPicker(false);
        startAssessment(subjectSlug);
      }
    } else {
      setAttemptId(null);
      setCurrentQuestion(null);
      setQuizResult(null);
      setErrorMsg(null);
      setTabWarning(null);
      setShowLevelPicker(false);
    }
  }, [isOpen, subjectSlug, isGenericMath, startAssessment]);

  if (!isOpen) return null;

  const currentTrackInfo = MATH_GRADE_TRACKS.find((t) => t.slug === activeSlug);

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-4 md:p-6 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-white/15 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
              {isAnyMath ? <GraduationCap className="w-5 h-5 text-emerald-400" /> : <BrainCircuit className="w-5 h-5" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-white tracking-wide uppercase">
                  {currentTrackInfo ? currentTrackInfo.title : `${activeSlug.replace(/-/g, ' ')} Diagnostic`}
                </h2>
                {isAnyMath && !showLevelPicker && (
                  <button
                    type="button"
                    onClick={() => setShowLevelPicker(true)}
                    className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 hover:bg-white/10 text-emerald-300 border border-emerald-500/30 transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <RotateCcw className="w-2.5 h-2.5" /> Change Level
                  </button>
                )}
              </div>
              <p className="text-xs text-slate-400">
                Practical calculation assessment & Bayesian IRT skill calibration
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
          {/* 1. Grade / Level Picker for Mathematics */}
          {showLevelPicker ? (
            <div className="space-y-4 animate-in fade-in">
              <div className="text-center space-y-1.5 pb-2">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
                  <GraduationCap className="w-3.5 h-3.5" /> Grade & Career Track Selection
                </div>
                <h3 className="text-lg font-bold text-white">
                  Select Your Mathematics Level
                </h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
                  Mathematics differs across grades and professional streams. Select your level to receive practical, calculation-based questions tailored specifically to your curriculum.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                {MATH_GRADE_TRACKS.map((track) => (
                  <button
                    key={track.slug}
                    onClick={() => {
                      setActiveSlug(track.slug);
                      setShowLevelPicker(false);
                      startAssessment(track.slug);
                    }}
                    className="p-4 rounded-2xl bg-white/5 hover:bg-emerald-500/15 border border-white/10 hover:border-emerald-500/40 text-left transition-all group flex flex-col justify-between space-y-2 cursor-pointer shadow-sm hover:shadow-emerald-500/10"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xl">{track.icon}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-emerald-300 border border-white/10 font-semibold">
                          {track.grade}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">
                        {track.title}
                      </h4>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed line-clamp-2">
                        {track.subtitle}
                      </p>
                    </div>

                    <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-emerald-400 font-medium">
                      <span>Practical assessment</span>
                      <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : errorMsg ? (
            <div className="p-6 text-center space-y-4">
              {errorMsg.toLowerCase().includes('age confirmation') ? (
                <>
                  <div className="p-3 bg-brand-500/10 border border-brand-500/20 text-brand-400 rounded-2xl inline-block">
                    <ShieldCheck className="w-8 h-8" />
                  </div>
                  <h3 className="text-lg font-bold text-white">Age Confirmation Required</h3>
                  <p className="text-slate-300 text-sm max-w-md mx-auto leading-relaxed">
                    EduMeet requires students to confirm they are 18 years of age or older before taking diagnostic assessments and participating in peer study sessions.
                  </p>

                  <div className="max-w-md mx-auto p-4 rounded-2xl bg-slate-800/70 border border-slate-700 text-left">
                    <label className="flex items-start gap-3 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={ageChecked}
                        onChange={(e) => setAgeChecked(e.target.checked)}
                        className="mt-0.5 rounded border-slate-600 text-brand-500 focus:ring-brand-500 cursor-pointer"
                      />
                      <span className="text-xs text-slate-200 font-medium leading-relaxed">
                        I confirm that I am at least 18 years old and agree to mutual peer teaching standards.
                      </span>
                    </label>
                  </div>

                  <div className="flex items-center justify-center gap-3 pt-2">
                    <button
                      type="button"
                      onClick={onClose}
                      className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition-colors cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      disabled={!ageChecked || isConfirmingAge}
                      onClick={handleConfirmAgeAndStart}
                      className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold transition-all shadow-md shadow-brand-500/25 flex items-center gap-2 cursor-pointer"
                    >
                      {isConfirmingAge ? (
                        <>
                          <RotateCcw className="w-4 h-4 animate-spin" /> Confirming...
                        </>
                      ) : (
                        <>
                          Confirm & Start Quiz <ArrowRight className="w-4 h-4" />
                        </>
                      )}
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-2xl inline-block">
                    <AlertTriangle className="w-8 h-8" />
                  </div>
                  <h3 className="text-lg font-bold text-white">Assessment Notice</h3>
                  <p className="text-slate-300 text-sm max-w-md mx-auto">{errorMsg}</p>
                  <div className="flex items-center justify-center gap-3 pt-2">
                    <button
                      onClick={onClose}
                      className="px-6 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium transition-colors cursor-pointer"
                    >
                      Close
                    </button>
                    {isAnyMath && (
                      <button
                        onClick={() => setShowLevelPicker(true)}
                        className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-all cursor-pointer"
                      >
                        Select Another Level
                      </button>
                    )}
                    {!isAuthenticated && (
                      <button
                        onClick={() => setAuthModalOpen(true)}
                        className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium transition-all shadow-md shadow-brand-500/25 flex items-center gap-2 cursor-pointer"
                      >
                        <LogIn className="w-4 h-4" /> Log In / Sign Up
                      </button>
                    )}
                  </div>
                </>
              )}
            </div>
          ) : quizResult ? (
            /* Comprehensive Academic Report Card Screen */
            <div className="space-y-6 animate-in fade-in duration-300">
              {/* Report Card Header & Status Banner */}
              <div className="text-center space-y-2 pb-2">
                <div className="inline-flex p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  <Award className="w-8 h-8" />
                </div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-semibold text-slate-300">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  Academic Assessment Report Card
                </div>
                <h3 className="text-2xl font-extrabold text-white tracking-tight">
                  {currentTrackInfo ? currentTrackInfo.title : activeSlug.replace(/-/g, ' ')} Calibration
                </h3>
                <p className="text-xs text-slate-400 max-w-lg mx-auto">
                  Your diagnostic evaluation is complete. Review your performance breakdown, correct vs incorrect submissions, and conceptual explanations below.
                </p>
              </div>

              {/* KPI Score Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-4 rounded-2xl bg-white/5 border border-white/10 text-center space-y-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Overall Score</span>
                  <p className="text-2xl font-black text-emerald-400">
                    {(quizResult.overall_score_percentage ?? 0).toFixed(0)}%
                  </p>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 font-medium">
                    {(quizResult.overall_score_percentage ?? 0) >= 80 ? 'Mastery' : (quizResult.overall_score_percentage ?? 0) >= 50 ? 'Proficient' : 'Needs Practice'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-500/20 text-center space-y-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-emerald-400">Correct</span>
                  <p className="text-2xl font-black text-emerald-400">
                    {quizResult.correct_answers_count ?? (quizResult.questions_review?.filter((r) => r.is_correct).length || 0)}
                  </p>
                  <span className="text-[10px] text-slate-400">Verified Answers</span>
                </div>

                <div className="p-4 rounded-2xl bg-rose-950/20 border border-rose-500/20 text-center space-y-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-rose-400">Incorrect</span>
                  <p className="text-2xl font-black text-rose-400">
                    {quizResult.incorrect_answers_count ?? (quizResult.questions_review?.filter((r) => !r.is_correct && !r.timed_out).length || 0)}
                  </p>
                  <span className="text-[10px] text-slate-400">Review Required</span>
                </div>

                <div className="p-4 rounded-2xl bg-amber-950/20 border border-amber-500/20 text-center space-y-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-400">Timed Out</span>
                  <p className="text-2xl font-black text-amber-400">
                    {quizResult.timed_out_count ?? (quizResult.questions_review?.filter((r) => r.timed_out).length || 0)}
                  </p>
                  <span className="text-[10px] text-slate-400">60s Exceeded</span>
                </div>
              </div>

              {/* Topic Mastery Calibration Bars */}
              {quizResult.topic_scores && quizResult.topic_scores.length > 0 && (
                <div className="space-y-3 bg-slate-800/40 p-4 sm:p-5 rounded-2xl border border-white/5">
                  <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider flex items-center justify-between">
                    <span>Topic-by-Topic Mastery Calibration</span>
                    <span className="text-[10px] text-slate-500 font-mono">Bayesian IRT Engine</span>
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    {quizResult.topic_scores.map((t) => (
                      <div key={t.topic_slug} className="space-y-1.5 p-3 rounded-xl bg-black/20 border border-white/5">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-200 capitalize font-medium text-xs">
                            {t.topic_slug.replace(/-/g, ' ')}
                          </span>
                          <span className="text-emerald-300 font-bold">{t.score.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                          <div
                            className="h-2 rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-700"
                            style={{ width: `${Math.min(100, Math.max(5, t.score))}%` }}
                          />
                        </div>
                        <div className="flex justify-between items-center text-[10px] text-slate-400 pt-0.5">
                          <span>Confidence</span>
                          <span className="capitalize text-slate-300 font-mono">{t.confidence_level}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Detailed Question-by-Question Academic Review */}
              {quizResult.questions_review && quizResult.questions_review.length > 0 && (
                <div className="space-y-4 pt-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-1 border-b border-white/10">
                    <div>
                      <h4 className="text-sm font-bold text-white flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        Detailed Question Review & Conceptual Solutions
                      </h4>
                      <p className="text-xs text-slate-400">
                        Compare your chosen answers against the verified keys and examine step-by-step conceptual walkthroughs.
                      </p>
                    </div>

                    {/* Filter Tabs */}
                    <div className="flex items-center gap-1.5 bg-black/30 p-1 rounded-xl border border-white/10 text-xs self-start sm:self-auto">
                      <button
                        type="button"
                        onClick={() => setReviewFilter('all')}
                        className={`px-3 py-1 rounded-lg font-medium transition-all cursor-pointer ${
                          reviewFilter === 'all'
                            ? 'bg-brand-600 text-white shadow-sm'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        All ({quizResult.questions_review.length})
                      </button>
                      <button
                        type="button"
                        onClick={() => setReviewFilter('wrong')}
                        className={`px-3 py-1 rounded-lg font-medium transition-all cursor-pointer flex items-center gap-1 ${
                          reviewFilter === 'wrong'
                            ? 'bg-rose-600 text-white shadow-sm'
                            : 'text-rose-300/80 hover:text-rose-200'
                        }`}
                      >
                        <XCircle className="w-3 h-3" />
                        Wrong ({quizResult.questions_review.filter((r) => !r.is_correct).length})
                      </button>
                      <button
                        type="button"
                        onClick={() => setReviewFilter('correct')}
                        className={`px-3 py-1 rounded-lg font-medium transition-all cursor-pointer flex items-center gap-1 ${
                          reviewFilter === 'correct'
                            ? 'bg-emerald-600 text-white shadow-sm'
                            : 'text-emerald-300/80 hover:text-emerald-200'
                        }`}
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        Correct ({quizResult.questions_review.filter((r) => r.is_correct).length})
                      </button>
                    </div>
                  </div>

                  {/* Question Cards List */}
                  <div className="space-y-4">
                    {quizResult.questions_review
                      .filter((item) => {
                        if (reviewFilter === 'wrong') return !item.is_correct;
                        if (reviewFilter === 'correct') return item.is_correct;
                        return true;
                      })
                      .map((q, qIndex) => {
                        const originalIndex = quizResult.questions_review!.findIndex(
                          (orig) => orig.question_id === q.question_id
                        );
                        const displayIndex = originalIndex >= 0 ? originalIndex + 1 : qIndex + 1;

                        return (
                          <div
                            key={q.question_id}
                            className={`p-5 rounded-2xl border transition-all space-y-4 ${
                              q.is_correct
                                ? 'bg-slate-900/40 border-emerald-500/30'
                                : q.timed_out
                                ? 'bg-slate-900/40 border-amber-500/30'
                                : 'bg-slate-900/40 border-rose-500/30'
                            }`}
                          >
                            {/* Card Header */}
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <span className="px-2.5 py-0.5 rounded-lg bg-white/10 font-mono text-xs text-white font-bold">
                                  Q{displayIndex}
                                </span>
                                <span className="text-xs font-semibold text-slate-300 capitalize">
                                  {q.topic_slug.replace(/-/g, ' ')}
                                </span>
                                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-400 capitalize">
                                  {q.difficulty}
                                </span>
                              </div>

                              <div>
                                {q.is_correct ? (
                                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-bold">
                                    <CheckCircle2 className="w-3.5 h-3.5" /> Correct Answer (+1.0)
                                  </span>
                                ) : q.timed_out ? (
                                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-bold">
                                    <Timer className="w-3.5 h-3.5" /> Timed Out (0.0)
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 text-xs font-bold">
                                    <XCircle className="w-3.5 h-3.5" /> Incorrect Answer (0.0)
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Prompt */}
                            <div className="space-y-3">
                              <p className="text-sm font-semibold text-white leading-relaxed">
                                {q.prompt_text}
                              </p>

                              {/* Code snippet if programming / practical */}
                              {q.code_snippet && (
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between px-3 py-1 bg-slate-950 rounded-t-xl border-t border-x border-white/10 text-[10px] font-mono text-slate-400">
                                    <span className="flex items-center gap-1.5 text-emerald-400">
                                      <Code2 className="w-3 h-3" /> Code Snippet
                                    </span>
                                    <span>Python 3.x</span>
                                  </div>
                                  <pre className="p-4 rounded-b-xl bg-black/70 border border-white/10 font-mono text-xs text-emerald-300 overflow-x-auto leading-relaxed">
                                    {q.code_snippet}
                                  </pre>
                                </div>
                              )}
                            </div>

                            {/* Options List with Visual Feedback */}
                            <div className="space-y-2 pt-1">
                              {q.options.map((opt) => {
                                const isUserChoice = q.selected_option_id === opt.id;
                                const isCorrectChoice = q.correct_option_id === opt.id;

                                let cardStyle = 'bg-white/5 border-white/5 text-slate-300';
                                let badge = null;

                                if (isCorrectChoice && isUserChoice) {
                                  cardStyle = 'bg-emerald-500/20 border-emerald-500/60 text-emerald-100 font-medium';
                                  badge = (
                                    <span className="text-[11px] font-bold text-emerald-300 flex items-center gap-1">
                                      <CheckCircle2 className="w-3.5 h-3.5" /> Your Choice (Correct ✓)
                                    </span>
                                  );
                                } else if (isCorrectChoice && !isUserChoice) {
                                  cardStyle = 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200 font-medium';
                                  badge = (
                                    <span className="text-[11px] font-bold text-emerald-400 flex items-center gap-1">
                                      <CheckCircle2 className="w-3.5 h-3.5" /> Correct Answer Key ✓
                                    </span>
                                  );
                                } else if (isUserChoice && !isCorrectChoice) {
                                  cardStyle = 'bg-rose-950/40 border-rose-500/50 text-rose-200';
                                  badge = (
                                    <span className="text-[11px] font-bold text-rose-300 flex items-center gap-1">
                                      <XCircle className="w-3.5 h-3.5" /> Your Choice (Incorrect ✕)
                                    </span>
                                  );
                                }

                                return (
                                  <div
                                    key={opt.id}
                                    className={`p-3.5 rounded-xl border flex items-center justify-between text-xs transition-colors ${cardStyle}`}
                                  >
                                    <div className="flex items-center gap-3">
                                      <span
                                        className={`w-6 h-6 rounded-lg flex items-center justify-center font-bold text-xs ${
                                          isCorrectChoice
                                            ? 'bg-emerald-500 text-white'
                                            : isUserChoice
                                            ? 'bg-rose-500 text-white'
                                            : 'bg-white/10 text-slate-400'
                                        }`}
                                      >
                                        {opt.id}
                                      </span>
                                      <span className="font-sans">{opt.text}</span>
                                    </div>
                                    {badge}
                                  </div>
                                );
                              })}
                            </div>

                            {/* Deep Conceptual Explanation Box */}
                            <div className="p-4 rounded-xl bg-brand-950/40 border border-brand-500/30 space-y-1.5 mt-2">
                              <div className="flex items-center gap-2 text-brand-300 text-xs font-bold uppercase tracking-wider">
                                <Lightbulb className="w-4 h-4 text-amber-400" />
                                <span>Conceptual Answer & Step-by-Step Solution</span>
                              </div>
                              <p className="text-xs text-slate-300 leading-relaxed pl-6 whitespace-pre-line font-sans">
                                {q.explanation}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}

              {/* Bottom Actions */}
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4 border-t border-white/10">
                {isAnyMath && (
                  <button
                    onClick={() => {
                      setQuizResult(null);
                      setShowLevelPicker(true);
                    }}
                    className="w-full sm:w-auto px-6 py-2.5 rounded-xl border border-white/10 hover:bg-white/10 text-slate-300 text-xs font-semibold transition-all cursor-pointer"
                  >
                    Assess Another Mathematics Level
                  </button>
                )}
                <button
                  onClick={onClose}
                  className="w-full sm:w-auto px-8 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs tracking-wide transition-all shadow-lg shadow-emerald-500/25 cursor-pointer"
                >
                  Return to Dashboard
                </button>
              </div>
            </div>
          ) : currentQuestion ? (
            /* Active Question Screen */
            <div className="space-y-6 animate-in fade-in duration-200">
              {/* Question Progress and 60-Second Timer */}
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 font-mono text-slate-300">
                    Question {currentQuestion.current_index + 1} of {currentQuestion.total_questions}
                  </span>
                  <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 capitalize font-medium">
                    {currentQuestion.topic_slug.replace(/-/g, ' ')}
                  </span>
                </div>

                <div
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-lg font-mono font-bold text-xs transition-colors ${
                    timeLeft <= 15
                      ? 'bg-red-500/20 text-red-300 border border-red-500/30 animate-pulse'
                      : 'bg-white/5 text-slate-200 border border-white/10'
                  }`}
                >
                  <Timer className="w-3.5 h-3.5" />
                  <span>{timeLeft}s</span>
                </div>
              </div>

              {/* Question Prompt */}
              <div className="space-y-4">
                <h3 className="text-base sm:text-lg font-semibold text-white leading-relaxed">
                  {currentQuestion.prompt_text}
                </h3>

                {currentQuestion.code_snippet && (
                  <pre className="p-4 rounded-2xl bg-black/50 border border-white/10 font-mono text-xs text-emerald-300 overflow-x-auto">
                    {currentQuestion.code_snippet}
                  </pre>
                )}
              </div>

              {/* Options List */}
              <div className="space-y-2.5">
                {currentQuestion.options.map((opt) => {
                  const isSelected = selectedOption === opt.id;
                  return (
                    <button
                      key={opt.id}
                      onClick={() => setSelectedOption(opt.id)}
                      disabled={isLoading}
                      className={`w-full p-4 rounded-2xl border text-left transition-all flex items-center justify-between cursor-pointer ${
                        isSelected
                          ? 'bg-emerald-500/15 border-emerald-500/60 text-white shadow-md shadow-emerald-500/10'
                          : 'bg-white/5 hover:bg-white/10 border-white/5 text-slate-200'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`w-7 h-7 rounded-xl flex items-center justify-center font-bold text-xs transition-colors ${
                            isSelected
                              ? 'bg-emerald-500 text-white'
                              : 'bg-white/10 text-slate-300'
                          }`}
                        >
                          {opt.id}
                        </span>
                        <span className="text-sm font-medium">{opt.text}</span>
                      </div>
                      {isSelected && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="py-12 flex flex-col items-center justify-center space-y-3">
              <div className="w-6 h-6 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs text-slate-400">Loading diagnostic curriculum...</p>
            </div>
          )}
        </div>

        {/* Sticky Pinned Submit Footer for Active Questions */}
        {currentQuestion && !quizResult && !showLevelPicker && !errorMsg && (
          <div className="shrink-0 px-6 py-3.5 border-t border-white/10 bg-slate-900/95 flex items-center justify-between z-20">
            <div className="text-xs text-slate-400">
              {selectedOption ? (
                <span className="text-emerald-300 font-medium">Option {selectedOption} selected</span>
              ) : (
                <span className="text-slate-400">Select an option above to submit</span>
              )}
            </div>
            <button
              onClick={() => handleSubmit(selectedOption)}
              disabled={!selectedOption || isLoading}
              className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold tracking-wide transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2 cursor-pointer"
            >
              {isLoading ? 'Verifying...' : 'Submit & Proceed'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      <AuthModal isOpen={authModalOpen} onClose={() => setAuthModalOpen(false)} />
    </div>,
    document.body
  );
};
