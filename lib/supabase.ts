import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const publishableKey =
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ??
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

let client: SupabaseClient | undefined;

export function getSupabaseConfigError(): string | null {
  if (!url || !publishableKey) {
    return "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY (or NEXT_PUBLIC_SUPABASE_ANON_KEY).";
  }
  return null;
}

export function getSupabaseClient(): SupabaseClient {
  if (client) return client;
  const configError = getSupabaseConfigError();
  if (configError) {
    throw new Error(configError);
  }
  client = createClient(url!, publishableKey!);
  return client;
}
