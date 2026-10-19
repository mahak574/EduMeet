import { apiClient } from '../api/client';

export interface QuestionOption {
  id: string;
  text: string;
}

export interface CurrentQuestion {
  attempt_id: string;
  subject_slug: string;
  current_index: number;
  total_questions: number;
  question_id: string;
  topic_slug: string;
  difficulty: string;
  prompt_text: string;
  code_snippet?: string;
  options: QuestionOption[];
  time_limit_seconds: number;
  expires_at: string;
  tab_switch_count: number;
  is_completed?: boolean;
}

export interface QuizResult {
  attempt_id: string;
  subject_slug: string;
  overall_score_percentage: number;
  completed_at: string;
  is_completed: boolean;
  auto_submitted_due_to_violations: boolean;
  topic_scores: Array<{
    topic_slug: string;
    score: number;
    confidence_level: string;
  }>;
}

export interface SkillDetail {
  score: number;
  confidence_level: string;
  last_assessed_at?: string;
  diagnostic_attempts_count: number;
}

export interface SkillProfileData {
  user_id: string;
  subjects: Record<string, Record<string, SkillDetail>>;
  last_diagnostic_at: Record<string, string>;
  recent_snapshots: Array<{
    subject_slug: string;
    topic_slug: string;
    score: number;
    source_type: string;
    source_id: string;
    recorded_at: string;
  }>;
}

export const quizApi = {
  async startQuiz(subject_slug: string): Promise<CurrentQuestion> {
    return apiClient<CurrentQuestion>('/quizzes/start', {
      method: 'POST',
      body: JSON.stringify({ subject_slug }),
    });
  },

  async getCurrentQuestion(attempt_id: string): Promise<CurrentQuestion> {
    return apiClient<CurrentQuestion>(`/quizzes/${attempt_id}/current-question`);
  },

  async submitAnswer(
    attempt_id: string,
    selected_option_id: string | null,
    elapsed_seconds: number
  ): Promise<CurrentQuestion | QuizResult> {
    return apiClient<CurrentQuestion | QuizResult>(`/quizzes/${attempt_id}/answer`, {
      method: 'POST',
      body: JSON.stringify({
        selected_option_id,
        elapsed_seconds,
      }),
    });
  },

  async resumeQuiz(attempt_id: string): Promise<CurrentQuestion> {
    return apiClient<CurrentQuestion>(`/quizzes/${attempt_id}/resume`, {
      method: 'POST',
    });
  },

  async recordTabSwitch(attempt_id: string): Promise<{
    tab_switch_count: number;
    auto_submitted_due_to_violations: boolean;
    message: string;
  }> {
    return apiClient<{
      tab_switch_count: number;
      auto_submitted_due_to_violations: boolean;
      message: string;
    }>(`/quizzes/${attempt_id}/tab-switch`, {
      method: 'POST',
    });
  },

  async getQuizResult(attempt_id: string): Promise<QuizResult> {
    return apiClient<QuizResult>(`/quizzes/${attempt_id}/result`);
  },

  async getMySkills(): Promise<SkillProfileData> {
    return apiClient<SkillProfileData>('/skills/me');
  },
};
