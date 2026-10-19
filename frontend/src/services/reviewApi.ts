import { apiClient } from '../api/client';

export interface MistakeItem {
  id: string;
  user_id: string;
  subject_slug: string;
  topic_slug: string;
  subtopic_slug: string;
  question_ref_id: string;
  question_prompt: string;
  user_mistake_tag: string;
  learner_notes?: string;
  resolved: boolean;
  created_at: string;
}

export interface ReviewScheduleItem {
  id: string;
  user_id: string;
  subject_slug: string;
  subtopic_slug: string;
  repetition_number: number;
  easiness_factor: number;
  interval_days: number;
  next_review_date: string;
  last_reviewed_at?: string;
  is_due: boolean;
}

export interface PostCheckResult {
  session_id: string;
  pre_score_percentage?: number;
  post_score_percentage: number;
  learning_gain_delta: number;
  total_questions: number;
  correct_count: number;
  snapshot_id: string;
}

export const reviewApi = {
  async getMistakes(subject_slug?: string, resolved?: boolean): Promise<MistakeItem[]> {
    const params = new URLSearchParams();
    if (subject_slug) params.append('subject_slug', subject_slug);
    if (resolved !== undefined) params.append('resolved', String(resolved));
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiClient<MistakeItem[]>(`/reviews/mistakes${query}`);
  },

  async resolveMistake(mistake_id: string): Promise<MistakeItem> {
    return apiClient<MistakeItem>(`/reviews/mistakes/${mistake_id}/resolve`, {
      method: 'PATCH',
    });
  },

  async getDueReviewSchedules(): Promise<ReviewScheduleItem[]> {
    return apiClient<ReviewScheduleItem[]>('/reviews/schedules/due');
  },

  async getAllReviewSchedules(): Promise<ReviewScheduleItem[]> {
    return apiClient<ReviewScheduleItem[]>('/reviews/schedules');
  },

  async evaluateReview(schedule_id: string, quality_rating: number): Promise<ReviewScheduleItem> {
    return apiClient<ReviewScheduleItem>(`/reviews/schedules/${schedule_id}/evaluate`, {
      method: 'POST',
      body: JSON.stringify({ quality_rating }),
    });
  },

  async getPostcheckQuestions(session_id: string): Promise<any[]> {
    return apiClient<any[]>(`/reviews/sessions/${session_id}/postcheck`);
  },

  async submitPostcheck(session_id: string, answers: Record<string, string>): Promise<PostCheckResult> {
    return apiClient<PostCheckResult>(`/reviews/sessions/${session_id}/postcheck/submit`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    });
  },

  async submitSessionRating(
    session_id: string,
    clarity: number,
    helpfulness: number,
    feedback_text?: string
  ): Promise<{ session_id: string; rated: boolean }> {
    return apiClient(`/reviews/sessions/${session_id}/rate`, {
      method: 'POST',
      body: JSON.stringify({ clarity, helpfulness, feedback_text }),
    });
  },

  async createPeerQuiz(session_id: string, questions: any[]): Promise<any> {
    return apiClient(`/peer-quizzes/${session_id}/create`, {
      method: 'POST',
      body: JSON.stringify({ questions }),
    });
  },

  async getAssignedPeerQuiz(session_id: string): Promise<any> {
    return apiClient(`/peer-quizzes/${session_id}/assigned`);
  },

  async getDraftedPeerQuiz(session_id: string): Promise<any> {
    return apiClient(`/peer-quizzes/${session_id}/drafted`);
  },

  async submitPeerQuizAnswers(session_id: string, answers: any[]): Promise<any> {
    return apiClient(`/peer-quizzes/${session_id}/submit`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    });
  },
};
