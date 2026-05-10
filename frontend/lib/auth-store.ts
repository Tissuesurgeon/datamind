"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type UserOut = {
  id: string;
  wallet_address: string;
  display_name: string | null;
  email: string | null;
  avatar_url: string | null;
  created_at: string;
};

type AuthState = {
  token: string | null;
  user: UserOut | null;
  hydrated: boolean;
  setSession: (token: string, user: UserOut) => void;
  signOut: () => void;
  setHydrated: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      hydrated: false,
      setSession: (token, user) => set({ token, user }),
      signOut: () => set({ token: null, user: null }),
      setHydrated: () => set({ hydrated: true }),
    }),
    {
      name: "datamind.auth",
      onRehydrateStorage: () => (state) => state?.setHydrated(),
    }
  )
);
