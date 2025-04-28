import { create } from 'zustand';
import { supabase } from '../lib/supabase';

interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string) => Promise<void>;
  signOut: () => Promise<void>;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: false,
  signIn: async (email: string, password: string) => {
    // Mock successful sign in
    set({
      user: {
        id: 'mock-user-id',
        email: email,
        name: 'Mock User',
      }
    });
  },
  signUp: async (email: string, password: string, name: string) => {
    // Mock successful sign up
    set({
      user: {
        id: 'mock-user-id',
        email: email,
        name: name,
      }
    });
  },
  signOut: async () => {
    set({ user: null });
  },
  setUser: (user) => set({ user, loading: false }),
}));