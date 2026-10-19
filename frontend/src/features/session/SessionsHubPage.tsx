import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Video,
  Sparkles,
  Play,
  Clock,
  CheckCircle2,
  Users,
  Code2,
  ArrowRight,
  Loader2,
  LogIn,
} from 'lucide-react';
import { sessionApi } from '../../services/sessionApi';
import { useAuthStore } from '../../stores/authStore';
import { AuthModal } from '../auth/AuthModal';

export const SessionsHubPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const [sessions, setSessions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isCreatingDemo, setIsCreatingDemo] = useState<boolean>(false);
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchSessions = async () => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    try {
      const data = await sessionApi.getMySessions();
      setSessions(data);
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [isAuthenticated]);

  const handleLaunchDemoSession = async () => {
    if (!isAuthenticated) {
      setAuthModalOpen(true);
      return;
    }
    setIsCreatingDemo(true);
    setErrorMessage(null);
    try {
      const res = await sessionApi.createDemoSession();
      navigate(`/session/${res.session_id}`);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to initialize demo session room.');
    } finally {
      setIsCreatingDemo(false);
    }
  };

  const activeSessions = sessions.filter(
    (s) => s.status !== 'closed' && s.status !== 'cancelled' && s.status !== 'no_show_cancelled'
  );
  const pastSessions = sessions.filter(
    (s) => s.status === 'closed' || s.status === 'cancelled' || s.status === 'no_show_cancelled'
  );

  return (
    <div className="space-y-8 animate-in fade-in max-w-5xl mx-auto pb-12">
      {/* Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-brand-500/20 bg-gradient-to-br from-emerald-950/20 via-slate-900/60 to-slate-950/60 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-300 text-xs font-semibold mb-2">
              <Sparkles className="w-3.5 h-3.5" /> Synchronized 60-Minute Classroom
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Live Collaborative Session Rooms
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-xl leading-relaxed">
              Real-time video/audio with Jitsi Meet, shared Monaco Code Editor powered by Yjs CRDTs, and server-enforced 25/25 role switching.
            </p>
          </div>

          <button
            onClick={handleLaunchDemoSession}
            disabled={isCreatingDemo}
            className="px-6 py-3 rounded-2xl bg-gradient-to-r from-emerald-600 to-brand-600 hover:from-emerald-500 hover:to-brand-500 text-white text-xs font-semibold tracking-wide transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 cursor-pointer shrink-0"
          >
            {isCreatingDemo ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" /> Launch Interactive Test Room
              </>
            )}
          </button>
        </div>

        {errorMessage && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs">
            {errorMessage}
          </div>
        )}
      </div>

      {/* Protocol Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
          <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 w-fit">
            <Clock className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-white text-sm">Server-Enforced 25/25 Timer</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            25 min Teacher A instructs → 25 min Teacher B instructs → 10 min reciprocal peer quiz exchange.
          </p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
          <div className="p-2 rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20 w-fit">
            <Code2 className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-white text-sm">Monaco + Yjs Collaboration</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Multi-cursor synchronized code editor with dynamic language syntax highlighting and real-time execution.
          </p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
          <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 w-fit">
            <Video className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-white text-sm">Jitsi Video & Audio Stream</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Secure WebRTC media streaming with optional camera controls, screen sharing, and audio-only low bandwidth modes.
          </p>
        </div>
      </div>

      {/* Active / Scheduled Sessions */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-brand-400" />
            Your Live Sessions ({activeSessions.length})
          </h2>
          {!isAuthenticated && (
            <button
              onClick={() => setAuthModalOpen(true)}
              className="px-3 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
            >
              <LogIn className="w-3.5 h-3.5" /> Log In
            </button>
          )}
        </div>

        {isLoading ? (
          <div className="py-12 flex justify-center text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
          </div>
        ) : activeSessions.length === 0 ? (
          <div className="py-12 text-center text-slate-400 space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-slate-800/60 border border-white/5 flex items-center justify-center mx-auto text-slate-500">
              <Video className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium text-slate-300">No active or scheduled sessions right now.</p>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Join the Peer Matching Pool to be matched, or click "Launch Interactive Test Room" above to test the Live Classroom environment instantly!
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {activeSessions.map((session) => (
              <div
                key={session.session_id}
                className="p-5 rounded-2xl bg-slate-900/80 border border-white/10 hover:border-brand-500/30 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-bold text-white">Partner: {session.partner_name}</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-brand-500/10 text-brand-300 border border-brand-500/20">
                      {session.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Teaching: <strong className="text-slate-200 capitalize">{session.my_teach_topic.replace(/-/g, ' ')}</strong> ({session.my_teach_subject.toUpperCase()})
                    {' • '}
                    Learning: <strong className="text-slate-200 capitalize">{session.my_learn_topic.replace(/-/g, ' ')}</strong>
                  </p>
                </div>

                <button
                  onClick={() => navigate(`/session/${session.session_id}`)}
                  className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer shadow-md shadow-brand-500/20"
                >
                  <Video className="w-4 h-4" /> Enter Live Room <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Past Completed Sessions */}
      {pastSessions.length > 0 && (
        <div className="glass-panel p-6 rounded-3xl border border-white/10 space-y-4">
          <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
            Completed Sessions Archive
          </h3>
          <div className="space-y-2">
            {pastSessions.map((s) => (
              <div
                key={s.session_id}
                className="p-3.5 rounded-xl bg-slate-900/40 border border-white/5 flex items-center justify-between text-xs text-slate-400"
              >
                <span>Partner: <strong className="text-slate-300">{s.partner_name}</strong></span>
                <span className="capitalize">{s.my_teach_topic.replace(/-/g, ' ')} / {s.my_learn_topic.replace(/-/g, ' ')}</span>
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Completed
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
      />
    </div>
  );
};
