import React, { useState, useEffect } from 'react';
import {
  Brain,
  Sparkles,
  HelpCircle,
  PlayCircle,
  Loader2,
} from 'lucide-react';
import { quizApi, SkillProfileData } from '../../services/quizApi';
import { DiagnosticQuizModal } from '../quiz/DiagnosticQuizModal';

export const SkillMatrix: React.FC = () => {
  const [skillsData, setSkillsData] = useState<SkillProfileData | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<'dsa' | 'dbms'>('dsa');
  const [quizModalOpen, setQuizModalOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchSkills = async () => {
    setIsLoading(true);
    try {
      const data = await quizApi.getMySkills();
      setSkillsData(data);
    } catch {
      // Fallback if not authenticated or error
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSkills();
  }, []);

  const currentTopics = skillsData?.subjects?.[selectedSubject] || {};
  const topicKeys = Object.keys(currentTopics);

  return (
    <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 space-y-6">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
            <Brain className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Private Skill Calibration</h2>
            <p className="text-xs text-slate-400">
              Assessed via Bayesian estimation. Never shared publicly on leaderboards.
            </p>
          </div>
        </div>

        {/* Diagnostic Start Button */}
        <button
          onClick={() => setQuizModalOpen(true)}
          className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold tracking-wide transition-all shadow-md shadow-brand-500/20 flex items-center gap-2 cursor-pointer shrink-0"
        >
          <PlayCircle className="w-4 h-4" /> Take {selectedSubject.toUpperCase()} Diagnostic
        </button>
      </div>

      {/* Subject Tabs */}
      <div className="flex gap-2 border-b border-white/10 pb-3">
        <button
          onClick={() => setSelectedSubject('dsa')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            selectedSubject === 'dsa'
              ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Data Structures & Algorithms
        </button>
        <button
          onClick={() => setSelectedSubject('dbms')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            selectedSubject === 'dbms'
              ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Database Management Systems
        </button>
      </div>

      {/* Topic Mastery Grid */}
      {isLoading ? (
        <div className="py-12 flex flex-col items-center justify-center space-y-3 text-slate-400">
          <Loader2 className="w-7 h-7 animate-spin text-brand-400" />
          <p className="text-xs">Loading skill calibration...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {topicKeys.length === 0 ? (
            <div className="col-span-2 py-8 text-center text-slate-400 space-y-3 bg-slate-900/40 rounded-2xl border border-white/5 p-6">
              <HelpCircle className="w-8 h-8 text-slate-500 mx-auto" />
              <p className="text-sm font-medium text-slate-300">
                No diagnostic assessment recorded for {selectedSubject.toUpperCase()} yet.
              </p>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Take the 15-minute diagnostic to calculate your strengths and identify what you can teach vs learn.
              </p>
              <button
                onClick={() => setQuizModalOpen(true)}
                className="mt-2 px-6 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold transition-all inline-flex items-center gap-2 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5" /> Start Assessment
              </button>
            </div>
          ) : (
            topicKeys.map((topic) => {
              const skill = currentTopics[topic];
              const score = skill.score;
              const isStrength = score >= 70;
              const isGrowth = score <= 40;

              return (
                <div
                  key={topic}
                  className="p-4 rounded-2xl bg-slate-900/60 border border-white/5 hover:border-white/10 transition-all space-y-2.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-white capitalize">
                      {topic.replace(/-/g, ' ')}
                    </span>
                    <div className="flex items-center gap-1.5">
                      {isStrength && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Can Teach
                        </span>
                      )}
                      {isGrowth && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          Can Learn
                        </span>
                      )}
                      <span className="text-xs font-bold font-mono text-brand-300">
                        {score.toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Progress Track */}
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all duration-700 ${
                        isStrength
                          ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                          : isGrowth
                          ? 'bg-gradient-to-r from-amber-500 to-orange-400'
                          : 'bg-gradient-to-r from-brand-500 to-indigo-400'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(5, score))}%` }}
                    />
                  </div>

                  <div className="flex justify-between items-center text-[11px] text-slate-500 pt-1">
                    <span>Confidence: <strong className="text-slate-400 capitalize">{skill.confidence_level}</strong></span>
                    <span>Attempts: <strong className="text-slate-400">{skill.diagnostic_attempts_count}</strong></span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Modal Integration */}
      <DiagnosticQuizModal
        isOpen={quizModalOpen}
        onClose={() => setQuizModalOpen(false)}
        subjectSlug={selectedSubject}
        onComplete={fetchSkills}
      />
    </div>
  );
};
