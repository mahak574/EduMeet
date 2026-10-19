import React from 'react';
import {
  Sparkles,
  GitMerge,
  Scale,
  Calendar,
} from 'lucide-react';
import { MatchConfirmationCard } from './MatchConfirmationCard';

export const MatchingHubPage: React.FC = () => {

  return (
    <div className="space-y-8 animate-in fade-in max-w-5xl mx-auto pb-12">
      {/* Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-brand-500/20 bg-gradient-to-br from-indigo-950/20 via-slate-900/60 to-slate-950/60 space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-300 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" /> Reciprocal Peer Matching
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Graph-Based Complementary Matchmaking
        </h1>
        <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
          EduMeet never puts you in random chat rooms. Our NetworkX graph matching algorithm pairs you with another student who excels in the exact subtopics where you have growth gaps, and vice versa.
        </p>
      </div>

      {/* Main Matching Queue & Proposals Card */}
      <MatchConfirmationCard />

      {/* How Matching Engine Works */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
          <div className="p-2.5 rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20 w-fit">
            <GitMerge className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-white text-base">Reciprocal Gain Metric</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Pairs are weighted by reciprocal knowledge gains: <code className="text-brand-300 font-mono text-[11px] block mt-1">Gain = (Gap_A × Advantage_B) + (Gap_B × Advantage_A)</code>
          </p>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 w-fit">
            <Scale className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-white text-base">Equal 25/25 Contribution</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Every session is strictly reciprocal: you teach for 25 minutes, your partner teaches for 25 minutes, followed by a 10-minute quiz exchange.
          </p>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
          <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 w-fit">
            <Calendar className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-white text-base">Availability Overlap</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            The matcher requires at least a 60-minute contiguous timeslot overlap in shared preferred languages before generating a mutual proposal.
          </p>
        </div>
      </div>

      {/* Match Protocol Guidelines */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 bg-slate-900/40 space-y-4">
        <h3 className="text-lg font-bold text-white">The 4 Rules of Reciprocal Matching</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-slate-300">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-1">
            <span className="font-bold text-brand-300">1. Private Growth</span>
            <p className="text-slate-400">Match outcomes and skill scores are never shown on public rankings or leaderboards.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-1">
            <span className="font-bold text-emerald-300">2. Mutual Acceptance</span>
            <p className="text-slate-400">Both students must accept the proposal and timeslot before a room is provisioned.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-1">
            <span className="font-bold text-indigo-300">3. Diagnostic Calibration</span>
            <p className="text-slate-400">You must complete a diagnostic quiz in at least one subject to establish your teaching strengths.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-1">
            <span className="font-bold text-amber-300">4. Disconnect Protection</span>
            <p className="text-slate-400">3-minute disconnect grace pauses the session timer automatically to ensure full instructional time.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
