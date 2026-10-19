import { apiClient } from '../api/client';

export interface SessionDetails {
  session_id: string;
  status: 'scheduled' | 'waiting_room' | 'teacher_a' | 'teacher_b' | 'quiz_exchange' | 'followup' | 'closed' | 'cancelled' | 'no_show_cancelled';
  session_mode: string;
  my_role: 'teacher_a' | 'teacher_b';
  my_teach_subject: string;
  my_teach_topic: string;
  my_learn_subject: string;
  my_learn_topic: string;
  partner_id: string;
  partner_name: string;
  partner_role: string;
  partner_teach_topic: string;
  current_teacher_id: string | null;
  is_current_teacher: boolean;
  scheduled_start_utc: string;
  scheduled_end_utc: string;
  phase_ends_at: string | null;
  remaining_seconds: number;
  is_paused: boolean;
  total_paused_seconds: number;
  present_user_ids: string[];
  video_room_id: string;
  yjs_doc_id: string;
  chat_is_locked: boolean;
}

export interface WsTicketResponse {
  ticket: string;
  expires_in_seconds: number;
  session_id: string;
  role: string;
}

export interface PrecheckQuestion {
  question_id: string;
  subject_slug: string;
  topic_slug: string;
  difficulty: string;
  prompt_text: string;
  code_snippet?: string;
  options: Array<{ id: string; text: string }>;
}

export interface ChatMessage {
  id?: string;
  sender_id: string;
  sender_name: string;
  content: string;
  created_at: string;
}

export const sessionApi = {
  async getSessionDetails(sessionId: string): Promise<SessionDetails> {
    return apiClient<SessionDetails>(`/sessions/${sessionId}`);
  },

  async getWsTicket(sessionId: string): Promise<WsTicketResponse> {
    return apiClient<WsTicketResponse>(`/sessions/${sessionId}/ws-ticket`, {
      method: 'POST',
    });
  },

  async getPrecheckQuestions(sessionId: string): Promise<PrecheckQuestion[]> {
    return apiClient<PrecheckQuestion[]>(`/sessions/${sessionId}/precheck`);
  },

  async submitPrecheck(sessionId: string, answers: Record<string, string>): Promise<{
    session_id: string;
    score_percentage: number;
    correct_count: number;
    total_questions: number;
    snapshot_id: string;
  }> {
    return apiClient(`/sessions/${sessionId}/precheck/submit`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    });
  },

  async advancePhase(sessionId: string, targetPhase?: string): Promise<{
    session_id: string;
    status: string;
    phase_ends_at: string;
  }> {
    return apiClient(`/sessions/${sessionId}/advance`, {
      method: 'POST',
      body: JSON.stringify({ target_phase: targetPhase }),
    });
  },

  async getVideoToken(sessionId: string): Promise<{
    room_name: string;
    domain: string;
    display_name: string;
    user_id: string;
    role: string;
    audio_only: boolean;
  }> {
    return apiClient(`/sessions/${sessionId}/video-token`);
  },

  async getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
    return apiClient<ChatMessage[]>(`/sessions/${sessionId}/messages`);
  },

  async sendMessage(sessionId: string, content: string): Promise<ChatMessage> {
    return apiClient<ChatMessage>(`/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  },

  async getMySessions(): Promise<Array<{
    session_id: string;
    status: string;
    session_mode: string;
    my_role: string;
    my_teach_subject: string;
    my_teach_topic: string;
    my_learn_subject: string;
    my_learn_topic: string;
    partner_name: string;
    scheduled_start_utc: string;
    scheduled_end_utc: string;
  }>> {
    return apiClient<Array<any>>('/sessions/my');
  },

  async createDemoSession(): Promise<{
    session_id: string;
    status: string;
    message: string;
  }> {
    return apiClient<{ session_id: string; status: string; message: string }>('/sessions/demo', {
      method: 'POST',
    });
  },
};
