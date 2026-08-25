"use client";
import { FormEvent, useEffect, useState } from "react";
import { getSupabaseClient } from "@/lib/supabase";
import { useAuth } from "./AuthProvider";

type Data = {
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  major: string | null;
  graduation_year: number | null;
  show_last_initial: boolean;
};
export function Profile({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { user, signOut } = useAuth();
  const [data, setData] = useState<Data | null>(null);
  const [sessions, setSessions] = useState(0);
  const [beacons, setBeacons] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);
  useEffect(() => {
    if (!open || !user) return;
    const s = getSupabaseClient();
    void s
      .from("profiles")
      .select(
        "first_name,last_name,email,major,graduation_year,show_last_initial",
      )
      .eq("id", user.id)
      .single()
      .then(({ data }) => setData(data as Data));
    void s
      .from("study_sessions")
      .select("id", { count: "exact", head: true })
      .eq("creator_id", user.id)
      .gt("ends_at", new Date().toISOString())
      .then(({ count }) => setSessions(count ?? 0));
    void s
      .from("study_beacons")
      .select("id", { count: "exact", head: true })
      .eq("user_id", user.id)
      .gt("expires_at", new Date().toISOString())
      .then(({ count }) => setBeacons(count ?? 0));
  }, [open, user]);
  if (!open || !user || !data) return null;
  const save = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const { error } = await getSupabaseClient().rpc("update_my_profile", {
      p_first_name: f.get("first") as string,
      p_last_name: f.get("last") as string,
      p_show_last_initial: f.get("initial") === "on",
      p_major: f.get("major") as string,
      p_graduation_year: f.get("year") ? Number(f.get("year")) : null,
      p_avatar_url: "",
    });
    setNotice(error ? "Could not save your profile." : "Profile saved.");
  };
  const initials = `${data.first_name?.[0] ?? "U"}${data.last_name?.[0] ?? ""}`;
  return (
    <div className="absolute inset-0 z-50 flex items-end bg-slate-950/35">
      <form
        onSubmit={save}
        className="max-h-[90dvh] w-full overflow-y-auto rounded-t-3xl bg-white p-6"
      >
        <div className="flex justify-between">
          <h2 className="text-xl font-bold">Your profile</h2>
          <button type="button" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="mt-5 flex items-center gap-3">
          <div className="grid h-14 w-14 place-items-center rounded-full bg-uic-blue text-lg font-bold text-white">
            {initials}
          </div>
          <div>
            <p className="font-semibold">
              {data.first_name}{" "}
              {data.show_last_initial ? data.last_name?.[0] + "." : ""}
            </p>
            <p className="text-sm text-slate-500">{data.email ?? user.email}</p>
          </div>
        </div>
        <div className="mt-5 grid grid-cols-2 gap-3">
          <div className="rounded-xl bg-slate-50 p-3">
            <b>{sessions}</b>
            <p className="text-xs">My active sessions</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-3">
            <b>{beacons}</b>
            <p className="text-xs">My live beacons</p>
          </div>
        </div>
        <div className="mt-5 space-y-3">
          <input
            name="first"
            required
            defaultValue={data.first_name ?? ""}
            placeholder="First name"
            className="w-full rounded-xl border p-3"
          />
          <input
            name="last"
            defaultValue={data.last_name ?? ""}
            placeholder="Last name"
            className="w-full rounded-xl border p-3"
          />
          <label className="flex gap-2 text-sm">
            <input
              name="initial"
              type="checkbox"
              defaultChecked={data.show_last_initial}
            />{" "}
            Show only my last initial to other students
          </label>
          <input
            name="major"
            defaultValue={data.major ?? ""}
            placeholder="Major"
            className="w-full rounded-xl border p-3"
          />
          <input
            name="year"
            type="number"
            min="2000"
            max="2100"
            defaultValue={data.graduation_year ?? ""}
            placeholder="Graduation year"
            className="w-full rounded-xl border p-3"
          />
        </div>
        <button className="mt-4 w-full rounded-xl bg-uic-blue py-3 font-semibold text-white">
          Save profile
        </button>
        <button
          type="button"
          onClick={() => void signOut()}
          className="mt-3 w-full py-2 text-sm text-slate-600 underline"
        >
          Sign out
        </button>
        {notice && <p className="mt-3 text-center text-sm">{notice}</p>}
      </form>
    </div>
  );
}
