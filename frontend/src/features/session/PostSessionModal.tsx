import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  CheckCircle2,
  Star,
  ArrowRight,
  TrendingUp,
  Loader2,
  X,
} from 'lucide-react';
import { reviewApi, PostCheckResult } from '../../services/reviewApi';
import { useNavigate } from 'react-router-dom';

interface PostSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  partnerName: string;
  learnedTopic: string;
}

export const PostSessionModal: React.FC<PostSessionModalProps> = ({
  isOpen,
  onClose,
  sessionId,
  partnerName,
  learnedTopic,
}) => {
  const navigate = useNavigate();

  const [step, setStep] = useState<'check' | 'delta' | 'rating' | 'done'>('check');
  const [questions, setQuestions] = useState<any[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [postResult, setPostResult] = useState<PostCheckResult | null>(null);
  const [clarity, setClarity] = useState<number>(5);
  const [helpfulness, setHelpfulness] = useState<number>(5);
  const [feedbackText, setFeedbackText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen || !sessionId) return;
    const fetchQuestions = async () => {
      setIsLoading(true);
      try {
        const qs = await reviewApi.getPostcheckQuestions(sessionId);
        setQuestions(qs);
      } catch {
        // ignore
      } finally {
        setIsLoading(false);
      }
    };
    fetchQuestions();
  }, [isOpen, sessionId]);

  const handleSubmitPostcheck = async () => {
    setIsLoading(true);
    try {
      const res = await reviewApi.submitPostcheck(sessionId, answers);
      setPostResult(res);
      setStep('delta');
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitRating = async () => {
    setIsLoading(true);
    try {
      await reviewApi.submitSessionRating(sessionId, clarity, helpfulness, feedbackText);
      setStep('done');
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in">
      <div className="glass-panel w-full max-w-xl rounded-3xl border border-white/10 p-6 sm:p-8 space-y-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-all"
        >
          <X className="w-5 h-5" />
        </button>

        {/* STEP 1: HELD-OUT POST-CHECK */}
        {step === 'check' && (
          <div className="space-y-5">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-brand-500/20 text-brand-300 border border-brand-500/30">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white tracking-tight">Post-Session Evaluation</h3>
                <p className="text-xs text-slate-400">
                  Measure your learning gain on <strong className="text-white capitalize">{learnedTopic.replace(/-/g, ' ')}</strong>.
                </p>
              </div>
            </div>

            {isLoading ? (
              <div className="py-12 flex justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
              </div>
            ) : questions.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-400 space-y-3">
                <p>No post-check questions found for this session.</p>
                <button
                  onClick={() => setStep('rating')}
                  className="px-5 py-2 rounded-xl bg-brand-600 text-white text-xs font-semibold"
                >
                  Proceed to Rate Partner
                </button>
              </div>
            ) : (
              <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-1">
                {questions.map((q, idx) => (
                  <div key={q.question_id} className="p-4 rounded-xl bg-slate-900/80 border border-white/5 space-y-2.5">
                    <p className="text-xs font-semibold text-slate-200">
                      {idx + 1}. {q.prompt_text}
                    </p>
                    <div className="space-y-1.5">
                      {q.options.map((opt: any) => (
                        <button
                          key={opt.id}
                          type="button"
                          onClick={() => setAnswers({ ...answers, [q.question_id]: opt.id })}
                          className={`w-full p-2.5 rounded-lg text-left text-xs transition-all border ${
                            answers[q.question_id] === opt.id
                              ? 'bg-brand-500/20 border-brand-500 text-white'
                              : 'bg-slate-800/40 border-white/5 text-slate-400 hover:text-white'
                          }`}
                        >
                          <span className="font-bold mr-2 text-brand-300">{opt.id}.</span> {opt.text}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}

                <button
                  onClick={handleSubmitPostcheck}
                  disabled={isLoading || Object.keys(answers).length < questions.length}
                  className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold tracking-wide transition-all disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-brand-500/25"
                >
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Submit Post-Check <ArrowRight className="w-4 h-4" /></>}
                </button>
              </div>
            )}
          </div>
        )}

        {/* STEP 2: LEARNING GAIN DELTA */}
        {step === 'delta' && postResult && (
          <div className="text-center space-y-6 py-2">
            <div className="p-3 w-14 h-14 mx-auto rounded-2xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center">
              <TrendingUp className="w-8 h-8" />
            </div>

            <div className="space-y-2">
              <h3 className="text-xl font-bold text-white tracking-tight">Learning Gain Measured!</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Compared to your pre-session baseline, here is your measured topic growth:
              </p>
            </div>

            {/* Score Delta Display */}
            <div className="grid grid-cols-3 gap-3 p-4 rounded-2xl bg-slate-900/80 border border-white/10">
              <div className="space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-500">Pre-Session</span>
                <p className="text-base font-bold text-slate-300 font-mono">
                  {postResult.pre_score_percentage?.toFixed(0) ?? '50'}%
                </p>
              </div>
              <div className="space-y-1 border-x border-white/10">
                <span className="text-[10px] uppercase font-bold text-slate-500">Post-Session</span>
                <p className="text-base font-bold text-emerald-400 font-mono">
                  {postResult.post_score_percentage.toFixed(0)}%
                </p>
              </div>
              <div className="space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-500">Gain (Δ)</span>
                <p className="text-base font-bold text-brand-300 font-mono">
                  {postResult.learning_gain_delta >= 0 ? `+${postResult.learning_gain_delta.toFixed(0)}` : postResult.learning_gain_delta.toFixed(0)}%
                </p>
              </div>
            </div>

            <button
              onClick={() => setStep('rating')}
              className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold tracking-wide transition-all flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-brand-500/25"
            >
              Rate Partner's Teaching <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* STEP 3: 5-STAR PARTNER RATING */}
        {step === 'rating' && (
          <div className="space-y-5">
            <div className="text-center space-y-1.5">
              <h3 className="text-lg font-bold text-white tracking-tight">Rate {partnerName}'s Teaching</h3>
              <p className="text-xs text-slate-400">
                Ratings are mutual and confidential. High ratings unlock partner portfolios.
              </p>
            </div>

            <div className="space-y-4">
              {/* Clarity Rating */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-200">Teaching Clarity</span>
                  <span className="font-bold font-mono text-brand-300">{clarity} / 5</span>
                </div>
                <div className="flex gap-2 justify-center py-1">
                  {[1, 2, 3, 4, 5].map((val) => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => setClarity(val)}
                      className={`p-2 rounded-xl transition-all ${
                        clarity >= val ? 'text-amber-400 scale-110' : 'text-slate-600 hover:text-slate-400'
                      }`}
                    >
                      <Star className="w-6 h-6 fill-current" />
                    </button>
                  ))}
                </div>
              </div>

              {/* Helpfulness Rating */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-200">Helpfulness & Engagement</span>
                  <span className="font-bold font-mono text-brand-300">{helpfulness} / 5</span>
                </div>
                <div className="flex gap-2 justify-center py-1">
                  {[1, 2, 3, 4, 5].map((val) => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => setHelpfulness(val)}
                      className={`p-2 rounded-xl transition-all ${
                        helpfulness >= val ? 'text-amber-400 scale-110' : 'text-slate-600 hover:text-slate-400'
                      }`}
                    >
                      <Star className="w-6 h-6 fill-current" />
                    </button>
                  ))}
                </div>
              </div>

              {/* Feedback text */}
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-400">Constructive Feedback (Optional)</label>
                <textarea
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="What did your partner explain exceptionally well?"
                  rows={2}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl p-3 text-xs text-white placeholder-slate-500 outline-none focus:border-brand-500 resize-none"
                />
              </div>

              <button
                onClick={handleSubmitRating}
                disabled={isLoading}
                className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold tracking-wide transition-all disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-brand-500/25"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Submit Rating & Complete Session <ArrowRight className="w-4 h-4" /></>}
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: CELEBRATION & EXIT */}
        {step === 'done' && (
          <div className="text-center space-y-5 py-4">
            <div className="p-3 w-16 h-16 mx-auto rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center">
              <CheckCircle2 className="w-10 h-10" />
            </div>

            <div className="space-y-1.5">
              <h3 className="text-xl font-bold text-white tracking-tight">Session Fully Completed!</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Thank you for contributing to the reciprocal learning network. Your skill calibration and weekly consistency have been updated.
              </p>
            </div>

            <button
              onClick={() => {
                onClose();
                navigate('/');
              }}
              className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold tracking-wide transition-all cursor-pointer shadow-lg shadow-brand-500/25"
            >
              Return to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
