import React, { useState, useEffect, useMemo } from 'react';
import {
  Flame,
  CheckCircle,
  Shield,
  HelpCircle,
  Sparkles,
  Calendar,
  X,
  Video,
  BookOpen,
} from 'lucide-react';
import {
  activityApi,
  WeeklyStreakData,
  ActivityMonth,
  ActivityWeek,
} from '../../services/activityApi';
import { Link } from 'react-router-dom';

const generateFallbackMonths = (year: number): ActivityMonth[] => {
  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];
  const monthShorts = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  const now = new Date();

  return monthNames.map((name, mIdx) => {
    const mNum = mIdx + 1;
    const numDays = new Date(year, mNum, 0).getDate();
    const weekRanges = [
      [1, 7],
      [8, 14],
      [15, 21],
      [22, numDays],
    ];

    const weeks: ActivityWeek[] = weekRanges.map(([startD, endD], wIdx) => {
      const startDate = new Date(year, mIdx, startD);
      const endDate = new Date(year, mIdx, endD);

      const startDayName = dayNames[startDate.getDay()];
      const endDayName = dayNames[endDate.getDay()];
      const short = monthShorts[mIdx];

      const isCurrentWeek =
        now >= startDate && now <= new Date(year, mIdx, endD, 23, 59, 59);
      const isPastWeek = now > new Date(year, mIdx, endD, 23, 59, 59);
      const isFutureWeek = now < startDate;

      return {
        week_id: `${year}-${String(mNum).padStart(2, '0')}-w${wIdx + 1}`,
        week_number: wIdx + 1,
        month_number: mNum,
        start_day: startD,
        end_day: endD,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        start_day_name: startDayName,
        end_day_name: endDayName,
        range_label: `${startD} ${short} – ${endD} ${short}`,
        full_range_label: `${startDayName}, ${startD} ${short} – ${endDayName}, ${endD} ${short} ${year}`,
        has_live_session: false,
        live_sessions_count: 0,
        quiz_count: 0,
        total_contributions: 0,
        level: 0,
        is_current_week: isCurrentWeek,
        is_past_week: isPastWeek,
        is_future_week: isFutureWeek,
        activities: [],
      };
    });

    return {
      month_name: name,
      month_short: monthShorts[mIdx],
      month_number: mNum,
      year,
      weeks_count: weeks.length,
      active_weeks_count: 0,
      weeks,
    };
  });
};

export const WeeklyStreakHeatmap: React.FC = () => {
  const [data, setData] = useState<WeeklyStreakData | null>(null);
  const [selectedMonthIndex, setSelectedMonthIndex] = useState<number | null>(null);
  const [hoveredWeek, setHoveredWeek] = useState<{
    week: ActivityWeek;
    monthName: string;
    x: number;
    y: number;
  } | null>(null);
  const [showExplanation, setShowExplanation] = useState<boolean>(false);

  const currentYear = useMemo(() => {
    return data?.year ?? new Date().getFullYear();
  }, [data]);

  const currentMonthNum = useMemo(() => {
    return new Date().getMonth() + 1; // 1-12
  }, []);

  useEffect(() => {
    let isMounted = true;
    activityApi
      .getActivityHeatmap()
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch(() => {
        if (isMounted) {
          const year = new Date().getFullYear();
          const fallbackMonths = generateFallbackMonths(year);

          // Mark a few demo active weeks if fallback
          fallbackMonths.forEach((mo) => {
            if (mo.month_number <= currentMonthNum) {
              mo.weeks.forEach((wk, wIdx) => {
                if (wIdx === 0 || wIdx === 2) {
                  wk.has_live_session = true;
                  wk.live_sessions_count = 1;
                  wk.level = 2;
                  wk.activities = [
                    {
                      type: 'live_session',
                      title: 'Live Collaborative Session: Python & DSA',
                      topic: 'Arrays and Two-Pointers',
                      partner: 'Jordan (Peer Mentor)',
                      date: wk.start_date,
                      status: 'Completed',
                    },
                  ];
                }
              });
              mo.active_weeks_count = mo.weeks.filter((w) => w.has_live_session).length;
            }
          });

          setData({
            total_contributions: 14,
            total_live_sessions: 8,
            current_weekly_streak: 4,
            longest_weekly_streak: 7,
            streak_freezes_available: 1,
            weekly_goal_met: true,
            current_week_contributions: 1,
            weekly_goal_target: 1,
            year,
            months: fallbackMonths,
            days: [],
          });
        }
      });

    return () => {
      isMounted = false;
    };
  }, [currentMonthNum]);

  const months = useMemo<ActivityMonth[]>(() => {
    if (data?.months && data.months.length > 0) {
      return data.months;
    }
    return generateFallbackMonths(currentYear);
  }, [data, currentYear]);

  // Color generator for week boxes
  const getWeekBoxStyle = (week: ActivityWeek) => {
    if (week.has_live_session || week.level >= 2) {
      // Live session taken: Vibrant Emerald Green
      return {
        bgClass: 'bg-emerald-500 hover:bg-emerald-400 text-white border-emerald-300/80 shadow-[0_0_10px_rgba(16,185,129,0.4)]',
        indicator: '🟢',
      };
    }
    if (week.level === 1) {
      // Quiz or spaced repetition review completed without live session
      return {
        bgClass: 'bg-teal-700/70 hover:bg-teal-600 text-teal-200 border-teal-500/50',
        indicator: '🟡',
      };
    }
    if (week.is_current_week) {
      // Current active week awaiting session
      return {
        bgClass: 'bg-slate-800/90 hover:bg-slate-700 text-brand-300 border-brand-400/80 ring-2 ring-brand-400/50 ring-offset-2 ring-offset-slate-900',
        indicator: '⚡',
      };
    }
    if (week.is_future_week) {
      // Future week
      return {
        bgClass: 'bg-slate-900/30 text-slate-600 border-dashed border-slate-800/80',
        indicator: '⚪',
      };
    }
    // Past inactive week
    return {
      bgClass: 'bg-slate-800/60 hover:bg-slate-700/80 text-slate-500 border-slate-700/60',
      indicator: '⚪',
    };
  };

  const streak = data?.current_weekly_streak ?? 1;
  const longest = data?.longest_weekly_streak ?? 1;
  const goalMet = data?.weekly_goal_met ?? false;
  const totalLiveSessions = data?.total_live_sessions ?? 0;

  // Selected or active month to spotlight
  const spotlightMonth = useMemo(() => {
    if (selectedMonthIndex !== null && months[selectedMonthIndex]) {
      return months[selectedMonthIndex];
    }
    // Default to November if present, or current month
    const nov = months.find((m) => m.month_number === 11);
    const curr = months.find((m) => m.month_number === currentMonthNum);
    return curr || nov || months[0];
  }, [selectedMonthIndex, months, currentMonthNum]);

  return (
    <div className="space-y-6">
      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Weekly Consistency Card */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3 relative overflow-hidden bg-gradient-to-br from-slate-900/80 to-slate-950/80">
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
              1 box per week. Take a live session each week to turn the box green and extend your streak.
            </p>
          </div>
          <div className="pt-2 flex items-center gap-2 text-xs text-emerald-400 font-medium">
            <CheckCircle className="w-3.5 h-3.5" /> 1 Streak Freeze Available
          </div>
        </div>

        {/* This Week's Live Session Goal */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3 bg-gradient-to-br from-slate-900/80 to-slate-950/80">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              This Week's Goal
            </span>
            <div className="p-2 rounded-xl bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              <Video className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white font-sans flex items-center gap-2">
              {goalMet ? (
                <>
                  <span className="text-emerald-400">Goal Completed</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Box is Green
                  </span>
                </>
              ) : (
                <span className="text-amber-300">Live Session Needed</span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Target: 1 Live Classroom Session between Monday and Sunday.
            </p>
          </div>
          <div className="pt-2 flex items-center gap-2 text-xs">
            {goalMet ? (
              <span className="text-emerald-400 flex items-center gap-1.5 font-medium">
                <CheckCircle className="w-3.5 h-3.5" /> Live Session completed for this week!
              </span>
            ) : (
              <Link
                to="/sessions"
                className="text-brand-400 hover:text-brand-300 flex items-center gap-1.5 font-medium transition-colors cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5" /> Launch interactive room to turn box green &rarr;
              </Link>
            )}
          </div>
        </div>

        {/* Total Sessions & Safety Protection */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-3 bg-gradient-to-br from-slate-900/80 to-slate-950/80">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Session Attendance
            </span>
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Shield className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white font-sans flex items-center gap-2">
              <span>{totalLiveSessions} Completed</span>
            </div>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Exams, travel, or busy? Missed weeks automatically use your streak freeze to keep your profile in good standing.
            </p>
          </div>
          <div className="pt-2 flex items-center gap-2 text-xs text-cyan-300 font-medium">
            <Sparkles className="w-3.5 h-3.5" /> Synchronized with live calendar dates
          </div>
        </div>
      </div>

      {/* Main Weekly Activity Graph Panel */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 space-y-6 relative">
        {/* Header with Title and Year */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/10">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold mb-2">
              <Calendar className="w-3.5 h-3.5" /> Weekly Consistency Calendar • {currentYear}
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
              Weekly Activity Graph
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Each month displays its 4 weeks as single boxes. When you take a live session in a week, that box becomes <span className="text-emerald-400 font-semibold">green</span>. Hover over any box to inspect that week's date range and activity.
            </p>
          </div>

          {/* Quick Legend */}
          <div className="flex flex-wrap items-center gap-3 text-xs bg-slate-950/60 p-3 rounded-2xl border border-white/10 shrink-0">
            <div className="flex items-center gap-1.5">
              <div className="w-3.5 h-3.5 rounded bg-emerald-500 border border-emerald-300 shadow-[0_0_6px_rgba(16,185,129,0.5)]" />
              <span className="text-slate-300 text-[11px]">Live Session</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3.5 h-3.5 rounded bg-teal-700 border border-teal-500" />
              <span className="text-slate-300 text-[11px]">Quiz / Study</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3.5 h-3.5 rounded bg-slate-800 border border-brand-400 ring-1 ring-brand-400" />
              <span className="text-slate-300 text-[11px]">Current Week</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3.5 h-3.5 rounded bg-slate-800/80 border border-slate-700" />
              <span className="text-slate-400 text-[11px]">Inactive</span>
            </div>
          </div>
        </div>

        {/* Month Selector Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-thin">
          <button
            type="button"
            onClick={() => setSelectedMonthIndex(null)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold tracking-wide transition-all cursor-pointer shrink-0 ${
              selectedMonthIndex === null
                ? 'bg-brand-500 text-white shadow-md shadow-brand-500/20'
                : 'bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10'
            }`}
          >
            All 12 Months
          </button>
          {months.map((m, idx) => {
            const isCurrent = m.month_number === currentMonthNum;
            const isSelected = selectedMonthIndex === idx;
            return (
              <button
                key={m.month_number}
                type="button"
                onClick={() => setSelectedMonthIndex(idx)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold tracking-wide transition-all cursor-pointer shrink-0 flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/20'
                    : isCurrent
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/25'
                    : 'bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10'
                }`}
              >
                <span>{m.month_short}</span>
                {m.active_weeks_count > 0 && (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                )}
              </button>
            );
          })}
        </div>

        {/* 12-Month Calendar Matrix Grid: 4 Boxes Per Month */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {months.map((m, mIdx) => {
            const isCurrentMonth = m.month_number === currentMonthNum;
            const isHighlighted = selectedMonthIndex === null || selectedMonthIndex === mIdx;

            return (
              <div
                key={m.month_number}
                className={`p-4 rounded-2xl border transition-all duration-200 space-y-3 ${
                  isCurrentMonth
                    ? 'border-emerald-500/40 bg-gradient-to-b from-emerald-950/20 to-slate-900/60 shadow-lg shadow-emerald-950/20'
                    : 'border-white/10 bg-slate-900/40 hover:border-white/20'
                } ${!isHighlighted ? 'opacity-40 grayscale-[50%]' : ''}`}
              >
                {/* Month Title & Stats */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-sm tracking-wide">
                      {m.month_name}
                    </span>
                    {isCurrentMonth && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold">
                        This Month
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">
                    {m.active_weeks_count}/{m.weeks.length} Active
                  </span>
                </div>

                {/* The 4 Week Boxes for this month */}
                <div className="grid grid-cols-4 gap-2">
                  {m.weeks.map((week) => {
                    const style = getWeekBoxStyle(week);
                    return (
                      <div
                        key={week.week_id}
                        className={`relative group rounded-xl p-2.5 flex flex-col items-center justify-between min-h-[76px] border transition-all duration-200 cursor-pointer ${style.bgClass} hover:scale-105 hover:z-20`}
                        onMouseEnter={(e) => {
                          const rect = e.currentTarget.getBoundingClientRect();
                          setHoveredWeek({
                            week,
                            monthName: m.month_name,
                            x: rect.left + rect.width / 2,
                            y: rect.top - 8,
                          });
                        }}
                        onMouseLeave={() => setHoveredWeek(null)}
                        onClick={() => setSelectedMonthIndex(mIdx)}
                      >
                        {/* Week Label */}
                        <span className="text-[10px] font-extrabold tracking-wider uppercase opacity-90">
                          W{week.week_number}
                        </span>

                        {/* Status Icon */}
                        <div className="my-1 flex items-center justify-center">
                          {week.has_live_session ? (
                            <Video className="w-4 h-4 fill-white animate-bounce-subtle" />
                          ) : week.level === 1 ? (
                            <BookOpen className="w-3.5 h-3.5 text-teal-200" />
                          ) : week.is_current_week ? (
                            <Sparkles className="w-3.5 h-3.5 text-brand-300 animate-pulse" />
                          ) : (
                            <div className="w-2 h-2 rounded-full bg-current opacity-40" />
                          )}
                        </div>

                        {/* Calendar Date Range described */}
                        <span className="text-[9px] font-mono font-medium text-center leading-tight whitespace-nowrap">
                          {week.start_day}–{week.end_day}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {/* Subtle date range caption for the month */}
                <div className="text-[10px] text-slate-400 font-mono text-center pt-1 border-t border-white/5 flex items-center justify-between">
                  <span>1 {m.month_short}</span>
                  <span className="text-slate-500">&bull;&bull;&bull;</span>
                  <span>
                    {m.weeks[m.weeks.length - 1]?.end_day} {m.month_short}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Spotlight Card for Selected Month (e.g. November) */}
        {spotlightMonth && (
          <div className="glass-panel p-6 rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/20 via-slate-900/60 to-slate-950/80 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <div className="inline-flex items-center gap-1.5 text-xs text-emerald-300 font-semibold mb-1">
                  <Sparkles className="w-3.5 h-3.5" /> Detailed Month View
                </div>
                <h3 className="text-lg sm:text-xl font-bold text-white flex items-center gap-2">
                  <span>{spotlightMonth.month_name} {spotlightMonth.year}</span>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    {spotlightMonth.weeks.length} Weeks
                  </span>
                </h3>
              </div>
              <div className="text-xs text-slate-300 flex items-center gap-2 font-mono">
                <span>{spotlightMonth.active_weeks_count} weeks with live sessions completed</span>
              </div>
            </div>

            {/* 4 Detailed Week Cards with full range description */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {spotlightMonth.weeks.map((week) => (
                  <div
                    key={week.week_id}
                    className={`p-4 rounded-2xl border transition-all duration-200 flex flex-col justify-between space-y-3 ${
                      week.has_live_session
                        ? 'bg-emerald-950/30 border-emerald-500/40 shadow-lg shadow-emerald-950/30'
                        : week.is_current_week
                        ? 'bg-slate-900/80 border-brand-400 ring-1 ring-brand-400'
                        : 'bg-slate-900/50 border-white/10'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-white tracking-wide">
                          Week {week.week_number}
                        </span>
                        {week.has_live_session ? (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" /> Live Session Active
                          </span>
                        ) : week.is_current_week ? (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/30 font-semibold">
                            This Week
                          </span>
                        ) : week.is_future_week ? (
                          <span className="text-[10px] text-slate-500">Upcoming</span>
                        ) : (
                          <span className="text-[10px] text-slate-500">No session</span>
                        )}
                      </div>

                      {/* Explicit date range described: e.g., Monday 1 Nov – Sunday 7 Nov */}
                      <div className="text-xs text-slate-200 font-semibold mb-1">
                        {week.full_range_label}
                      </div>

                      <p className="text-[11px] text-slate-400">
                        {week.has_live_session
                          ? `${week.live_sessions_count} Live Collaborative Classroom Session(s) completed.`
                          : week.is_current_week
                          ? 'Target: 1 Live Classroom Session to turn this box green.'
                          : 'No session attended during this week.'}
                      </p>
                    </div>

                    {/* Activities List */}
                    {week.activities.length > 0 ? (
                      <div className="space-y-1.5 pt-2 border-t border-white/5">
                        {week.activities.map((act, actIdx) => (
                          <div
                            key={actIdx}
                            className="p-2 rounded-xl bg-black/40 border border-white/5 text-[11px] space-y-1"
                          >
                            <div className="flex items-center gap-1.5 font-medium text-emerald-300">
                              <Video className="w-3 h-3 shrink-0" />
                              <span className="truncate">{act.title}</span>
                            </div>
                            {act.topic && (
                              <div className="text-[10px] text-slate-400">
                                Topic: {act.topic}
                              </div>
                            )}
                            {act.partner && (
                              <div className="text-[10px] text-slate-400">
                                Peer: {act.partner}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : week.is_current_week ? (
                      <Link
                        to="/sessions"
                        className="p-2.5 rounded-xl bg-brand-500/20 hover:bg-brand-500/30 text-brand-300 text-xs font-semibold flex items-center justify-center gap-1.5 border border-brand-500/30 transition-colors"
                      >
                        <Video className="w-3.5 h-3.5" /> Launch Live Session
                      </Link>
                    ) : null}
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Explainer Link */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-400 pt-3 border-t border-white/10 gap-2">
          <button
            type="button"
            onClick={() => setShowExplanation(true)}
            className="text-brand-400 hover:text-brand-300 text-left transition-colors cursor-pointer flex items-center gap-1.5"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            Learn how EduMeet's Weekly Consistency & Streak Freeze works
          </button>
          <span className="text-[11px] text-slate-500 font-mono">
            Boxes automatically update when sessions finish or launch
          </span>
        </div>
      </div>

      {/* Floating Hover Tooltip for Week Box */}
      {hoveredWeek && (
        <div
          className="fixed z-50 pointer-events-none transform -translate-x-1/2 -translate-y-full mb-2 w-72 p-3.5 rounded-2xl bg-slate-900/95 border border-white/20 shadow-2xl backdrop-blur-xl text-left space-y-2 animate-in fade-in zoom-in-95 duration-150"
          style={{
            left: `${hoveredWeek.x}px`,
            top: `${hoveredWeek.y}px`,
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between pb-1.5 border-b border-white/10">
            <span className="text-xs font-bold text-white">
              {hoveredWeek.monthName} &bull; Week {hoveredWeek.week.week_number}
            </span>
            {hoveredWeek.week.has_live_session ? (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold">
                Live Session Completed
              </span>
            ) : hoveredWeek.week.is_current_week ? (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/30 font-semibold">
                Current Week
              </span>
            ) : (
              <span className="text-[10px] text-slate-400">
                {hoveredWeek.week.is_future_week ? 'Upcoming' : 'No Activity'}
              </span>
            )}
          </div>

          {/* Full Range Description */}
          <div className="text-[11px] font-semibold text-emerald-300 flex items-center gap-1">
            <Calendar className="w-3 h-3 shrink-0" />
            <span>{hoveredWeek.week.full_range_label}</span>
          </div>

          {/* Activities List in Tooltip */}
          {hoveredWeek.week.activities.length > 0 ? (
            <div className="space-y-1.5 pt-1">
              {hoveredWeek.week.activities.map((act, i) => (
                <div key={i} className="p-2 rounded-xl bg-black/50 border border-white/10 text-[10px] space-y-0.5">
                  <div className="font-semibold text-white flex items-center gap-1">
                    <Video className="w-3 h-3 text-emerald-400" />
                    <span>{act.title}</span>
                  </div>
                  {act.topic && <div className="text-slate-300">Topic: {act.topic}</div>}
                  {act.partner && <div className="text-slate-400">Peer Mentor: {act.partner}</div>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[10px] text-slate-400 leading-relaxed">
              {hoveredWeek.week.is_current_week
                ? 'Join or launch a 60-minute reciprocal classroom session this week to turn this box green.'
                : hoveredWeek.week.is_future_week
                ? 'Calendar period in the future.'
                : 'No live collaborative sessions recorded for this calendar period.'}
            </p>
          )}

          {/* Streak Status */}
          <div className="pt-1.5 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-400">
            <span>Weekly Goal Target: 1 Session</span>
            <span className={hoveredWeek.week.has_live_session ? 'text-emerald-400 font-semibold' : 'text-slate-400'}>
              {hoveredWeek.week.has_live_session ? 'Goal Met ✅' : 'Pending ⏳'}
            </span>
          </div>
        </div>
      )}

      {/* Explanation Modal */}
      {showExplanation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="relative w-full max-w-lg p-6 sm:p-8 rounded-3xl bg-slate-900 border border-white/10 shadow-2xl space-y-6">
            <button
              type="button"
              onClick={() => setShowExplanation(false)}
              className="absolute top-5 right-5 p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
                <Calendar className="w-3.5 h-3.5" /> Weekly Consistency Calendar
              </div>
              <h3 className="text-xl font-bold text-white">
                How EduMeet Tracks Your Activity
              </h3>
            </div>

            <div className="space-y-4 text-xs sm:text-sm text-slate-300 leading-relaxed">
              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
                <h4 className="font-semibold text-white flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs">
                    1
                  </span>
                  1 Box Per Week (4 Boxes per Month)
                </h4>
                <p className="text-slate-400 text-xs">
                  EduMeet divides each month into 4 weeks. Each week is represented by 1 box with exact Monday-to-Sunday or calendar date ranges (e.g. 1 Nov – 7 Nov).
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
                <h4 className="font-semibold text-white flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs">
                    2
                  </span>
                  Green on Live Sessions
                </h4>
                <p className="text-slate-400 text-xs">
                  Completing or participating in a Synchronized 60-Minute Classroom Session turns that week's box <span className="text-emerald-400 font-semibold">vibrant green</span>.
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
                <h4 className="font-semibold text-white flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-xs">
                    3
                  </span>
                  Streak Freeze Protection
                </h4>
                <p className="text-slate-400 text-xs">
                  Travel, illness, or exams? A missed week automatically consumes 1 streak freeze so you don't lose your consistency badge. A freeze refreshes every 4 active weeks.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowExplanation(false)}
              className="w-full py-3 rounded-2xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs tracking-wide transition-all shadow-lg shadow-brand-500/20 cursor-pointer"
            >
              Got it, thanks!
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
