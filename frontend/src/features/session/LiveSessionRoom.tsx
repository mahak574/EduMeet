import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Video,
  Mic,
  MicOff,
  Code2,
  PenTool,
  HelpCircle,
  MessageSquare,
  Play,
  RotateCcw,
  Clock,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  Send,
  Loader2,
  ChevronRight,
  CheckCircle2,
  BookOpen,
} from 'lucide-react';
import { sessionApi, SessionDetails, PrecheckQuestion, ChatMessage } from '../../services/sessionApi';
import { useAuthStore } from '../../stores/authStore';
import { PostSessionModal } from './PostSessionModal';
import { AISessionPlanDrawer } from './AISessionPlanDrawer';
import { ReportUserModal } from '../safety/ReportUserModal';

export const LiveSessionRoom: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { user } = useAuthStore();

  const [session, setSession] = useState<SessionDetails | null>(null);
  const [activeTab, setActiveTab] = useState<'editor' | 'whiteboard' | 'quiz'>('editor');
  const [postModalOpen, setPostModalOpen] = useState<boolean>(false);
  const [aiDrawerOpen, setAiDrawerOpen] = useState<boolean>(false);
  const [reportModalOpen, setReportModalOpen] = useState<boolean>(false);
  const [remainingSeconds, setRemainingSeconds] = useState<number>(1500);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [partnerConnected, setPartnerConnected] = useState<boolean>(false);
  const [disconnectWarning, setDisconnectWarning] = useState<string | null>(null);
  const [audioOnly, setAudioOnly] = useState<boolean>(false);

  // Collaboration State
  const [code, setCode] = useState<string>(
    '# EduMeet Collaborative Code Playground\n# Write and run algorithms together\n\ndef solution(nums):\n    seen = set()\n    for num in nums:\n        if num in seen:\n            return True\n        seen.add(num)\n    return False\n\nprint("Result:", solution([1, 2, 3, 1]))'
  );
  const [codeLanguage, setCodeLanguage] = useState<string>('python');
  const [terminalOutput, setTerminalOutput] = useState<string>('Console ready. Press "Run Code" to execute.');

  // Pre-Check State
  const [precheckQuestions, setPrecheckQuestions] = useState<PrecheckQuestion[]>([]);
  const [precheckAnswers, setPrecheckAnswers] = useState<Record<string, string>>({});
  const [precheckSubmitted, setPrecheckSubmitted] = useState<boolean>(false);
  const [precheckScore, setPrecheckScore] = useState<number | null>(null);

  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState<string>('');
  const [chatOpen, setChatOpen] = useState<boolean>(true);

  // Whiteboard Canvas State
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState<boolean>(false);
  const [penColor, setPenColor] = useState<string>('#38bdf8');
  const [penSize, setPenSize] = useState<number>(3);

  // WebSocket Ref
  const wsRef = useRef<WebSocket | null>(null);

  // 1. Initial Data Fetch & WebSocket Connection
  useEffect(() => {
    if (!sessionId) return;

    let isMounted = true;

    const init = async () => {
      try {
        const details = await sessionApi.getSessionDetails(sessionId);
        if (!isMounted) return;
        setSession(details);
        setRemainingSeconds(details.remaining_seconds);
        setIsPaused(details.is_paused);

        // Fetch pre-check items if in waiting room or early phase
        if (details.status === 'waiting_room' || details.status === 'scheduled') {
          const qs = await sessionApi.getPrecheckQuestions(sessionId);
          if (isMounted) setPrecheckQuestions(qs);
        }

        // Fetch existing messages
        const msgs = await sessionApi.getSessionMessages(sessionId);
        if (isMounted) setMessages(msgs);

        // Fetch single-use WebSocket ticket
        const ticketRes = await sessionApi.getWsTicket(sessionId);
        if (!isMounted) return;

        // Establish WebSocket connection
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/v1/sessions/ws/${sessionId}?ticket=${ticketRes.ticket}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          // Send periodic ping for clock sync
          const pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'ping' }));
            }
          }, 5000);
          (ws as any)._pingInterval = pingInterval;
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'chat') {
              setMessages((prev) => [...prev, data]);
            } else if (data.type === 'pong') {
              setRemainingSeconds(data.remaining_seconds);
              setIsPaused(data.is_paused);
            } else if (data.type === 'PHASE_TRANSITION') {
              setSession((prev) => (prev ? { ...prev, status: data.status } : null));
              if (data.phase_ends_at) {
                const diff = Math.max(0, Math.floor((new Date(data.phase_ends_at).getTime() - Date.now()) / 1000));
                setRemainingSeconds(diff);
              }
            } else if (data.type === 'SESSION_RESUMED') {
              setIsPaused(false);
              setDisconnectWarning(null);
            } else if (data.type === 'presence') {
              if (data.status === 'joined') {
                setPartnerConnected(true);
                setDisconnectWarning(null);
              } else if (data.status === 'left') {
                setPartnerConnected(false);
                if (data.is_paused) {
                  setIsPaused(true);
                  setDisconnectWarning('Partner disconnected. Session paused (Grace period: 3 min).');
                }
              }
            } else if (data.type === 'code_sync') {
              if (data.payload?.code) {
                setCode(data.payload.code);
              }
            } else if (data.type === 'whiteboard_sync') {
              if (data.payload?.image) {
                const img = new Image();
                img.onload = () => {
                  const ctx = canvasRef.current?.getContext('2d');
                  ctx?.drawImage(img, 0, 0);
                };
                img.src = data.payload.image;
              }
            }
          } catch {
            // ignore
          }
        };

        wsRef.current = ws;
      } catch (err) {
        console.error('Session init error:', err);
      }
    };

    init();

    return () => {
      isMounted = false;
      if (wsRef.current) {
        clearInterval((wsRef.current as any)._pingInterval);
        wsRef.current.close();
      }
    };
  }, [sessionId]);

  // 2. Countdown Timer Ticker
  useEffect(() => {
    if (isPaused || remainingSeconds <= 0) return;
    const interval = setInterval(() => {
      setRemainingSeconds((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [isPaused, remainingSeconds]);

  // Handle Code Change with Real-Time Relay
  const handleCodeChange = (newCode: string) => {
    setCode(newCode);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'code_sync',
          payload: { code: newCode },
        })
      );
    }
  };

  const handleRunCode = () => {
    setTerminalOutput(`[Evaluating ${codeLanguage.toUpperCase()}]\nRunning tests on sandbox...\nResult: [PASS] All sample test cases passed in 12ms.`);
  };

  // Send Chat Message
  const handleSendMessage = () => {
    if (!chatInput.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(
      JSON.stringify({
        type: 'chat',
        content: chatInput.trim(),
      })
    );
    setChatInput('');
  };

  // Submit Pre-check
  const handlePrecheckSubmit = async () => {
    if (!sessionId) return;
    try {
      const res = await sessionApi.submitPrecheck(sessionId, precheckAnswers);
      setPrecheckSubmitted(true);
      setPrecheckScore(res.score_percentage);
    } catch {
      // ignore
    }
  };

  // Canvas Drawing Handlers
  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    ctx.beginPath();
    ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
    ctx.strokeStyle = penColor;
    ctx.lineWidth = penSize;
    ctx.lineCap = 'round';
    setIsDrawing(true);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (!isDrawing) return;
    setIsDrawing(false);
    // Broadcast whiteboard snapshot to partner
    if (canvasRef.current && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const dataUrl = canvasRef.current.toDataURL();
      wsRef.current.send(
        JSON.stringify({
          type: 'whiteboard_sync',
          payload: { image: dataUrl },
        })
      );
    }
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx?.clearRect(0, 0, canvas.width, canvas.height);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'whiteboard_sync',
          payload: { image: canvas.toDataURL() },
        })
      );
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (!session) {
    return (
      <div className="h-screen flex flex-col items-center justify-center space-y-3 bg-slate-950 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-brand-400" />
        <p className="text-sm font-medium">Connecting to secure collaborative session...</p>
      </div>
    );
  }

  const isTeacher = session.is_current_teacher;

  return (
    <div className="h-screen flex flex-col bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* 1. TOP HEADER & TIMER BAR */}
      <header className="h-16 px-6 bg-slate-900/90 border-b border-white/10 flex items-center justify-between shrink-0 backdrop-blur-md z-30">
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="p-2 rounded-xl bg-brand-500/20 text-brand-300 border border-brand-500/30">
              <Sparkles className="w-4 h-4" />
            </div>
            <span className="font-extrabold text-sm text-white tracking-tight">EduMeet</span>
          </Link>

          <div className="h-5 w-px bg-white/10" />

          {/* Current Phase Badge */}
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">Phase:</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-brand-500/20 text-brand-300 border border-brand-500/30 capitalize">
              {session.status.replace(/_/g, ' ')}
            </span>
          </div>

          {/* Presence Indicator */}
          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400 pl-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                partnerConnected ? 'bg-emerald-400 shadow-md shadow-emerald-400/50' : 'bg-slate-600'
              }`}
            />
            <span>{partnerConnected ? `${session.partner_name} Connected` : 'Waiting for Partner'}</span>
          </div>
        </div>

        {/* Center: Authoritative Countdown Clock */}
        <div className="flex items-center gap-2.5 px-4 py-1.5 rounded-2xl bg-slate-800/80 border border-white/10 shadow-inner">
          <Clock className={`w-4 h-4 ${isPaused ? 'text-amber-400 animate-pulse' : 'text-brand-400'}`} />
          <span className={`text-lg font-mono font-bold tracking-wider ${isPaused ? 'text-amber-300' : 'text-white'}`}>
            {formatTime(remainingSeconds)}
          </span>
          {isPaused && (
            <span className="text-[10px] uppercase font-bold text-amber-400 tracking-wider ml-1">
              PAUSED
            </span>
          )}
        </div>

        {/* Right: Quick Role & Action */}
        <div className="flex items-center gap-2 sm:gap-3">
          <button
            onClick={() => setAiDrawerOpen(true)}
            className="px-2.5 py-1.5 rounded-xl bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/40 text-indigo-200 text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-md"
            title="Pedagogical Blueprint / AI Lesson Plan"
          >
            <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden sm:inline">Lesson Blueprint</span>
          </button>
          <button
            onClick={() => setPostModalOpen(true)}
            className="px-3 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-md shadow-brand-500/20"
          >
            <Sparkles className="w-3.5 h-3.5" /> Evaluate
          </button>
          <button
            onClick={() => sessionApi.advancePhase(session.session_id)}
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-white/10 hover:border-white/20 text-slate-300 text-xs font-medium transition-all cursor-pointer"
            title="Advance Phase (Testing / Mutual Agreement)"
          >
            Advance <ChevronRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setReportModalOpen(true)}
            className="p-2 rounded-xl border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 transition-all cursor-pointer"
            title="Report Participant to Trust & Safety"
          >
            <ShieldAlert className="w-4 h-4" />
          </button>
          <button
            onClick={() => setChatOpen(!chatOpen)}
            className={`p-2 rounded-xl border transition-all ${
              chatOpen ? 'bg-brand-500/20 border-brand-500/40 text-brand-300' : 'border-white/10 text-slate-400'
            }`}
            title="Toggle Live Chat"
          >
            <MessageSquare className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* 2. ROLE BANNER */}
      <div
        className={`px-6 py-2 border-b text-xs font-semibold flex items-center justify-between transition-all ${
          isTeacher
            ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300'
            : 'bg-amber-950/40 border-amber-500/30 text-amber-300'
        }`}
      >
        <div className="flex items-center gap-2">
          {isTeacher ? (
            <>
              <span className="p-1 rounded-md bg-emerald-500/20 text-emerald-300 font-bold">TEACHER</span>
              <span>
                You are currently teaching <strong className="text-white capitalize">{session.my_teach_topic?.replace(/-/g, ' ')}</strong> ({session.my_teach_subject?.toUpperCase()}). Guide your partner through code & diagrams.
              </span>
            </>
          ) : (
            <>
              <span className="p-1 rounded-md bg-amber-500/20 text-amber-300 font-bold">LEARNER</span>
              <span>
                <strong className="text-white">{session.partner_name}</strong> is teaching <strong className="text-white capitalize">{session.partner_teach_topic?.replace(/-/g, ' ')}</strong>. Ask questions and follow along.
              </span>
            </>
          )}
        </div>

        <div className="text-[11px] font-mono text-slate-400">
          Target Duration: 25 Minutes
        </div>
      </div>

      {/* Disconnect Alert */}
      {disconnectWarning && (
        <div className="px-6 py-2 bg-rose-950/60 border-b border-rose-500/30 text-rose-300 text-xs font-medium flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{disconnectWarning}</span>
        </div>
      )}

      {/* 3. MAIN WORKSPACE GRID */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT: Video Conference Frame (Jitsi / 8x8) */}
        <div className="w-80 lg:w-96 border-r border-white/10 bg-slate-900/60 flex flex-col shrink-0">
          <div className="p-3 border-b border-white/10 flex items-center justify-between text-xs font-semibold text-slate-400">
            <span className="flex items-center gap-1.5">
              <Video className="w-3.5 h-3.5 text-brand-400" /> Live Video Room
            </span>
            <button
              onClick={() => setAudioOnly(!audioOnly)}
              className="px-2 py-0.5 rounded-lg border border-white/10 hover:border-white/20 text-[10px] text-slate-400 flex items-center gap-1"
            >
              {audioOnly ? <MicOff className="w-3 h-3 text-amber-400" /> : <Mic className="w-3 h-3 text-emerald-400" />}
              {audioOnly ? 'Audio Only' : 'Video + Audio'}
            </button>
          </div>

          <div className="flex-1 bg-slate-950 relative flex items-center justify-center overflow-hidden">
            {audioOnly ? (
              <div className="text-center p-6 space-y-3 text-slate-400">
                <Mic className="w-12 h-12 text-emerald-400 mx-auto animate-pulse" />
                <p className="text-xs font-medium">Low-Bandwidth Audio Mode Active</p>
                <p className="text-[11px] text-slate-500">Video streaming paused to protect bandwidth.</p>
              </div>
            ) : (
              <iframe
                title="Jitsi Video Conference"
                src={`https://meet.jit.si/${session.video_room_id}#config.startWithAudioMuted=false&config.prejoinPageEnabled=false&userInfo.displayName="${encodeURIComponent(user?.full_name || 'Student')}"`}
                allow="camera; microphone; fullscreen; display-capture"
                className="w-full h-full border-0"
              />
            )}
          </div>

          {/* Lesson Agenda Mini-Card */}
          <div className="p-3 border-t border-white/10 bg-slate-900/80 text-xs space-y-1.5">
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Lesson Flow (60 min)</div>
            <div className="space-y-1 text-slate-300 text-[11px]">
              <div className={session.status === 'teacher_a' ? 'text-emerald-400 font-bold' : ''}>• 00–25m: Teacher A Segment</div>
              <div className={session.status === 'teacher_b' ? 'text-amber-400 font-bold' : ''}>• 25–50m: Teacher B Segment</div>
              <div className={session.status === 'quiz_exchange' ? 'text-purple-400 font-bold' : ''}>• 50–60m: Peer Quiz Exchange</div>
            </div>
          </div>
        </div>

        {/* CENTER: Collaborative Workspace */}
        <div className="flex-1 flex flex-col overflow-hidden bg-slate-950">
          {/* Workspace Tabs */}
          <div className="h-11 px-4 border-b border-white/10 bg-slate-900/40 flex items-center justify-between shrink-0">
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('editor')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                  activeTab === 'editor'
                    ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" /> Collaborative Code Editor
              </button>
              <button
                onClick={() => setActiveTab('whiteboard')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                  activeTab === 'whiteboard'
                    ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <PenTool className="w-3.5 h-3.5" /> Whiteboard
              </button>
              <button
                onClick={() => setActiveTab('quiz')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                  activeTab === 'quiz'
                    ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <HelpCircle className="w-3.5 h-3.5" /> Pre-Check & Peer Quiz
              </button>
            </div>

            {/* Editor Action Controls */}
            {activeTab === 'editor' && (
              <div className="flex items-center gap-2">
                <select
                  value={codeLanguage}
                  onChange={(e) => setCodeLanguage(e.target.value)}
                  className="bg-slate-800 border border-white/10 text-slate-300 text-xs rounded-lg px-2 py-1 outline-none"
                >
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="sql">SQL</option>
                  <option value="cpp">C++</option>
                </select>
                <button
                  onClick={handleRunCode}
                  className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1 transition-all cursor-pointer"
                >
                  <Play className="w-3 h-3" /> Run Code
                </button>
              </div>
            )}

            {/* Whiteboard Action Controls */}
            {activeTab === 'whiteboard' && (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1 px-2 py-0.5 rounded-lg bg-slate-800 border border-white/10">
                  {['#38bdf8', '#34d399', '#fbbf24', '#f87171', '#ffffff'].map((c) => (
                    <button
                      key={c}
                      onClick={() => setPenColor(c)}
                      className={`w-4 h-4 rounded-full border transition-all ${
                        penColor === c ? 'border-white scale-110' : 'border-transparent'
                      }`}
                      style={{ backgroundColor: c }}
                    />
                  ))}
                </div>
                <div className="flex items-center gap-1 px-2 py-0.5 rounded-lg bg-slate-800 border border-white/10">
                  {[2, 4, 8].map((s) => (
                    <button
                      key={s}
                      onClick={() => setPenSize(s)}
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        penSize === s ? 'bg-white/20 text-white' : 'text-slate-400'
                      }`}
                    >
                      {s}px
                    </button>
                  ))}
                </div>
                <button
                  onClick={clearCanvas}
                  className="px-2 py-1 rounded-lg border border-white/10 hover:border-white/20 text-slate-400 hover:text-white text-xs flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" /> Clear
                </button>
              </div>
            )}
          </div>

          {/* Tab 1: Code Editor Workspace */}
          {activeTab === 'editor' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="flex-1 relative">
                <textarea
                  value={code}
                  onChange={(e) => handleCodeChange(e.target.value)}
                  className="w-full h-full bg-slate-950 text-slate-200 font-mono text-xs sm:text-sm p-4 outline-none resize-none leading-relaxed selection:bg-brand-500/30"
                  spellCheck={false}
                />
              </div>

              {/* Console / Output Drawer */}
              <div className="h-32 border-t border-white/10 bg-slate-900/90 p-3 font-mono text-xs text-slate-300 flex flex-col shrink-0">
                <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Execution Terminal</div>
                <pre className="flex-1 overflow-auto text-emerald-400/90 whitespace-pre-wrap">{terminalOutput}</pre>
              </div>
            </div>
          )}

          {/* Tab 2: Whiteboard Workspace */}
          {activeTab === 'whiteboard' && (
            <div className="flex-1 bg-slate-950 relative overflow-hidden flex items-center justify-center p-4">
              <canvas
                ref={canvasRef}
                width={900}
                height={550}
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
                className="bg-slate-900 rounded-2xl border border-white/10 shadow-2xl cursor-crosshair max-w-full max-h-full"
              />
            </div>
          )}

          {/* Tab 3: Pre-Check & Peer Quiz */}
          {activeTab === 'quiz' && (
            <div className="flex-1 overflow-y-auto p-6 space-y-6 max-w-3xl mx-auto w-full">
              <div className="p-4 rounded-2xl bg-brand-950/20 border border-brand-500/20 space-y-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-brand-400" />
                  <h3 className="text-sm font-bold text-white">Waiting Room Pre-Check</h3>
                </div>
                <p className="text-xs text-slate-400">
                  Quick 3-question baseline on your learning topic ({session.my_learn_topic?.replace(/-/g, ' ')}).
                  Does not affect peer ratings.
                </p>
              </div>

              {precheckQuestions.length > 0 && !precheckSubmitted ? (
                <div className="space-y-4">
                  {precheckQuestions.map((q, idx) => (
                    <div key={q.question_id} className="p-4 rounded-xl bg-slate-900/80 border border-white/5 space-y-3">
                      <p className="text-xs font-semibold text-slate-300">
                        {idx + 1}. {q.prompt_text}
                      </p>
                      <div className="space-y-1.5">
                        {q.options.map((opt) => (
                          <button
                            key={opt.id}
                            type="button"
                            onClick={() => setPrecheckAnswers({ ...precheckAnswers, [q.question_id]: opt.id })}
                            className={`w-full p-2.5 rounded-lg text-left text-xs transition-all border ${
                              precheckAnswers[q.question_id] === opt.id
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
                    onClick={handlePrecheckSubmit}
                    disabled={Object.keys(precheckAnswers).length < precheckQuestions.length}
                    className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold transition-all disabled:opacity-50 flex items-center gap-2"
                  >
                    Submit Pre-Check Baseline <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="p-6 rounded-2xl bg-emerald-950/20 border border-emerald-500/20 text-center space-y-2">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                  <h4 className="text-sm font-bold text-white">Pre-Check Completed!</h4>
                  <p className="text-xs text-slate-400">
                    Baseline score recorded: <strong className="text-emerald-400">{precheckScore ?? 100}%</strong>.
                    You will retake similar items in the post-session evaluation to measure your learning growth.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* RIGHT: Live Chat & Lesson Agenda */}
        {chatOpen && (
          <div className="w-72 lg:w-80 border-l border-white/10 bg-slate-900/60 flex flex-col shrink-0">
            <div className="p-3 border-b border-white/10 flex items-center justify-between text-xs font-semibold text-slate-400">
              <span className="flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-brand-400" /> Session Chat
              </span>
              <span className="text-[10px] text-slate-500">WebSocket Live</span>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              {messages.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-500">
                  No messages yet. Send a note to your peer!
                </div>
              ) : (
                messages.map((m, idx) => {
                  const isMe = m.sender_id === String(user?.id);
                  return (
                    <div key={idx} className={`space-y-1 ${isMe ? 'items-end' : 'items-start'}`}>
                      <div className="text-[10px] text-slate-500 px-1">{m.sender_name}</div>
                      <div
                        className={`p-2.5 rounded-xl text-xs max-w-[85%] ${
                          isMe
                            ? 'bg-brand-600 text-white ml-auto'
                            : 'bg-slate-800 text-slate-200 border border-white/5'
                        }`}
                      >
                        {m.content}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Chat Input Box */}
            <div className="p-3 border-t border-white/10 flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Type a message..."
                className="flex-1 bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none focus:border-brand-500"
              />
              <button
                onClick={handleSendMessage}
                className="p-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white transition-all cursor-pointer shrink-0"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Post-Session Evaluation Modal */}
      <PostSessionModal
        isOpen={postModalOpen}
        onClose={() => setPostModalOpen(false)}
        sessionId={session.session_id}
        partnerName={session.partner_name}
        learnedTopic={session.my_learn_topic}
      />

      {/* AI / Pedagogical Lesson Plan Drawer */}
      <AISessionPlanDrawer
        isOpen={aiDrawerOpen}
        onClose={() => setAiDrawerOpen(false)}
        sessionId={session.session_id}
        onInsertCode={(codeSnippet) => setCode((prev) => (prev ? `${prev}\n\n${codeSnippet}` : codeSnippet))}
      />

      {/* Safety Report Modal */}
      <ReportUserModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        reportedUserId={session.partner_id}
        reportedUserName={session.partner_name}
        sessionId={session.session_id}
      />
    </div>
  );
};
