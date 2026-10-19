import { apiClient } from '../api/client';

export interface PoolStatusResponse {
  is_in_pool: boolean;
  subject_slugs: string[];
  entered_at?: string;
  status?: string;
}

export interface MatchPartyInfo {
  user_id: string;
  user_name: string;
  teach_subject_slug: string;
  teach_topic_slug: string;
  learn_subject_slug: string;
  learn_topic_slug: string;
  confirmed: boolean;
  confirmed_at?: string;
  selected_slot?: string;
}

export interface MatchResponse {
  id: string;
  status: 'pending' | 'confirmed' | 'expired' | 'rejected';
  score: number;
  common_languages: string[];
  proposed_slots: string[];
  expires_at: string;
  session_id?: string;
  my_teach_subject?: string;
  my_teach_topic?: string;
  my_learn_subject?: string;
  my_learn_topic?: string;
  partner_name?: string;
  partner_id?: string;
  has_confirmed: boolean;
  partner_has_confirmed: boolean;
  participants: MatchPartyInfo[];
}

export const matchingApi = {
  async joinPool(subject_slugs: string[] = ['dsa', 'dbms']): Promise<PoolStatusResponse> {
    return apiClient<PoolStatusResponse>('/matching/pool/join', {
      method: 'POST',
      body: JSON.stringify({ subject_slugs }),
    });
  },

  async leavePool(): Promise<{ left: boolean }> {
    return apiClient<{ left: boolean }>('/matching/pool/leave', {
      method: 'POST',
    });
  },

  async getPoolStatus(): Promise<PoolStatusResponse> {
    return apiClient<PoolStatusResponse>('/matching/pool/status');
  },

  async getActiveMatch(): Promise<MatchResponse | null> {
    return apiClient<MatchResponse | null>('/matching/status');
  },

  async confirmMatch(matchId: string, chosenSlot: string): Promise<{
    match_id: string;
    match_status: string;
    session_id?: string;
    is_mutual: boolean;
  }> {
    return apiClient<{
      match_id: string;
      match_status: string;
      session_id?: string;
      is_mutual: boolean;
    }>(`/matching/confirm?match_id=${matchId}`, {
      method: 'POST',
      body: JSON.stringify({ chosen_slot: chosenSlot }),
    });
  },

  async declineMatch(matchId: string, reason?: string): Promise<{ declined: boolean }> {
    return apiClient<{ declined: boolean }>(`/matching/decline?match_id=${matchId}`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },
};
