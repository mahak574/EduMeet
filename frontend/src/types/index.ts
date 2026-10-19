export interface UserPreferences {
  preferred_teaching_style: 'visual' | 'socratic' | 'example_heavy' | 'theoretical';
  learning_goals: string[];
  audio_only_default: boolean;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'student' | 'admin';
  age_confirmed: boolean;
  country: string;
  timezone: string;
  languages: string[];
  subjects_studied: string[];
  is_verified_student: boolean;
  is_mentor: boolean;
  preferences?: UserPreferences;
}

export interface APIError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: APIError;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: User;
}
