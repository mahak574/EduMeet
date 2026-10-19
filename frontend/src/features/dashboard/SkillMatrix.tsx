import React, { useState, useEffect } from 'react';
import {
  Brain,
  Sparkles,
  HelpCircle,
  PlayCircle,
  Loader2,
  Plus,
  CheckCircle2,
  BookOpen,
} from 'lucide-react';
import { quizApi, SkillProfileData } from '../../services/quizApi';
import { DiagnosticQuizModal } from '../quiz/DiagnosticQuizModal';
import { useAuthStore } from '../../stores/authStore';
import { apiClient } from '../../api/client';
import { APIResponse } from '../../types';

export const SkillMatrix: React.FC = () => {
  const { user, updateUser } = useAuthStore();
  const [skillsData, setSkillsData] = useState<SkillProfileData | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<string>('dsa');
  const [quizModalOpen, setQuizModalOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [showAddSubject, setShowAddSubject] = useState<boolean>(false);
  const [newSubjectInput, setNewSubjectInput] = useState<string>('');

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

  // Compute union of user's studied subjects and calibrated profile subjects
  const subjectsFromProfile = Object.keys(skillsData?.subjects || {});
  const subjectsFromUser = user?.subjects_studied || [];
  const allSubjects = Array.from(
    new Set([...subjectsFromUser, ...subjectsFromProfile, 'dsa', 'dbms'])
  ).filter(Boolean);

  // Keep selected subject valid
  useEffect(() => {
    if (!allSubjects.includes(selectedSubject) && allSubjects.length > 0) {
      setSelectedSubject(allSubjects[0]);
    }
  }, [allSubjects, selectedSubject]);

  const currentTopics = skillsData?.subjects?.[selectedSubject] || {};
  const topicKeys = Object.keys(currentTopics);

  const handleAddSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleaned = newSubjectInput.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-');
    if (!cleaned) return;

    if (!allSubjects.includes(cleaned)) {
      const updatedList = Array.from(new Set([...subjectsFromUser, cleaned]));
      try {
        const res = await apiClient<APIResponse<any>>('/users/me', {
          method: 'PATCH',
          body: JSON.stringify({ subjects_studied: updatedList }),
        });
        if (res?.data) {
          updateUser(res.data);
        }
      } catch (err) {
        console.error('Failed to update subjects studied:', err);
      }
    }
    setSelectedSubject(cleaned);
    setNewSubjectInput('');
    setShowAddSubject(false);
  };

  // Calculate proficiency counts across all subjects
  let totalProficient = 0;
  let totalLearningTargets = 0;
  if (skillsData?.subjects) {
    Object.values(skillsData.subjects).forEach((subTopics) => {
      Object.values(subTopics).forEach((topic) => {
        if (topic.score >= 70) {
          totalProficient += 1;
        } else {
          totalLearningTargets += 1;
        }
      });
    });
  }

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
              Evaluated via Bayesian IRT estimation. ≥70% classifies as Proficient (Ready to Teach).
            </p>
          </div>
        </div>

        {/* Action Header Items */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setQuizModalOpen(true)}
            className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold tracking-wide transition-all shadow-md shadow-brand-500/20 flex items-center gap-2 cursor-pointer shrink-0"
          >
            <PlayCircle className="w-4 h-4" /> Start {selectedSubject.toUpperCase()} Assessment
          </button>
        </div>
      </div>

      {/* Global Mastery Summary Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-3.5 rounded-2xl bg-slate-900/50 border border-white/5 text-xs">
        <div>
          <span className="text-slate-400 block text-[11px]">Calibrated Subjects</span>
          <span className="font-bold text-white font-mono text-sm">{allSubjects.length} subjects</span>
        </div>
        <div>
          <span className="text-emerald-400 block text-[11px] font-medium">Proficient Topics (≥70%)</span>
          <span className="font-bold text-emerald-300 font-mono text-sm">{totalProficient} ready to teach</span>
        </div>
        <div className="col-span-2 sm:col-span-1">
          <span className="text-amber-400 block text-[11px] font-medium">Learning Targets (&lt;70%)</span>
          <span className="font-bold text-amber-300 font-mono text-sm">{totalLearningTargets} for peer study</span>
        </div>
      </div>

      {/* Dynamic Subject Tabs & Add Button */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-3 overflow-x-auto custom-scrollbar">
        {allSubjects.map((subj) => {
          const isSelected = selectedSubject === subj;
          return (
            <button
              key={subj}
              onClick={() => setSelectedSubject(subj)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer uppercase tracking-wider shrink-0 ${
                isSelected
                  ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30 shadow-md'
                  : 'text-slate-400 hover:text-white bg-slate-900/30 border border-transparent'
              }`}
            >
              {subj.replace(/-/g, ' ')}
            </button>
          );
        })}

        {/* Add Custom Subject Button */}
        {showAddSubject ? (
          <form onSubmit={handleAddSubject} className="flex items-center gap-1.5 shrink-0">
            <input
              type="text"
              autoFocus
              value={newSubjectInput}
              onChange={(e) => setNewSubjectInput(e.target.value)}
              placeholder="e.g. python, operating-systems"
              className="bg-slate-800 border border-brand-500/40 rounded-xl px-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none w-44"
            />
            <button
              type="submit"
              className="px-2.5 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition-all cursor-pointer"
            >
              Add
            </button>
            <button
              type="button"
              onClick={() => setShowAddSubject(false)}
              className="px-2 py-1.5 rounded-xl text-slate-400 hover:text-white text-xs cursor-pointer"
            >
              Cancel
            </button>
          </form>
        ) : (
          <button
            onClick={() => setShowAddSubject(true)}
            className="px-3 py-2 rounded-xl text-xs font-semibold text-brand-400 hover:text-brand-300 bg-brand-500/10 hover:bg-brand-500/20 border border-dashed border-brand-500/30 transition-all flex items-center gap-1 shrink-0 cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" /> Add Subject
          </button>
        )}
      </div>

      {/* Topic Mastery Grid */}
      {isLoading ? (
        <div className="py-12 flex flex-col items-center justify-center space-y-3 text-slate-400">
          <Loader2 className="w-7 h-7 animate-spin text-brand-400" />
          <p className="text-xs">Loading Bayesian skill calibration...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {topicKeys.length === 0 ? (
            <div className="col-span-2 py-8 text-center text-slate-400 space-y-3 bg-slate-900/40 rounded-2xl border border-white/5 p-6">
              <HelpCircle className="w-8 h-8 text-slate-500 mx-auto" />
              <p className="text-sm font-medium text-slate-300">
                No diagnostic assessment recorded for <span className="uppercase text-brand-300 font-bold">{selectedSubject.replace(/-/g, ' ')}</span> yet.
              </p>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Take the adaptive diagnostic assessment to calibrate your skill score across topics and unlock complementary peer matching.
              </p>
              <button
                onClick={() => setQuizModalOpen(true)}
                className="mt-2 px-6 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold transition-all inline-flex items-center gap-2 cursor-pointer shadow-md shadow-brand-500/20"
              >
                <Sparkles className="w-3.5 h-3.5" /> Start Assessment
              </button>
            </div>
          ) : (
            topicKeys.map((topic) => {
              const skill = currentTopics[topic];
              const score = skill.score;
              const isProficient = score >= 70;

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
                      {isProficient ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> Proficient (Can Teach)
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1">
                          <BookOpen className="w-3 h-3" /> Learning Target
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
                        isProficient
                          ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                          : 'bg-gradient-to-r from-amber-500 to-orange-400'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(5, score))}%` }}
                    />
                  </div>

                  <div className="flex justify-between items-center text-[11px] text-slate-500 pt-1">
                    <span>
                      Confidence: <strong className="text-slate-400 capitalize">{skill.confidence_level}</strong>
                    </span>
                    <span>
                      Attempts: <strong className="text-slate-400">{skill.diagnostic_attempts_count}</strong>
                    </span>
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
