import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Award,
  CheckCircle,
  Clock,
  Globe,
  HelpCircle,
  Lock,
  Shield,
  ShieldCheck,
  Sparkles,
  Star,
  Users,
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { APIResponse } from '../../types';

interface BadgeResponse {
  badge_key: string;
  title: string;
  description: string;
  icon_name: string;
  awarded_at: string;
}

interface PublicPortfolio {
  full_name: string;
  country: string;
  timezone: string;
  portfolio_slug?: string;
  is_public: boolean;
  is_verified_student: boolean;
  is_mentor: boolean;
  completed_sessions_count: number;
  distinct_partners_count: number;
  partner_diversity_unlocked: boolean;
  teaching_subjects: string[];
  badges: BadgeResponse[];
  average_clarity_rating?: number;
  average_helpfulness_rating?: number;
  notice?: string;
}

const BADGE_ICONS: Record<string, React.ReactNode> = {
  Sparkles: <Sparkles className="w-5 h-5 text-amber-400" />,
  Users: <Users className="w-5 h-5 text-brand-400" />,
  Star: <Star className="w-5 h-5 text-emerald-400" />,
  HelpCircle: <HelpCircle className="w-5 h-5 text-sky-400" />,
  ShieldCheck: <ShieldCheck className="w-5 h-5 text-purple-400" />,
};

export const PublicPortfolioView: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const [portfolio, setPortfolio] = useState<PublicPortfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (slug) {
      loadPortfolio();
    }
  }, [slug]);

  const loadPortfolio = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient<APIResponse<PublicPortfolio>>(`/users/portfolio/${slug}`);
      if (res?.success && res.data) {
        setPortfolio(res.data);
      }
    } catch (err: any) {
      setError(err.message || 'This teaching portfolio could not be found or is private.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center space-y-3 text-slate-400">
        <Sparkles className="w-8 h-8 text-brand-400 animate-spin" />
        <p className="text-sm font-medium">Loading verified teaching portfolio...</p>
      </div>
    );
  }

  if (error || !portfolio) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
        <div className="max-w-md w-full p-8 rounded-3xl bg-slate-900 border border-white/10 text-center space-y-4 shadow-2xl">
          <div className="w-16 h-16 mx-auto rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 flex items-center justify-center">
            <Lock className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-white">Portfolio Unavailable</h2>
          <p className="text-sm text-slate-400 leading-relaxed">{error}</p>
          <div className="pt-2">
            <Link
              to="/"
              className="inline-block px-5 py-2.5 rounded-2xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition-all shadow-lg shadow-brand-600/30"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans pb-16">
      {/* Top Navbar */}
      <nav className="h-16 px-6 border-b border-white/10 bg-slate-900/60 backdrop-blur-md flex items-center justify-between sticky top-0 z-40">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-brand-500/20 text-brand-300 border border-brand-500/30">
            <Sparkles className="w-4 h-4" />
          </div>
          <span className="font-extrabold text-sm text-white tracking-tight">EduMeet</span>
        </Link>
        <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-brand-400" />
          Academic Peer Portfolio
        </span>
      </nav>

      {/* Main Container */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 pt-10 space-y-8 animate-fade-in">
        {/* Header Profile Card */}
        <section className="p-6 sm:p-8 rounded-3xl bg-gradient-to-b from-slate-900/90 to-slate-900/50 border border-white/10 backdrop-blur-xl shadow-2xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="flex items-center gap-5">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white text-2xl font-black shadow-xl shadow-brand-600/30 border border-white/20">
                {portfolio.full_name.charAt(0)}
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h1 className="text-2xl font-black text-white tracking-tight">{portfolio.full_name}</h1>
                  {portfolio.is_verified_student && (
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30 flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" /> Verified Student
                    </span>
                  )}
                  {portfolio.is_mentor && (
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                      <Star className="w-3 h-3" /> Peer Mentor
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-400 mt-2">
                  <span className="flex items-center gap-1">
                    <Globe className="w-3.5 h-3.5" /> {portfolio.country.toUpperCase()}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> {portfolio.timezone}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Stat Pills */}
            <div className="flex items-center gap-3">
              <div className="p-4 rounded-2xl bg-slate-800/80 border border-white/5 text-center min-w-24">
                <span className="text-xl font-black text-brand-300 block">{portfolio.completed_sessions_count}</span>
                <span className="text-[10px] uppercase font-bold text-slate-400">Sessions</span>
              </div>
              <div className="p-4 rounded-2xl bg-slate-800/80 border border-white/5 text-center min-w-24">
                <span className="text-xl font-black text-indigo-300 block">{portfolio.distinct_partners_count}</span>
                <span className="text-[10px] uppercase font-bold text-slate-400">Partners</span>
              </div>
            </div>
          </div>

          {/* Teaching Disciplines */}
          <div className="pt-4 border-t border-white/5">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
              Teaching Subjects
            </span>
            <div className="flex flex-wrap gap-2">
              {portfolio.teaching_subjects.map((sub, i) => (
                <span
                  key={i}
                  className="px-3 py-1 rounded-xl bg-slate-800/90 text-slate-200 border border-white/10 text-xs font-bold uppercase tracking-wider"
                >
                  {sub}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* 5-Distinct-Partner Protection & Ratings Card */}
        <section className="p-6 sm:p-8 rounded-3xl bg-slate-900/60 border border-white/10 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <h2 className="text-base font-bold text-white">Verified Peer Teaching Ratings</h2>
            </div>
            {portfolio.partner_diversity_unlocked ? (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Verified ({portfolio.distinct_partners_count}/5 partners)
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                <Lock className="w-3 h-3" /> Unlocks at 5 Partners
              </span>
            )}
          </div>

          {!portfolio.partner_diversity_unlocked ? (
            <div className="p-6 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-center space-y-2">
              <Lock className="w-8 h-8 text-amber-400 mx-auto" />
              <h3 className="text-sm font-bold text-amber-200">Ratings Protected to Prevent Reciprocal Bias</h3>
              <p className="text-xs text-amber-300/80 max-w-lg mx-auto leading-relaxed">
                {portfolio.notice ||
                  `Peer ratings are revealed once the student completes sessions with at least 5 distinct partners (${portfolio.distinct_partners_count}/5 completed so far).`}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="p-5 rounded-2xl bg-slate-800/60 border border-white/5 space-y-1">
                <span className="text-xs text-slate-400 uppercase font-bold tracking-wider">Average Clarity</span>
                <div className="flex items-center gap-2">
                  <Star className="w-5 h-5 text-amber-400 fill-amber-400" />
                  <span className="text-2xl font-black text-white">{portfolio.average_clarity_rating}</span>
                  <span className="text-xs text-slate-400 font-medium">/ 5.0</span>
                </div>
                <p className="text-[11px] text-slate-400">Rated on clarity of explanation and mental models.</p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-800/60 border border-white/5 space-y-1">
                <span className="text-xs text-slate-400 uppercase font-bold tracking-wider">Average Helpfulness</span>
                <div className="flex items-center gap-2">
                  <Star className="w-5 h-5 text-emerald-400 fill-emerald-400" />
                  <span className="text-2xl font-black text-white">{portfolio.average_helpfulness_rating}</span>
                  <span className="text-xs text-slate-400 font-medium">/ 5.0</span>
                </div>
                <p className="text-[11px] text-slate-400">Rated on patience, responsiveness, and problem solving.</p>
              </div>
            </div>
          )}
        </section>

        {/* Milestone Badges Showcase */}
        <section className="p-6 sm:p-8 rounded-3xl bg-slate-900/60 border border-white/10 backdrop-blur-xl space-y-6">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-500/20 text-purple-300 border border-purple-500/30">
              <Award className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Academic Milestone Badges</h2>
              <p className="text-xs text-slate-400">Recognized achievements earned through reciprocal collaboration.</p>
            </div>
          </div>

          {portfolio.badges.length === 0 ? (
            <p className="text-xs text-slate-400 italic">No milestone badges unlocked yet.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {portfolio.badges.map((b, i) => (
                <div
                  key={i}
                  className="p-4 rounded-2xl bg-slate-800/60 border border-white/5 flex items-start gap-3.5 hover:border-brand-500/30 transition-all"
                >
                  <div className="p-2.5 rounded-xl bg-slate-900 border border-white/10 shrink-0">
                    {BADGE_ICONS[b.icon_name] || <Award className="w-5 h-5 text-brand-400" />}
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-white">{b.title}</h3>
                    <p className="text-xs text-slate-300 leading-relaxed">{b.description}</p>
                    <span className="text-[10px] text-slate-400 font-mono block">
                      Unlocked on {new Date(b.awarded_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
};
