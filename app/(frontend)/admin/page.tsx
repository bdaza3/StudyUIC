"use client";
import { useEffect, useState } from "react";
import { getSupabaseClient } from "@/lib/supabase";
import { useAuth } from "../components/AuthProvider";

type Submission = {
  id: string;
  name: string;
  building: string;
  floor: string | null;
  created_at: string;
};
export default function AdminPage() {
  const { user, loading } = useAuth();
  const [admin, setAdmin] = useState(false),
    [items, setItems] = useState<Submission[]>([]),
    [notice, setNotice] = useState("");
  const load = async () => {
    const s = getSupabaseClient();
    const { data: profile } = await s
      .from("profiles")
      .select("role")
      .eq("id", user?.id ?? "")
      .maybeSingle();
    if (profile?.role !== "admin") return;
    setAdmin(true);
    const { data } = await s
      .from("study_spot_submissions")
      .select("id,name,building,floor,created_at")
      .eq("status", "pending")
      .order("created_at");
    setItems((data ?? []) as Submission[]);
  };
  useEffect(() => {
    if (user) void load();
  }, [user]);
  const review = async (id: string, approve: boolean) => {
    const { error } = await getSupabaseClient().rpc("review_spot_submission", {
      p_submission_id: id,
      p_approve: approve,
    });
    setNotice(
      error
        ? "Review failed."
        : approve
          ? "Spot approved."
          : "Suggestion rejected.",
    );
    if (!error) void load();
  };
  if (loading) return <main className="p-6">Loading…</main>;
  if (!user)
    return (
      <main className="p-6">
        Sign in with an administrator account to access moderation.
      </main>
    );
  if (!admin)
    return <main className="p-6">Administrator access required.</main>;
  return (
    <main className="mx-auto max-w-xl p-5">
      <h1 className="text-2xl font-bold text-uic-blue">Spot moderation</h1>
      <p className="mt-1 text-sm text-slate-600">Pending student suggestions</p>
      <div className="mt-5 space-y-3">
        {items.map((x) => (
          <article key={x.id} className="rounded-2xl border p-4">
            <h2 className="font-bold">{x.name}</h2>
            <p className="text-sm">
              {x.building}
              {x.floor ? ` · Floor ${x.floor}` : ""}
            </p>
            <div className="mt-3 flex gap-2">
              <button
                onClick={() => void review(x.id, true)}
                className="rounded-lg bg-uic-blue px-3 py-2 text-sm font-semibold text-white"
              >
                Approve
              </button>
              <button
                onClick={() => void review(x.id, false)}
                className="rounded-lg border px-3 py-2 text-sm"
              >
                Reject
              </button>
            </div>
          </article>
        ))}
        {!items.length && (
          <p className="rounded-xl bg-slate-50 p-4 text-sm">
            No pending suggestions.
          </p>
        )}
      </div>
      {notice && <p className="mt-4 text-sm">{notice}</p>}
    </main>
  );
}
