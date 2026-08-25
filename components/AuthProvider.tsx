"use client";

import { createContext, useContext, useEffect, useState } from "react";
import type { User } from "@supabase/supabase-js";
import { getSupabaseClient } from "@/lib/supabase";

type AuthValue = {
  user: User | null;
  loading: boolean;
  signIn: (email: string) => Promise<string | null>;
  signOut: () => Promise<void>;
};
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const supabase = getSupabaseClient();
    void supabase.auth.getUser().then(({ data }) => {
      setUser(data.user);
      setLoading(false);
    });
    const { data: listener } = supabase.auth.onAuthStateChange(
      (_event, session) => setUser(session?.user ?? null),
    );
    return () => listener.subscription.unsubscribe();
  }, []);
  const signIn = async (email: string) => {
    if (!email.trim().toLowerCase().endsWith("@uic.edu"))
      return "Use your @uic.edu email address.";
    const { error } = await getSupabaseClient().auth.signInWithOtp({
      email,
      options: { emailRedirectTo: window.location.origin },
    });
    return error
      ? "We could not send that sign-in link. Please try again."
      : null;
  };
  const signOut = async () => {
    await getSupabaseClient().auth.signOut();
  };
  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
