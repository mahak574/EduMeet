import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, Loader2, ShieldAlert, X } from 'lucide-react';
import { apiClient } from '../../api/client';

interface ReportUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  reportedUserId: string;
  reportedUserName: string;
  sessionId?: string;
}

export const ReportUserModal: React.FC<ReportUserModalProps> = ({
  isOpen,
  onClose,
  reportedUserId,
  reportedUserName,
  sessionId,
}) => {
  const [reason, setReason] = useState<'harassment' | 'inappropriate_behavior' | 'no_show' | 'spam'>('inappropriate_behavior');
  const [details, setDetails] = useState('');
  const [blockUser, setBlockUser] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (details.trim().length < 10) {
      setError('Please provide at least 10 characters explaining the incident.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await apiClient('/safety/reports', {
        method: 'POST',
        body: JSON.stringify({
          reported_user_id: reportedUserId,
          session_id: sessionId || null,
          reason,
          details: details.trim(),
          block_user: blockUser,
        }),
      });
      setSubmitted(true);
    } catch (err: any) {
      setError(err.message || 'Failed to submit report. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-lg bg-slate-900 border border-rose-500/30 rounded-3xl p-6 sm:p-8 shadow-2xl shadow-rose-950/50">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white p-2 rounded-xl hover:bg-white/5 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {submitted ? (
          <div className="text-center py-6 space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <CheckCircle className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-white">Report Submitted to Trust & Safety</h3>
            <p className="text-sm text-slate-300 max-w-sm mx-auto leading-relaxed">
              Thank you for keeping our peer community safe. Our academic moderation team investigates all reports immediately.
              {blockUser && ' You will not be paired with this participant in future matching cycles.'}
            </p>
            <div className="pt-4">
              <button
                onClick={onClose}
                className="w-full py-3 rounded-2xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-sm transition-all cursor-pointer"
              >
                Close Window
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-2xl bg-rose-500/20 text-rose-400 border border-rose-500/30">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Report Participant</h3>
                <p className="text-xs text-slate-400">
                  Filing a confidential Trust & Safety report against <span className="text-rose-300 font-semibold">{reportedUserName}</span>
                </p>
              </div>
            </div>

            {error && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center gap-2.5 text-xs text-rose-300">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-300">Reason</label>
              <select
                value={reason}
                onChange={(e) => setReason(e.target.value as any)}
                className="w-full bg-slate-800/80 border border-white/10 rounded-2xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-rose-400 transition-colors cursor-pointer"
              >
                <option value="inappropriate_behavior">Inappropriate / Unprofessional Behavior</option>
                <option value="harassment">Harassment or Offensive Language</option>
                <option value="no_show">No-Show / Abandoned Session Early</option>
                <option value="spam">Spam / Commercial Solicitations</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-300">Details & Context</label>
              <textarea
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                placeholder="Describe what occurred with specific details to assist moderator investigation..."
                rows={4}
                className="w-full bg-slate-800/80 border border-white/10 rounded-2xl p-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-rose-400 transition-colors resize-none"
              />
              <span className="text-[11px] text-slate-400">Minimum 10 characters required.</span>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-800/50 border border-white/5 flex items-center justify-between">
              <div>
                <span className="text-sm font-semibold text-white block">Block this participant</span>
                <span className="text-xs text-slate-400">Permanently prevents matching together in future schedules.</span>
              </div>
              <input
                type="checkbox"
                checked={blockUser}
                onChange={(e) => setBlockUser(e.target.checked)}
                className="w-5 h-5 rounded accent-rose-500 cursor-pointer"
              />
            </div>

            <div className="pt-2 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold transition-all cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2.5 rounded-2xl bg-rose-600 hover:bg-rose-500 text-white text-sm font-semibold transition-all flex items-center gap-2 shadow-lg shadow-rose-600/30 cursor-pointer disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldAlert className="w-4 h-4" />}
                Submit Report
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
