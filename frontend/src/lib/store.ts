import { create } from "zustand";
import api from "@/lib/api";

interface User {
  id: string;
  phone: string;
  name: string | null;
  email: string | null;
  role: string | null;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isNew: boolean;
  isLoading: boolean;
  sendOtp: (phone: string) => Promise<string | null>;
  verifyOtp: (phone: string, otp: string) => Promise<boolean>;
  fetchMe: () => Promise<void>;
  updateUser: (data: Partial<User> & { role?: string }) => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>((set, get) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("hermes_token") : null,
  isNew: false,
  isLoading: false,

  sendOtp: async (phone: string) => {
    await api.post("/auth/otp/send", { phone });
    return null;
  },

  verifyOtp: async (phone: string, otp: string) => {
    const res = await api.post("/auth/otp/verify", { phone, otp });
    const { token, user_id, is_new } = res.data;
    localStorage.setItem("hermes_token", token);
    set({ token, isNew: is_new });
    await get().fetchMe();
    return is_new;
  },

  fetchMe: async () => {
    try {
      set({ isLoading: true });
      const res = await api.get("/auth/me");
      set({ user: res.data, isLoading: false });
    } catch {
      set({ user: null, isLoading: false });
    }
  },

  updateUser: async (data) => {
    await api.put("/auth/user", data);
    await get().fetchMe();
  },

  logout: () => {
    localStorage.removeItem("hermes_token");
    set({ user: null, token: null, isNew: false });
  },
}));
