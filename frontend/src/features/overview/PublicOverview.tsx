import React from 'react';
import {
  GraduationCap,
  Users2,
  BrainCircuit,
  Clock,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  Lock,
  Scale,
  FileSpreadsheet,
  BookOpen,
  HeartHandshake,
  CheckCircle2,
  Code2,
  Video,
  FileQuestion,
  EyeOff,
  UserCheck,
} from 'lucide-react';

interface PublicOverviewProps {
  onOpenAuth: (mode: 'login' | 'signup') => void;
}

export const PublicOverview: React.FC<PublicOverviewProps> = ({ onOpenAuth }) => {
  return (
    <div className="space-y-16 py-4 animate-in fade-in duration-300">
      {/* 1. HERO SECTION */}
      <section className="relative overflow-hidden p-8 sm:p-14 rounded-3xl glass-panel border border-brand-500/20 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 -mb-12 -ml-12 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-3xl relative z-10 space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-300 text-xs font-semibold">
            <Sparkles className="w-4 h-4" /> Global Reciprocal Peer Teaching
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight font-sans leading-[1.1]">
            Learn What You Lack.
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 via-indigo-300 to-purple-400">
              Master What You Teach.
            </span>
          </h1>

          <p className="text-slate-300 text-base sm:text-lg leading-relaxed max-w-2xl">
            EduMeet is a reciprocal peer-learning platform where students exchange knowledge.
            Teach a topic you know well for 25 minutes, get taught a topic you need help with for 25 minutes,
            and reinforce concepts with a 10-minute mutual quiz.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <button
              onClick={() => onOpenAuth('signup')}
              className="px-7 py-3.5 rounded-2xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm transition-all shadow-xl shadow-brand-500/25 flex items-center gap-2.5 cursor-pointer transform hover:-translate-y-0.5"
            >
              Get Started for Free <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onOpenAuth('login')}
              className="px-6 py-3.5 rounded-2xl bg-slate-900/80 hover:bg-slate-800 text-slate-200 border border-slate-700/80 font-medium text-sm transition-all cursor-pointer"
            >
              Already a Member? Log In
            </button>
          </div>

          <div className="pt-4 flex flex-wrap items-center gap-6 text-xs text-slate-400">
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> 100% Free Peer Exchange
            </span>
            <span className="flex items-center gap-2">
              <EyeOff className="w-4 h-4 text-brand-400" /> No Public Leaderboards
            </span>
            <span className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-400" /> 60-Minute Structured Format
            </span>
          </div>
        </div>
      </section>

      {/* 2. HOW EDUMEET WORKS (3 STEPS) */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-brand-400">Simple 3-Step Flow</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">How EduMeet Works</h2>
          <p className="text-slate-400 text-sm">
            Reciprocal learning ensures equal participation: both students contribute knowledge and both benefit equally.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4 relative">
            <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400 flex items-center justify-center font-bold text-lg">
              1
            </div>
            <h3 className="text-lg font-bold text-white">Select Your Subjects & Needs</h3>
            <p className="text-slate-400 text-xs sm:text-sm leading-relaxed">
              Tell us which subjects you feel confident teaching and which topics you are currently learning.
              Optional diagnostic assessments help calibrate your baseline.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4 relative">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-lg">
              2
            </div>
            <h3 className="text-lg font-bold text-white">Get Paired with a Peer</h3>
            <p className="text-slate-400 text-xs sm:text-sm leading-relaxed">
              Our matching engine pairs you with a student whose teaching strengths match your learning goals,
              and whose learning goals match your teaching strengths.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4 relative">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center font-bold text-lg">
              3
            </div>
            <h3 className="text-lg font-bold text-white">60-Min Reciprocal Session</h3>
            <p className="text-slate-400 text-xs sm:text-sm leading-relaxed">
              Meet in the live session room: 25 minutes teaching, 25 minutes learning, and 10 minutes peer quiz exchange.
              Any misconceptions are automatically logged to your review deck.
            </p>
          </div>
        </div>
      </section>

      {/* 3. KEY FEATURES */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Platform Features</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">Everything You Need for Effective Peer Learning</h2>
          <p className="text-slate-400 text-sm">
            Built from learning-science research on the testing effect, Feynman technique, and spaced repetition.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white">Diagnostic Assessments</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Evaluate real topic understanding through low-stakes adaptive checks. Separate from onboarding, strictly private, and free of public rankings.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center">
              <Users2 className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white">Reciprocal Peer Matching</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Find partners with complementary strengths. Real-time availability matching pairs you with students ready to study right now.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center">
              <Scale className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white">Reciprocal Teaching Balance</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Ensures fair 50:50 time allocation between peers. Both participants gain experience explaining difficult concepts and receiving guidance.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center">
              <FileQuestion className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white">Peer Quiz Exchange</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              The final 10 minutes of every session test retention through interactive questions crafted to cement core formulas and concepts.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white">Mistake Journal & Spaced Repetition</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Questions answered incorrectly are automatically saved to your mistake journal with derivation notes and scheduled for spaced review.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center">
              <BookOpen className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white">Private Progress Tracking</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Track weekly consistency, topic mastery levels, and completed session hours. Everything is completely private to you.
            </p>
          </div>
        </div>
      </section>

      {/* 4. SESSION STRUCTURE (60 MINUTES) */}
      <section className="glass-panel p-8 sm:p-10 rounded-3xl border border-white/10 space-y-8">
        <div className="space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-brand-400">Structured Learning Protocol</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">The 60-Minute Reciprocal Session Format</h2>
          <p className="text-slate-400 text-sm max-w-2xl">
            Unstructured study sessions easily drift off-topic. EduMeet enforces a proven 60-minute rhythm with an integrated phase timer.
          </p>
        </div>

        {/* Visual Progress Bar */}
        <div className="space-y-2">
          <div className="w-full bg-slate-900 rounded-2xl p-1.5 border border-slate-800 flex flex-col sm:flex-row gap-2">
            <div className="flex-1 bg-brand-500/20 border border-brand-500/40 rounded-xl p-4 text-center">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-300">Phase 1 (25 Mins)</span>
              <p className="text-white font-bold text-sm mt-1">You Teach Partner</p>
              <p className="text-slate-400 text-xs mt-1">Explain your strength using whiteboard, code & audio</p>
            </div>
            <div className="flex-1 bg-indigo-500/20 border border-indigo-500/40 rounded-xl p-4 text-center">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-300">Phase 2 (25 Mins)</span>
              <p className="text-white font-bold text-sm mt-1">Partner Teaches You</p>
              <p className="text-slate-400 text-xs mt-1">Ask questions, learn new concepts & solve examples</p>
            </div>
            <div className="w-full sm:w-44 bg-purple-500/20 border border-purple-500/40 rounded-xl p-4 text-center">
              <span className="text-xs font-bold uppercase tracking-wider text-purple-300">Phase 3 (10 Mins)</span>
              <p className="text-white font-bold text-sm mt-1">Quiz Exchange</p>
              <p className="text-slate-400 text-xs mt-1">Reciprocal quiz & review</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 text-xs text-slate-300">
          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-brand-400 flex-shrink-0 mt-0.5" />
            <span>Integrated synchronized phase timer keeps both peers strictly on schedule.</span>
          </div>
          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
            <span>Collaborative whiteboard, code sandbox, and optional video/audio calling.</span>
          </div>
          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
            <span>Automated mistake logging populates your spaced review deck immediately.</span>
          </div>
        </div>
      </section>

      {/* 5. BENEFITS */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">Why Reciprocal Teaching Works</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">Benefits of Learning by Teaching</h2>
          <p className="text-slate-400 text-sm">
            Empirical cognitive science shows active teaching yields 90% retention compared to 10-20% for passive lectures.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center font-bold">
                <HeartHandshake className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white">The Feynman Technique in Practice</h3>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              When you explain a problem to another person in plain language, you immediately identify where your mental model is incomplete. Teaching is the ultimate diagnostic of true understanding.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center font-bold">
                <EyeOff className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white">Psychological Safety Without Competition</h3>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Traditional platforms rely on toxic leaderboards, rankings, and public score comparisons that induce anxiety. EduMeet is strictly collaborative — there are no public ratings or student rankings.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center font-bold">
                <BrainCircuit className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white">Targeted Diagnostic Calibration</h3>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Instead of guessing your level, diagnostic quizzes pin down exactly which topics need attention (e.g. Dynamic Programming vs. Tree Traversals), allowing focused session planning.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center font-bold">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white">Equitable Peer Collaboration</h3>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              High-quality tutoring should not be limited to those who can afford $50/hour private tutors. In EduMeet, your currency is your own knowledge and effort.
            </p>
          </div>
        </div>
      </section>

      {/* 6. EXAMPLE PRODUCT PREVIEW (ILLUSTRATIVE INTERACTIVE MOCKUP) */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-purple-400">Interactive Workspace</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">A Preview of the Live Session Room</h2>
          <p className="text-slate-400 text-sm">
            Purpose-built for peer learning with synchronized whiteboards, code execution, and reciprocal timer.
          </p>
        </div>

        {/* Illustrative Product Mockup Card */}
        <div className="glass-panel rounded-3xl border border-white/15 overflow-hidden shadow-2xl bg-slate-950/80">
          {/* Mockup Header */}
          <div className="px-6 py-4 bg-slate-900/90 border-b border-white/10 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-red-500/80" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
              <span className="text-xs font-semibold text-slate-300 ml-2">
                Live Reciprocal Session: Data Structures (You Teach) ↔ Python Basics (Peer Teaches)
              </span>
            </div>

            <div className="flex items-center gap-3">
              <div className="px-3 py-1 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/40 text-xs font-bold flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" /> 21:40 • Phase 1: You Teach
              </div>
              <span className="text-[11px] uppercase font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Connected
              </span>
            </div>
          </div>

          {/* Mockup Body: Split Workspace */}
          <div className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: Collaborative Code & Whiteboard Pane (7 cols) */}
            <div className="lg:col-span-7 bg-slate-900/90 rounded-2xl border border-slate-800 p-4 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-[11px] text-slate-400">
                <div className="flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-brand-400" />
                  <span className="font-semibold text-slate-300">arrays_and_hashing.py</span>
                </div>
                <span className="text-[10px] text-slate-500">Synchronized Whiteboard & Code</span>
              </div>

              <div className="text-slate-300 space-y-1 leading-relaxed">
                <p className="text-slate-500"># Phase 1 Problem: Two Sum Pattern with Hash Map</p>
                <p><span className="text-purple-400">def</span> <span className="text-blue-400">find_pair</span>(nums: list[int], target: int) -&gt; list[int]:</p>
                <p className="pl-4">seen = {}</p>
                <p className="pl-4"><span className="text-purple-400">for</span> i, num <span className="text-purple-400">in</span> enumerate(nums):</p>
                <p className="pl-8">diff = target - num</p>
                <p className="pl-8"><span className="text-purple-400">if</span> diff <span className="text-purple-400">in</span> seen:</p>
                <p className="pl-12 text-emerald-400">return [seen[diff], i]  # O(1) lookup</p>
                <p className="pl-8">seen[num] = i</p>
                <p className="pl-4"><span className="text-purple-400">return</span> []</p>
              </div>

              <div className="mt-4 p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
                <span>Output Prediction: find_pair([2, 7, 11, 15], 9) -&gt; [0, 1]</span>
                <span className="text-emerald-400 font-semibold">✓ Verified Test Passed</span>
              </div>
            </div>

            {/* Right: Peer Presence & Session Controls (5 cols) */}
            <div className="lg:col-span-5 space-y-4">
              {/* Video/Audio Presence Box */}
              <div className="h-36 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-800 relative flex items-center justify-center text-center p-4">
                <div className="space-y-2">
                  <div className="w-12 h-12 rounded-full bg-brand-500/20 border border-brand-500/40 text-brand-300 flex items-center justify-center mx-auto text-sm font-bold">
                    P
                  </div>
                  <p className="text-xs font-semibold text-slate-200">Peer: Priya S. (Computer Science)</p>
                  <p className="text-[10px] text-slate-400 flex items-center justify-center gap-1.5">
                    <Video className="w-3 h-3 text-emerald-400" /> WebRTC Audio/Video Active
                  </p>
                </div>
              </div>

              {/* Reciprocal Checklist */}
              <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2 text-xs">
                <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Session Agenda</span>
                <div className="space-y-1.5 text-slate-400">
                  <div className="flex items-center gap-2 text-emerald-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Explain hash table collision resolution (Done)</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-200">
                    <div className="w-3.5 h-3.5 rounded-full border border-brand-400 flex items-center justify-center text-[9px] text-brand-400">•</div>
                    <span>Trace Two Sum array indices with partner (Current)</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-500">
                    <div className="w-3.5 h-3.5 rounded-full border border-slate-600" />
                    <span>Switch to Phase 2: Python generators & decorators</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Mockup Notice Footer */}
          <div className="px-6 py-3 bg-slate-900/60 border-t border-white/5 text-center text-[11px] text-slate-400">
            <span className="inline-flex items-center gap-1.5 font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-brand-400" />
              Illustrative Interactive Session Preview • Live session data is strictly private to the two matched participants.
            </span>
          </div>
        </div>
      </section>

      {/* 8. SOP & PROJECT OVERVIEW */}
      <section className="glass-panel p-8 sm:p-10 rounded-3xl border border-white/10 space-y-6">
        <div className="space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-brand-400">Project Overview & SOP</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">Our Educational Mission & Standard Workflow</h2>
          <p className="text-slate-400 text-sm max-w-3xl leading-relaxed">
            EduMeet addresses a fundamental breakdown in technical education: students often spend hundreds of hours passively watching videos, but retain little because they rarely formulate explanations in their own words.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-white uppercase tracking-wider text-slate-300">Target Learners</h4>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Designed for university STEM students, self-taught programmers, bootcamp learners, and engineering candidates seeking structured peer accountability without financial barriers.
            </p>
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-bold text-white uppercase tracking-wider text-slate-300">Standard Operating Procedure (SOP)</h4>
            <ol className="text-xs sm:text-sm text-slate-400 space-y-1.5 list-decimal list-inside leading-relaxed">
              <li><strong className="text-slate-300">Profile Setup:</strong> Define academic subjects and learning goals.</li>
              <li><strong className="text-slate-300">Diagnostic Calibration:</strong> Voluntarily verify topic readiness.</li>
              <li><strong className="text-slate-300">Reciprocal Matching:</strong> Match into a scheduled or live complementary pair.</li>
              <li><strong className="text-slate-300">60-Min Session:</strong> Execute the 25m teach + 25m learn + 10m quiz protocol.</li>
              <li><strong className="text-slate-300">Spaced Review:</strong> Review logged misunderstandings in your mistake journal.</li>
            </ol>
          </div>
        </div>
      </section>

      {/* 9. PRIVACY AND TRUST */}
      <section className="glass-panel p-8 sm:p-10 rounded-3xl border border-white/10 space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Student Privacy & Data Protection</h2>
            <p className="text-xs sm:text-sm text-slate-400">
              Built with privacy-by-design principles to ensure an anxiety-free, secure learning environment.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs text-slate-300">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5">
            <div className="font-semibold text-white flex items-center gap-1.5">
              <UserCheck className="w-4 h-4 text-brand-400" /> Identity Protected
            </div>
            <p className="text-slate-400 leading-relaxed">
              Peers only see your first name and subject interests. Your email and identity details are never shared.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5">
            <div className="font-semibold text-white flex items-center gap-1.5">
              <EyeOff className="w-4 h-4 text-emerald-400" /> No Public Scores
            </div>
            <p className="text-slate-400 leading-relaxed">
              Diagnostic scores and mistake logs are strictly private. We never publish rankings or performance scores.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5">
            <div className="font-semibold text-white flex items-center gap-1.5">
              <Lock className="w-4 h-4 text-indigo-400" /> Mutual AI Consent
            </div>
            <p className="text-slate-400 leading-relaxed">
              AI coaches and lesson plan assistants are strictly optional and require mutual consent from both peers.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5">
            <div className="font-semibold text-white flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-purple-400" /> Full Data Control
            </div>
            <p className="text-slate-400 leading-relaxed">
              Export your full study data or delete your account with one click under GDPR & privacy standards.
            </p>
          </div>
        </div>
      </section>

      {/* 10. FINAL CALL TO ACTION */}
      <section className="text-center p-10 sm:p-14 rounded-3xl glass-panel border border-brand-500/30 bg-gradient-to-b from-brand-950/40 to-slate-950 relative overflow-hidden shadow-2xl">
        <div className="max-w-2xl mx-auto space-y-6 relative z-10">
          <div className="w-12 h-12 rounded-2xl bg-brand-500/20 text-brand-300 border border-brand-500/30 flex items-center justify-center mx-auto shadow-lg shadow-brand-500/20">
            <GraduationCap className="w-6 h-6" />
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold text-white font-sans">
            Ready to Master Technical Topics by Teaching?
          </h2>

          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Join thousands of university and self-taught students accelerating their learning through structured, reciprocal peer teaching.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <button
              onClick={() => onOpenAuth('signup')}
              className="px-8 py-3.5 rounded-2xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm transition-all shadow-xl shadow-brand-500/25 flex items-center gap-2 cursor-pointer transform hover:-translate-y-0.5"
            >
              Create Your Free Account <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onOpenAuth('login')}
              className="px-6 py-3.5 rounded-2xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-700/80 text-sm font-medium transition-all cursor-pointer"
            >
              Sign In to Existing Account
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};
