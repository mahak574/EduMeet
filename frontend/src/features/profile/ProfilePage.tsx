import React, { useState } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { apiClient } from '../../api/client';
import { User } from '../../types';
import {
  User as UserIcon,
  Globe,
  Clock,
  BookOpen,
  GraduationCap,
  Sparkles,
  Download,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Plus,
  X,
} from 'lucide-react';

const COMMON_TIMEZONES = [
  'UTC',
  'Asia/Kolkata',
  'America/New_York',
  'America/Los_Angeles',
  'America/Chicago',
  'Europe/London',
  'Europe/Berlin',
  'Europe/Paris',
  'Asia/Tokyo',
  'Asia/Singapore',
  'Australia/Sydney',
];

const TEACHING_STYLES = [
  { id: 'example_heavy', label: 'Example-Heavy', desc: 'Step-by-step code and practical walkthroughs' },
  { id: 'visual', label: 'Visual & Diagrams', desc: 'Whiteboard models, memory flowcharts, and architecture maps' },
  { id: 'socratic', label: 'Socratic Method', desc: 'Guiding through questions, hypothesis testing, and active recall' },
  { id: 'theoretical', label: 'First Principles', desc: 'Formal proofs, asymptotic logic, and invariant correctness' },
] as const;

const LEARNING_GOAL_OPTIONS = [
  'Tech Placements & Interviews',
  'Semester University Exams',
  'GATE / Master Entrance Exams',
  'Deep Systems Mastery',
  'Open Source Contribution',
];

export const ProfilePage: React.FC = () => {
  const { user, updateUser, logout } = useAuthStore();
  if (!user) return null;

  const [fullName, setFullName] = useState(user.full_name || '');
  const [country, setCountry] = useState(user.country || 'IN');
  const [timezone, setTimezone] = useState(user.timezone || 'UTC');
  const [teachingStyle, setTeachingStyle] = useState(user.preferences?.preferred_teaching_style || 'example_heavy');
  const [learningGoals, setLearningGoals] = useState<string[]>(user.preferences?.learning_goals || ['Tech Placements & Interviews']);
  const [subjects, setSubjects] = useState<string[]>(user.subjects_studied.length ? user.subjects_studied : ['maths', 'python']);
  const [newSubject, setNewSubject] = useState('');
  const [instEmail, setInstEmail] = useState('');
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleAddSubject = (e: React.KeyboardEvent | React.MouseEvent) => {
    if ('key' in e && e.key !== 'Enter') return;
    e.preventDefault();
    const clean = newSubject.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-');
    if (clean && !subjects.includes(clean)) {
      setSubjects([...subjects, clean]);
      setNewSubject('');
    }
  };

  const handleRemoveSubject = (slug: string) => {
    setSubjects(subjects.filter((s) => s !== slug));
  };

  const toggleGoal = (goal: string) => {
    if (learningGoals.includes(goal)) {
      setLearningGoals(learningGoals.filter((g) => g !== goal));
    } else {
      setLearningGoals([...learningGoals, goal]);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setStatusMessage(null);
    try {
      const updated = await apiClient<User>('/users/me', {
        method: 'PATCH',
        body: JSON.stringify({
          full_name: fullName,
          country,
          timezone,
          subjects_studied: subjects,
          preferred_teaching_style: teachingStyle,
          learning_goals: learningGoals,
        }),
      });
      updateUser(updated);
      setStatusMessage({ text: 'Profile changes saved successfully.', type: 'success' });
    } catch (err: any) {
      setStatusMessage({ text: err.message || 'Failed to update profile.', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleVerifyStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!instEmail || !instEmail.includes('@')) return;
    try {
      await apiClient('/users/me/verify-student', {
        method: 'POST',
        body: JSON.stringify({ institutional_email: instEmail }),
      });
      const updated = await apiClient<User>('/users/me');
      updateUser(updated);
      setStatusMessage({ text: 'Verified student badge activated!', type: 'success' });
      setInstEmail('');
    } catch (err: any) {
      setStatusMessage({ text: err.message || 'Verification failed.', type: 'error' });
    }
  };

  const handleExportData = async () => {
    try {
      const res = await apiClient<{ user_data: any; exported_at: string }>('/users/me/export');
      const blob = new Blob([JSON.stringify(res, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `edumeet_data_export_${user.email}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setStatusMessage({ text: 'Data export failed: ' + err.message, type: 'error' });
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await apiClient('/users/me', { method: 'DELETE' });
      await logout();
    } catch (err: any) {
      setStatusMessage({ text: 'Failed to delete account: ' + err.message, type: 'error' });
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 space-y-8 animate-in fade-in duration-300">
      {/* Header Profile Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <UserIcon className="w-8 h-8 text-brand-400" />
            Student Profile & Preferences
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Global pairing uses your topic proficiencies and teaching style to match complementary peers.
          </p>
        </div>
        {user.is_verified_student && (
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
            <GraduationCap className="w-4 h-4" /> Verified Student
          </div>
        )}
      </div>

      {statusMessage && (
        <div
          className={`p-4 rounded-xl flex items-center gap-3 text-sm ${
            statusMessage.type === 'success'
              ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
              : 'bg-red-500/10 border border-red-500/20 text-red-300'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
          )}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Main Form */}
      <form onSubmit={handleSaveProfile} className="space-y-6">
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-6">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Globe className="w-5 h-5 text-brand-400" /> Basic Information
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                Full Name
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Alex Rivera"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-brand-500 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                Primary Account Email
              </label>
              <input
                type="email"
                disabled
                value={user.email}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900/50 border border-slate-800 text-slate-400 text-sm cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                Country (ISO Code)
              </label>
              <input
                type="text"
                maxLength={2}
                value={country}
                onChange={(e) => setCountry(e.target.value.toUpperCase())}
                placeholder="IN, US, UK, DE, CA"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-400" /> Timezone
              </label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500 transition-all cursor-pointer"
              >
                {COMMON_TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Subjects Studied */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-brand-400" /> Subjects Studied
          </h2>
          <p className="text-xs text-slate-400">
            Enter topics or subjects you either want to learn or teach (e.g. <code>maths</code>, <code>physics</code>, <code>python</code>).
          </p>

          <div className="flex flex-wrap gap-2 pt-2">
            {subjects.map((s) => (
              <span
                key={s}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-mono font-medium"
              >
                #{s}
                <button
                  type="button"
                  onClick={() => handleRemoveSubject(s)}
                  className="hover:text-white transition-colors"
                  aria-label={`Remove subject ${s}`}
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </span>
            ))}
          </div>

          <div className="flex gap-2 max-w-sm pt-2">
            <input
              type="text"
              value={newSubject}
              onChange={(e) => setNewSubject(e.target.value)}
              onKeyDown={handleAddSubject}
              placeholder="Add subject (e.g. python)"
              className="flex-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs placeholder-slate-500 focus:outline-none focus:border-brand-500"
            />
            <button
              type="button"
              onClick={handleAddSubject}
              className="px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white text-xs rounded-xl flex items-center gap-1 transition-all cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" /> Add
            </button>
          </div>
        </div>

        {/* Preferred Teaching Style */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-brand-400" /> Preferred Teaching Style
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {TEACHING_STYLES.map((style) => (
              <div
                key={style.id}
                onClick={() => setTeachingStyle(style.id)}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  teachingStyle === style.id
                    ? 'bg-brand-500/15 border-brand-500 shadow-md shadow-brand-500/10 text-white'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 text-slate-300'
                }`}
              >
                <div className="font-semibold text-sm">{style.label}</div>
                <div className="text-xs text-slate-400 mt-1">{style.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Learning Goals */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-lg font-bold text-white">Current Learning Goals</h2>
          <div className="flex flex-wrap gap-2.5">
            {LEARNING_GOAL_OPTIONS.map((goal) => {
              const active = learningGoals.includes(goal);
              return (
                <button
                  type="button"
                  key={goal}
                  onClick={() => toggleGoal(goal)}
                  className={`px-3.5 py-2 rounded-xl text-xs font-medium border transition-all cursor-pointer ${
                    active
                      ? 'bg-brand-600 border-brand-500 text-white shadow-sm'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                  }`}
                >
                  {goal}
                </button>
              );
            })}
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="w-full sm:w-auto px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-sm transition-all shadow-lg shadow-brand-500/20 disabled:opacity-50 cursor-pointer"
        >
          {saving ? 'Saving...' : 'Save Profile Changes'}
        </button>
      </form>

      {/* Optional Institutional Verification */}
      <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <GraduationCap className="w-5 h-5 text-emerald-400" />
          Optional Student Verification Badge
        </h2>
        <p className="text-xs text-slate-400">
          EduMeet is open to everyone regardless of university enrollment. If you possess an institutional student email (e.g. <code>.edu</code>, <code>.ac.in</code>), you can claim a verified badge.
        </p>

        {!user.is_verified_student ? (
          <form onSubmit={handleVerifyStudent} className="flex gap-3 max-w-md pt-2">
            <input
              type="email"
              required
              placeholder="student@university.edu"
              value={instEmail}
              onChange={(e) => setInstEmail(e.target.value)}
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-none focus:border-brand-500"
            />
            <button
              type="submit"
              className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded-xl transition-all cursor-pointer"
            >
              Verify
            </button>
          </form>
        ) : (
          <div className="text-xs text-emerald-300 flex items-center gap-2 pt-2">
            <CheckCircle2 className="w-4 h-4" /> Verified institutional address on record.
          </div>
        )}
      </div>

      {/* Data Privacy & GDPR */}
      <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
        <h2 className="text-lg font-bold text-white">Data Privacy & Portability</h2>
        <p className="text-xs text-slate-400">
          Your diagnostic scores and improvement records are completely private to you and your matched peers. There are no public leaderboards or rankings anywhere on EduMeet.
        </p>
        <div className="flex flex-wrap gap-4 pt-2">
          <button
            type="button"
            onClick={handleExportData}
            className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium flex items-center gap-2 transition-all cursor-pointer"
          >
            <Download className="w-4 h-4" /> Export Personal Data (JSON)
          </button>

          {!confirmDelete ? (
            <button
              type="button"
              onClick={() => setConfirmDelete(true)}
              className="px-4 py-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-300 text-xs font-medium flex items-center gap-2 transition-all cursor-pointer"
            >
              <Trash2 className="w-4 h-4" /> Delete Account & Purge Data
            </button>
          ) : (
            <div className="flex items-center gap-2 p-2 rounded-xl bg-red-950/40 border border-red-500/40">
              <span className="text-xs text-red-300">Permanently delete everything?</span>
              <button
                type="button"
                onClick={handleDeleteAccount}
                className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white text-xs rounded-lg font-medium cursor-pointer"
              >
                Yes, delete
              </button>
              <button
                type="button"
                onClick={() => setConfirmDelete(false)}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg cursor-pointer"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
