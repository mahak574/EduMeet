import { apiClient } from '../api/client';

export interface ActivityDay {
  date: string;
  count: number;
  level: number; // 0..4
  day_of_week: number; // 0..6
}

export interface WeeklyStreakData {
  total_contributions: number;
  current_weekly_streak: number;
  longest_weekly_streak: number;
  streak_freezes_available: number;
  weekly_goal_met: boolean;
  current_week_contributions: number;
  weekly_goal_target: number;
  days: ActivityDay[];
}

export const activityApi = {
  async getActivityHeatmap(): Promise<WeeklyStreakData> {
    return apiClient<WeeklyStreakData>('/users/me/activity');
  },
};
