import React, { useState, useEffect } from 'react';
import {
  Users,
  Sparkles,
  CheckCircle2,
  XCircle,
  Calendar,
  Clock,
  ArrowRight,
  Loader2,
  ShieldCheck,
  Video,
  BookOpen,
  GraduationCap,
  Globe,
  RefreshCw,
  UserCheck,
  LogIn,
} from 'lucide-react';
import { matchingApi, MatchResponse, PoolStatusResponse, PoolRosterResponse, QueuePeerInfo } from '../../services/matchingApi';
import { format } from 'date-fns';
import { useAuthStore } from '../../stores/authStore';
import { AuthModal } from '../auth/AuthModal';

export const MatchConfirmationCard: React.FC = () => {
  const { user, isAuthenticated } = useAuthStore();
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);
  const [poolStatus, setPoolStatus] = useState<PoolStatusResponse | null>(null);
  const [activeMatch, setActiveMatch] = useState<MatchResponse | null>(null);
  const [roster, setRoster] = useState<PoolRosterResponse | null>(null);
  const [isRosterLoading, setIsRosterLoading] = useState<boolean>(false);
  const [selectedSlot, setSelectedSlot] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchRoster = async () => {
    setIsRosterLoading(true);
    try {
      const rosterData = await matchingApi.getLiveRoster();
      setRoster(rosterData);
    } catch {
      // ignore
    } finally {
      setIsRosterLoading(false);
    }
  };

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [poolRes, matchRes, rosterRes] = await Promise.all([
        matchingApi.getPoolStatus(),
        matchingApi.getActiveMatch(),
        matchingApi.getLiveRoster().catch(() => null),
      ]);
      setPoolStatus(poolRes);
      setActiveMatch(matchRes);
      if (rosterRes) {
        setRoster(rosterRes);
      }
      if (matchRes?.proposed_slots && matchRes.proposed_slots.length > 0) {
        setSelectedSlot(matchRes.proposed_slots[0]);
      }
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh queue roster every 20 seconds to show active peers
    const interval = setInterval(() => {
      fetchRoster();
    }, 20000);
    return () => clearInterval(interval);
  }, []);

  const handleJoinPool = async () => {
    if (!isAuthenticated) {
      setAuthModalOpen(true);
      return;
    }

    setIsSubmitting(true);
    setActionMessage(null);
    try {
      const subjects = user?.subjects_studied?.length ? user.subjects_studied : undefined;
      const res = await matchingApi.joinPool(subjects);
      setPoolStatus(res);
      setActionMessage('You have joined the matching queue! Pairings run automatically.');
    } catch (err: any) {
      setActionMessage(err.message || 'Failed to join pool. Complete a diagnostic quiz first.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLeavePool = async () => {
    setIsSubmitting(true);
    try {
      await matchingApi.leavePool();
      setPoolStatus({ is_in_pool: false, subject_slugs: [] });
      setActionMessage('You left the matching queue.');
    } catch (err: any) {
      setActionMessage(err.message || 'Failed to leave pool.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmMatch = async () => {
    if (!activeMatch || !selectedSlot) return;
    setIsSubmitting(true);
    setActionMessage(null);
    try {
      const res = await matchingApi.confirmMatch(activeMatch.id, selectedSlot);
      if (res.is_mutual) {
        setActionMessage('Session confirmed! Both students have accepted.');
      } else {
        setActionMessage('Confirmed! Awaiting your partner\'s mutual confirmation.');
      }
      await fetchData();
    } catch (err: any) {
      setActionMessage(err.message || 'Failed to confirm match.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeclineMatch = async () => {
    if (!activeMatch) return;
    setIsSubmitting(true);
    setActionMessage(null);
    try {
      await matchingApi.declineMatch(activeMatch.id, 'Declined by user');
      setActiveMatch(null);
      setActionMessage('Match proposal declined. You remain in control of your matches.');
      await fetchData();
    } catch (err: any) {
      setActionMessage(err.message || 'Failed to decline match.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
      </div>
    );
  }

  // 1. STATE: Active Match Proposal or Confirmed Session
  if (activeMatch) {
    const isMutual = activeMatch.status === 'confirmed' && activeMatch.session_id;

    return (
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-brand-500/30 bg-gradient-to-br from-brand-950/40 via-slate-900/60 to-slate-950/60 space-y-6 relative overflow-hidden shadow-xl shadow-brand-950/50">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Users className="w-48 h-48 text-brand-400" />
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-brand-500/20 text-brand-300 border border-brand-500/30">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold text-white tracking-tight">
                  {isMutual ? 'Confirmed Peer Session' : 'Reciprocal Match Proposed!'}
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                  Strict 1:1
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Paired with <strong className="text-white">{activeMatch.partner_name}</strong> based on complementary skill gaps.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <span className="text-xs font-mono px-3 py-1 rounded-xl bg-slate-800 border border-white/10 text-slate-300 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Gain: {(activeMatch.score * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Reciprocal Teaching Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-500/20 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">You Will Teach (25 min)</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300">Your Strength</span>
            </div>
            <p className="text-base font-bold text-white capitalize">
              {activeMatch.my_teach_topic?.replace(/-/g, ' ')}
            </p>
            <p className="text-xs text-slate-400">
              Subject: <strong className="text-slate-300 uppercase">{activeMatch.my_teach_subject}</strong>
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-amber-950/20 border border-amber-500/20 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">You Will Learn (25 min)</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300">Growth Goal</span>
            </div>
            <p className="text-base font-bold text-white capitalize">
              {activeMatch.my_learn_topic?.replace(/-/g, ' ')}
            </p>
            <p className="text-xs text-slate-400">
              Taught by: <strong className="text-slate-300">{activeMatch.partner_name}</strong>
            </p>
          </div>
        </div>

        {/* Slot Selector & Confirmation Controls */}
        {isMutual ? (
          <div className="p-4 rounded-2xl bg-slate-900/80 border border-emerald-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
              <div>
                <p className="text-sm font-bold text-white">Mutual Agreement Reached</p>
                <p className="text-xs text-slate-400">
                  Video room & collaborative editor ready 5 minutes prior to scheduled start.
                </p>
              </div>
            </div>
            <a
              href={`/session/${activeMatch.session_id}`}
              className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold tracking-wide transition-all shadow-md shadow-emerald-500/20 flex items-center justify-center gap-2"
            >
              <Video className="w-4 h-4" /> Go to Waiting Room
            </a>
          </div>
        ) : (
          <div className="space-y-4 pt-2">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-brand-400" /> Select a Continuous Overlapping Time Slot:
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {activeMatch.proposed_slots.map((slot: string) => {
                  const dt = new Date(slot);
                  const isSelected = selectedSlot === slot;
                  return (
                    <button
                      key={slot}
                      type="button"
                      onClick={() => setSelectedSlot(slot)}
                      className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-brand-500/20 border-brand-500 text-white shadow-md shadow-brand-500/10'
                          : 'bg-slate-900/60 border-white/10 text-slate-400 hover:text-white hover:border-white/20'
                      }`}
                    >
                      <div className="text-xs font-bold">{format(dt, 'EEE, MMM d')}</div>
                      <div className="text-[11px] font-mono text-brand-300 flex items-center gap-1 mt-0.5">
                        <Clock className="w-3 h-3" /> {format(dt, 'h:mm a')} UTC
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Action Bar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-white/10">
              <div className="text-xs text-slate-400">
                {activeMatch.has_confirmed ? (
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> You confirmed this match. Waiting for {activeMatch.partner_name}...
                  </span>
                ) : (
                  <span>Please confirm before the proposal window expires in 24 hours.</span>
                )}
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <button
                  type="button"
                  disabled={isSubmitting}
                  onClick={handleDeclineMatch}
                  className="px-4 py-2.5 rounded-xl border border-rose-500/30 hover:bg-rose-500/10 text-rose-300 text-xs font-semibold transition-all cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <XCircle className="w-4 h-4" /> Decline
                </button>
                <button
                  type="button"
                  disabled={isSubmitting || activeMatch.has_confirmed || !selectedSlot}
                  onClick={handleConfirmMatch}
                  className={`px-6 py-2.5 rounded-xl text-white text-xs font-semibold tracking-wide transition-all flex items-center justify-center gap-2 cursor-pointer shadow-md ${
                    activeMatch.has_confirmed
                      ? 'bg-slate-700 cursor-not-allowed opacity-60'
                      : 'bg-brand-600 hover:bg-brand-500 shadow-brand-500/25'
                  }`}
                >
                  {isSubmitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" /> Confirm Match
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {actionMessage && (
          <p className="text-xs text-center text-brand-300 pt-1">{actionMessage}</p>
        )}
      </div>
    );
  }

  // Render Helper: Live Active Peer Roster
  const renderRosterSection = (_inPool: boolean) => (
    <div className="space-y-3 pt-2">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-1 border-b border-white/10">
        <div className="flex items-center gap-2">
          <div className="relative flex items-center justify-center">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping absolute" />
            <span className="w-2 h-2 rounded-full bg-emerald-400 relative" />
          </div>
          <h4 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
            <Users className="w-4 h-4 text-brand-400" />
            Active Peers in Matching Pool ({roster?.total_active_in_queue ?? 0})
          </h4>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">
            Reciprocal Bipartite Graph
          </span>
          <button
            type="button"
            onClick={fetchRoster}
            disabled={isRosterLoading}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-400 hover:text-white transition-colors cursor-pointer text-xs flex items-center gap-1"
            title="Refresh active queue roster"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRosterLoading ? 'animate-spin text-brand-400' : ''}`} />
            <span className="text-[10px]">Refresh</span>
          </button>
        </div>
      </div>

      {/* Peer Cards List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
        {roster?.peers && roster.peers.length > 0 ? (
          roster.peers.map((peer: QueuePeerInfo) => {
            return (
              <div
                key={peer.user_id}
                className={`p-4 rounded-2xl border transition-all space-y-3 ${
                  peer.is_me
                    ? 'bg-brand-950/20 border-brand-500/40'
                    : peer.is_compatible
                    ? 'bg-slate-900/60 border-emerald-500/40 shadow-sm shadow-emerald-500/10'
                    : 'bg-slate-900/40 border-white/10'
                }`}
              >
                {/* Header: Peer info & Suitability Badge */}
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-600 to-indigo-700 flex items-center justify-center font-bold text-xs text-white uppercase shadow-sm">
                      {peer.display_name.charAt(0)}
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-white">
                          {peer.display_name}
                        </span>
                        {peer.is_me && (
                          <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-brand-500/20 text-brand-300">
                            YOU
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-slate-400">
                        <span className="flex items-center gap-1">
                          <Globe className="w-2.5 h-2.5" /> {peer.country}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-2.5 h-2.5" /> Waiting {peer.waiting_minutes}m
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Compatibility Badge */}
                  <div>
                    {peer.is_compatible ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold">
                        <Sparkles className="w-3 h-3 text-emerald-400" />
                        Suitable for You
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-400 text-[10px]">
                        {peer.compatibility_label}
                      </span>
                    )}
                  </div>
                </div>

                {/* Subject Pairing Breakdown */}
                <div className="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-white/5">
                  <div className="p-2.5 rounded-xl bg-emerald-950/20 border border-emerald-500/20 space-y-1">
                    <div className="flex items-center gap-1 text-[10px] font-semibold text-emerald-400 uppercase tracking-wide">
                      <GraduationCap className="w-3 h-3" />
                      <span>Teaches</span>
                    </div>
                    <p className="font-bold text-white capitalize text-xs line-clamp-1">
                      {peer.teaches_subjects.join(', ') || 'Diagnostic Calibrated'}
                    </p>
                    {peer.teach_topics.length > 0 && (
                      <p className="text-[10px] text-slate-400 line-clamp-1 capitalize">
                        {peer.teach_topics.slice(0, 2).map((t: string) => t.replace(/-/g, ' ')).join(', ')}
                      </p>
                    )}
                  </div>

                  <div className="p-2.5 rounded-xl bg-amber-950/20 border border-amber-500/20 space-y-1">
                    <div className="flex items-center gap-1 text-[10px] font-semibold text-amber-400 uppercase tracking-wide">
                      <BookOpen className="w-3 h-3" />
                      <span>Learns</span>
                    </div>
                    <p className="font-bold text-white capitalize text-xs line-clamp-1">
                      {peer.learns_subjects.join(', ') || 'All Electives'}
                    </p>
                    {peer.learn_topics.length > 0 && (
                      <p className="text-[10px] text-slate-400 line-clamp-1 capitalize">
                        {peer.learn_topics.slice(0, 2).map((t: string) => t.replace(/-/g, ' ')).join(', ')}
                      </p>
                    )}
                  </div>
                </div>

                {/* Compatibility explanation */}
                {peer.is_compatible && (
                  <div className="text-[11px] text-emerald-300/90 flex items-center gap-1.5 pt-0.5">
                    <UserCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>Reciprocal Fit: They teach what you need, and need what you teach.</span>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="col-span-2 p-6 rounded-2xl bg-white/5 border border-white/10 text-center space-y-1.5">
            <Users className="w-6 h-6 text-slate-400 mx-auto" />
            <p className="text-xs text-white font-medium">No other students in the queue right now.</p>
            <p className="text-[11px] text-slate-400">
              Enter the pool to register your availability. You will be paired automatically when a reciprocal student joins.
            </p>
          </div>
        )}
      </div>
    </div>
  );

  // 2. STATE: In Matching Pool (Waiting for algorithm run)
  if (poolStatus?.is_in_pool) {
    return (
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-brand-500/20 bg-slate-900/40 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center">
              <span className="absolute w-8 h-8 rounded-full bg-brand-500/30 animate-ping" />
              <div className="p-3 rounded-2xl bg-brand-500/20 border border-brand-500/30 text-brand-400 relative">
                <Users className="w-6 h-6" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white tracking-tight">Active in Matching Pool</h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Ready for Pairings
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Reciprocal Bipartite Graph matches you based on complementary skill gaps (25m teach / 25m learn / 10m quiz).
              </p>
            </div>
          </div>

          <button
            type="button"
            disabled={isSubmitting}
            onClick={handleLeavePool}
            className="px-4 py-2 rounded-xl border border-white/10 hover:border-white/20 text-slate-400 hover:text-white text-xs font-medium transition-all cursor-pointer"
          >
            Leave Queue
          </button>
        </div>

        {actionMessage && (
          <p className="text-xs text-brand-300 pt-1">{actionMessage}</p>
        )}

        {/* Live Active Peers & Compatibility View */}
        {renderRosterSection(true)}
      </div>
    );
  }

  // 3. STATE: Idle / Not in Matching Pool
  return (
    <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 bg-slate-900/40 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div className="space-y-1.5 max-w-xl">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-white tracking-tight">Reciprocal Peer Teaching</h3>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-brand-500/10 text-brand-400 border border-brand-500/20">
              Graph Matching Active
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Get paired for a 1-hour session: <strong>25 min</strong> you teach your strength, <strong>25 min</strong> your partner teaches theirs, followed by a <strong>10 min</strong> reciprocal peer quiz.
          </p>
        </div>

        <button
          type="button"
          disabled={isSubmitting}
          onClick={handleJoinPool}
          className="px-6 py-3 rounded-2xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold tracking-wide transition-all shadow-lg shadow-brand-500/25 flex items-center justify-center gap-2 cursor-pointer shrink-0"
        >
          {isSubmitting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : !isAuthenticated ? (
            <>
              <LogIn className="w-4 h-4" /> Log In to Join Matching Pool
            </>
          ) : (
            <>
              <Users className="w-4 h-4" /> Enter Matching Pool <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>

      {actionMessage && (
        <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-in fade-in">
          <span>{actionMessage}</span>
          {actionMessage.toLowerCase().includes('diagnostic') && (
            <a
              href="#skill-matrix"
              onClick={() => {
                const el = document.getElementById('skill-matrix') || document.querySelector('button[title*="Assessment"]');
                el?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="px-3 py-1.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 font-bold border border-amber-500/30 text-center transition-all shrink-0 cursor-pointer"
            >
              Take Diagnostic Quiz →
            </a>
          )}
        </div>
      )}

      {/* Live Active Peers & Compatibility View */}
      {renderRosterSection(false)}

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
