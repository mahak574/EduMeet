import { apiClient } from '../api/client';

export interface ActivityDay {
  date: string;
  count: number;
  level: number; // 0..4
  day_of_week: number; // 0..6
}

export interface ActivityItem {
  type: 'live_session' | 'quiz' | 'mistake';
  title: string;
  topic?: string;
  partner?: string;
  score?: string;
  date: string;
  status?: string;
}

export interface ActivityWeek {
  week_id: string;
  week_number: number;
  month_number: number;
  start_day: number;
  end_day: number;
  start_date: string;
  end_date: string;
  start_day_name: string;
  end_day_name: string;
  range_label: string;
  full_range_label: string;
  has_live_session: boolean;
  live_sessions_count: number;
  quiz_count: number;
  total_contributions: number;
  level: number; // 0: inactive, 1: quiz/practice, 2..4: live session (vibrant green)
  is_current_week: boolean;
  is_past_week: boolean;
  is_future_week: boolean;
  activities: ActivityItem[];
}

export interface ActivityMonth {
  month_name: string;
  month_short: string;
  month_number: number;
  year: number;
  weeks_count: number;
  active_weeks_count: number;
  weeks: ActivityWeek[];
}

export interface WeeklyStreakData {
  total_contributions: number;
  total_live_sessions?: number;
  current_weekly_streak: number;
  longest_weekly_streak: number;
  streak_freezes_available: number;
  weekly_goal_met: boolean;
  current_week_contributions: number;
  weekly_goal_target: number;
  year?: number;
  months?: ActivityMonth[];
  days: ActivityDay[];
}

export const activityApi = {
  async getActivityHeatmap(): Promise<WeeklyStreakData> {
    return apiClient<WeeklyStreakData>('/users/me/activity');
  },
};
