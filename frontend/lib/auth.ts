/**
 * Authentication utilities for ZimPrep Frontend
 * 
 * Handles JWT token storage and user session management
 */

export interface User {
  id: string;
  email: string;
  role: string;
  name?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
  expires_in: number;
}

// ============================================================================
// TOKEN MANAGEMENT
// ============================================================================

/**
 * Store authentication token
 */
export function setAuthToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('zimprep_token', token);
  }
}

/**
 * Get authentication token
 */
export function getAuthToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('zimprep_token');
  }
  return null;
}

/**
 * Clear all authentication data
 */
export function clearAuth(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('zimprep_token');
    localStorage.removeItem('zimprep_user');
  }
}

// ============================================================================
// USER DATA MANAGEMENT
// ============================================================================

/**
 * Store user data
 */
export function setUser(user: User): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('zimprep_user', JSON.stringify(user));
  }
}

/**
 * Get stored user data
 */
export function getUser(): User | null {
  if (typeof window !== 'undefined') {
    const userData = localStorage.getItem('zimprep_user');
    return userData ? JSON.parse(userData) : null;
  }
  return null;
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return !!getAuthToken();
}

// ============================================================================
// LOGIN HELPER
// ============================================================================

/**
 * Login user and store credentials
 * 
 * @param email - User email
 * @param password - User password
 * @returns Login response with token and user data
 */
export async function login(email: string, password: string): Promise<LoginResponse> {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Login failed');
  }

  const data: LoginResponse = await response.json();
  
  // Store token and user
  setAuthToken(data.access_token);
  setUser(data.user);
  
  return data;
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
  const token = getAuthToken();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  if (token) {
    try {
      await fetch(`${API_URL}/api/v1/auth/logout`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    } catch (error) {
      console.error('Logout request failed:', error);
    }
  }
  
  clearAuth();
}
