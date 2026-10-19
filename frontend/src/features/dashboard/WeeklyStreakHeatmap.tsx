import React, { useState, useEffect, useMemo } from 'react';
import {
  Flame,
  CheckCircle,
  Shield,
  HelpCircle,
  Sparkles,
  Info,
  Calendar,
  X,
} from 'lucide-react';
import { activityApi, WeeklyStreakData, ActivityDay } from '../../services/activityApi';
import { format, parseISO } from 'date-fns';

export const WeeklyStreakHeatmap: React.FC = () => {
  const [data, setData] = useState<WeeklyStreakData | null>(null);
  const [hoveredDay, setHoveredDay] = useState<{
    day: ActivityDay;
    x: number;
    y: number;
  } | null>(null);
  const [showExplanation, setShowExplanation] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    activityApi
      .getActivityHeatmap()
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch(() => {
        // Fallback demo data if unauthenticated
        if (isMounted) {
          const mockDays: ActivityDay[] = [];
          const now = new Date();
          const start = new Date(now.getTime() - 52 * 7 * 86400000);
          let cur = new Date(start);
          while (cur <= now) {
            const seed = (cur.getDate() * 17 + cur.getMonth() * 31) % 100;
            const isWeekday = cur.getDay() >= 1 && cur.getDay() <= 5;
            let cnt = 0;
            if (isWeekday && seed > 60) cnt = 1 + (seed % 4);
            const level = cnt === 0 ? 0 : cnt === 1 ? 1 : cnt <= 3 ? 2 : cnt <= 5 ? 3 : 4;
            mockDays.push({
              date: cur.toISOString().split('T')[0],
              count: cnt,
              level,
              day_of_week: cur.getDay(),
            });
            cur = new Date(cur.getTime() + 86400000);
          }
          setData({
            total_contributions: 364,
            current_weekly_streak: 8,
            longest_weekly_streak: 14,
            streak_freezes_available: 1,
            weekly_goal_met: true,
            current_week_contributions: 2,
            weekly_goal_target: 1,
            days: mockDays,
          });
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Split days into 52 weekly columns (each column has 7 days, 0=Sun to 6=Sat)
  const columns = useMemo(() => {
    if (!data?.days?.length) return [];
    const cols: ActivityDay[][] = [];
    let curCol: ActivityDay[] = [];

    data.days.forEach((day) => {
      curCol.push(day);
      if (curCol.length === 7) {
        cols.push(curCol);
        curCol = [];
      }
    });
    if (curCol.length > 0) {
      cols.push(curCol);
    }
    return cols;
  }, [data]);

  // Compute month label header markers based on column indices
  const monthLabels = useMemo(() => {
    if (!columns.length) return [];
    const labels: Array<{ text: string; colIndex: number }> = [];
    let lastMonth = -1;

    columns.forEach((col, idx) => {
      if (col[0]) {
        try {
          const d = parseISO(col[0].date);
          const m = d.getMonth();
          if (m !== lastMonth) {
            labels.push({
              text: format(d, 'MMM'),
              colIndex: idx,
            });
            lastMonth = m;
          }
        } catch {
          // ignore date parse
        }
      }
    });
    return labels;
  }, [columns]);

  const getColorClass = (level: number) => {
    switch (level) {
      case 1:
        return 'bg-[#0e4429] border-[#006d32]/40 hover:border-emerald-400';
      case 2:
        return 'bg-[#006d32] border-[#26a641]/40 hover:border-emerald-300';
      case 3:
        return 'bg-[#26a641] border-[#39d353]/50 hover:border-emerald-200';
      case 4:
        return 'bg-[#39d353] border-emerald-300/70 shadow-[0_0_6px_rgba(57,211,83,0.3)] hover:border-white';
      default:
        return 'bg-[#161b22] border-white/5 hover:border-slate-500';
    }
  };

  const streak = data?.current_weekly_streak ?? 1;
  const longest = data?.longest_weekly_streak ?? 1;
  const goalMet = data?.weekly_goal_met ?? true;
  const total = data?.total_contributions ?? 0;

  return (
    <div className="space-y-6">
      {/* 3 Weekly Consistency Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Weekly Streak Card */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Weekly Consistency
            </span>
            <div className="p-2 rounded-xl bg-amber-500/15 text-amber-400 border border-amber-500/30">
              <Flame className="w-4 h-4 fill-amber-400/30 animate-pulse" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white flex items-center gap-2 font-sans">
              <span>{streak} Week Streak</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 font-medium">
                Best: {longest} wks
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              At least 1 completed reciprocal session per week. No high-anxiety daily streaks.
            </p>
          </div>
          <div className="pt-2 flex items-center gap-2 text-xs text-emerald-400 font-medium">
            <CheckCircle className="w-3.5 h-3.5" /> 1 Streak Freeze Available
          </div>
        </div>

        {/* Weekly Goal Card */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              This Week's Goal
            </span>
            <div className="p-2 rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20">
              <Calendar className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white font-sans">
              {goalMet ? 'Goal Completed' : 'In Progress'}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Target: 1 reciprocal teaching session or quiz review between Monday and Sunday.
            </p>
          </div>
          <div className="pt-2 flex items-center gap-2 text-xs">
            {goalMet ? (
              <span className="text-emerald-400 flex items-center gap-1.5 font-medium">
                <CheckCircle className="w-3.5 h-3.5" /> 1/1 Sessions Completed this Week
              </span>
            ) : (
              <span className="text-amber-400 flex items-center gap-1.5 font-medium">
                <Info className="w-3.5 h-3.5" /> 0/1 Completed • Complete by Sunday
              </span>
            )}
          </div>
        </div>

        {/* Streak Freeze & Life-Friendly Protection */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Streak Protection
            </span>
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Shield className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white font-sans flex items-center gap-2">
              <span>❄️ 1 Active Freeze</span>
            </div>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Exams, illness, or travel? A missed week automatically consumes your freeze so your streak stays safe.
            </p>
          </div>
          <div className="pt-2 flex items-center gap-2 text-xs text-cyan-300 font-medium">
            <Sparkles className="w-3.5 h-3.5" /> Refreshes every 4 active weeks
          </div>
        </div>
      </div>

      {/* GitHub-Style Contribution Heat Map Section */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2">
          <h3 className="text-base sm:text-lg font-bold text-white font-sans">
            {total} contributions in the last year
          </h3>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="font-mono text-brand-300 font-semibold">Weekly Streak System</span>
          </div>
        </div>

        {/* The Contribution Heat Map Grid */}
        <div className="p-4 sm:p-5 rounded-2xl border border-white/10 bg-[#0d1117] overflow-x-auto shadow-inner">
          <div className="min-w-[760px] select-none">
            {/* Month Header Row */}
            <div className="flex text-[10px] text-slate-400 mb-2 pl-8 font-mono h-4 relative">
              {monthLabels.map((m, i) => (
                <span
                  key={`${m.text}-${i}`}
                  style={{
                    position: 'absolute',
                    left: `${m.colIndex * 14 + 32}px`,
                  }}
                  className="tracking-wider uppercase"
                >
                  {m.text}
                </span>
              ))}
            </div>

            {/* Grid Area with Day Labels */}
            <div className="flex gap-2">
              {/* Day Labels on Left: Mon, Wed, Fri */}
              <div className="flex flex-col justify-between text-[9px] text-slate-400 font-mono py-1 w-6 shrink-0 h-[104px]">
                <span className="leading-none"></span>
                <span className="leading-none">Mon</span>
                <span className="leading-none"></span>
                <span className="leading-none">Wed</span>
                <span className="leading-none"></span>
                <span className="leading-none">Fri</span>
                <span className="leading-none"></span>
              </div>

              {/* 52 Columns of 7 Squares */}
              <div className="flex gap-[3px] flex-1">
                {columns.map((col, colIdx) => (
                  <div key={colIdx} className="flex flex-col gap-[3px]">
                    {col.map((day) => (
                      <div
                        key={day.date}
                        className={`w-[11px] h-[11px] rounded-[2px] border transition-transform cursor-pointer ${getColorClass(
                          day.level
                        )} hover:scale-125 hover:z-20`}
                        onMouseEnter={(e) => {
                          const rect = e.currentTarget.getBoundingClientRect();
                          setHoveredDay({
                            day,
                            x: rect.left + rect.width / 2,
                            y: rect.top - 8,
                          });
                        }}
                        onMouseLeave={() => setHoveredDay(null)}
                      />
                    ))}
                  </div>
                ))}
              </div>
            </div>

            {/* Bottom Bar: Explainer Link and Legend */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-slate-400 pt-4 mt-2 border-t border-white/5 gap-3">
              <button
                type="button"
                onClick={() => setShowExplanation(true)}
                className="text-brand-400 hover:text-brand-300 text-left transition-colors cursor-pointer flex items-center gap-1.5"
              >
                <HelpCircle className="w-3.5 h-3.5" />
                Learn how we count contributions & weekly streaks
              </button>

              {/* Legend: Less [][][][][] More */}
              <div className="flex items-center gap-2 self-end sm:self-auto font-mono text-[10px]">
                <span>Less</span>
                <div className="flex gap-[3px]">
                  <div className="w-[10px] h-[10px] rounded-[2px] bg-[#161b22] border border-white/5" />
                  <div className="w-[10px] h-[10px] rounded-[2px] bg-[#0e4429] border border-[#006d32]/40" />
                  <div className="w-[10px] h-[10px] rounded-[2px] bg-[#006d32] border border-[#26a641]/40" />
                  <div className="w-[10px] h-[10px] rounded-[2px] bg-[#26a641] border border-[#39d353]/50" />
                  <div className="w-[10px] h-[10px] rounded-[2px] bg-[#39d353] border border-emerald-300/70" />
                </div>
                <span>More</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Floating Hover Tooltip (Matching GitHub's tooltip in screenshot) */}
      {hoveredDay && (
        <div
          className="fixed z-50 pointer-events-none transform -translate-x-1/2 -translate-y-full px-3 py-1.5 rounded-lg bg-slate-900/95 border border-white/20 text-white text-xs font-medium shadow-2xl backdrop-blur-md whitespace-nowrap animate-in fade-in zoom-in-95 duration-100"
          style={{
            left: `${hoveredDay.x}px`,
            top: `${hoveredDay.y}px`,
          }}
        >
          {hoveredDay.day.count === 0 ? (
            <span className="text-slate-400">
              No contributions on {format(parseISO(hoveredDay.day.date), 'MMMM do')}.
            </span>
          ) : (
            <span>
              <strong className="text-emerald-400 font-bold">{hoveredDay.day.count}</strong>{' '}
              {hoveredDay.day.count === 1 ? 'contribution' : 'contributions'} on{' '}
              {format(parseISO(hoveredDay.day.date), 'MMMM do')}.
            </span>
          )}
        </div>
      )}

      {/* How Streaks Are Managed (Weekly Philosophy Modal) */}
      {showExplanation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in">
          <div className="relative w-full max-w-lg p-6 sm:p-8 glass-panel rounded-3xl border border-brand-500/30 shadow-2xl space-y-4">
            <button
              onClick={() => setShowExplanation(false)}
              className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3">
              <div className="p-3 rounded-2xl bg-brand-500/20 text-brand-300 border border-brand-500/30">
                <Flame className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white font-sans">
                  The Weekly Consistency Model
                </h3>
                <p className="text-xs text-slate-400">
                  Building durable peer learning habits without anxiety
                </p>
              </div>
            </div>

            <div className="space-y-3 text-xs text-slate-300 leading-relaxed pt-2">
              <p>
                Most learning platforms use <strong>daily streaks</strong> that punish students for missing a single day due to exams, family, or fatigue.
              </p>
              <div className="p-4 rounded-2xl bg-slate-900/80 border border-white/5 space-y-2">
                <span className="font-bold text-brand-300 text-sm">
                  EduMeet’s 3 Rules for Weekly Streaks:
                </span>
                <ul className="list-disc pl-4 space-y-1.5 text-slate-300">
                  <li>
                    <strong>Evaluated Weekly:</strong> Complete at least 1 reciprocal teaching session, diagnostic assessment, or spaced repetition review between Monday and Sunday.
                  </li>
                  <li>
                    <strong>1 Streak Freeze Always Included:</strong> If you cannot complete a session during an exam or travel week, your Streak Freeze is automatically applied to protect your streak.
                  </li>
                  <li>
                    <strong>Freeze Auto-Refresh:</strong> Completing 4 consecutive active weeks replenishes your Streak Freeze automatically.
                  </li>
                </ul>
              </div>
              <p className="text-slate-400">
                Our mission is deep, reciprocal learning mastery—not artificial daily retention tricks.
              </p>
            </div>

            <div className="pt-2 text-right">
              <button
                onClick={() => setShowExplanation(false)}
                className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-all shadow-md shadow-brand-500/20 cursor-pointer"
              >
                Got It
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
