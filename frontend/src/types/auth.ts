export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  message: string;
  user: User;
  access_token?: string;
  token_type?: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isInitialColdLoad: boolean;
  login: (credentials: LoginCredentials) => Promise<User>;
  logout: () => Promise<void>;
  refetchUser: () => Promise<void>;
}
