"use client";

import { FormEvent, useEffect, useState } from "react";
import { getSupabaseClient } from "@/lib/supabase";
import type { StudyBeacon, StudySpot } from "@/lib/types";

type Props = { spot: StudySpot | null; onClose: () => void };

const isActive = (beacon: StudyBeacon) => new Date(beacon.expires_at).getTime() > Date.now();

export function SpotDetailDrawer({ spot, onClose }: Props) {
  const [beacons, setBeacons] = useState<StudyBeacon[]>([]);
  const [courseCode, setCourseCode] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!spot) return;
    const supabase = getSupabaseClient();
    setBeacons([]);
    setMessage(null);

    const loadBeacons = async () => {
      const { data, error } = await supabase
        .from("study_beacons")
        .select("id, spot_id, course_code, description, created_at, expires_at")
        .eq("spot_id", spot.id)
        .gt("expires_at", new Date().toISOString())
        .order("created_at", { ascending: false });
      if (error) setMessage(error.message);
      else setBeacons((data ?? []) as StudyBeacon[]);
    };
    void loadBeacons();

    const channel = supabase
      .channel(`study-beacons:${spot.id}`)
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "study_beacons", filter: `spot_id=eq.${spot.id}` },
        (payload) => {
          if (payload.eventType === "DELETE") {
            setBeacons((current) => current.filter((beacon) => beacon.id !== payload.old.id));
            return;
          }
          const beacon = payload.new as StudyBeacon;
          setBeacons((current) => {
            const withoutUpdated = current.filter((item) => item.id !== beacon.id);
            return isActive(beacon) ? [beacon, ...withoutUpdated] : withoutUpdated;
          });
        },
      )
      .subscribe();

    return () => {
      void supabase.removeChannel(channel);
    };
  }, [spot]);

  const submitBeacon = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!spot) return;
    setIsSubmitting(true);
    setMessage(null);
    const { error } = await getSupabaseClient().from("study_beacons").insert({
      spot_id: spot.id,
      course_code: courseCode.trim(),
      description: description.trim(),
      expires_at: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
    });
    setIsSubmitting(false);
    if (error) setMessage(error.message);
    else {
      setCourseCode("");
      setDescription("");
      setMessage("Beacon is live for the next two hours.");
    }
  };

  if (!spot) return null;

  return (
    <section role="dialog" aria-modal="true" aria-label={`${spot.name} details`} className="absolute inset-x-0 bottom-0 z-20 rounded-t-3xl bg-white shadow-2xl">
      <div className="mx-auto h-1.5 w-10 rounded-full bg-slate-300" />
      <div className="max-h-[78dvh] overflow-y-auto px-5 pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-uic-flame">{spot.building}</p>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">{spot.name}</h2>
            <p className="mt-1 text-sm text-slate-600">Outlet density: <span className="font-semibold">{spot.outlet_density}</span></p>
          </div>
          <button type="button" onClick={onClose} className="rounded-full p-2 text-slate-500 hover:bg-slate-100" aria-label="Close details">✕</button>
        </div>

        <div className="mt-6 border-t border-slate-100 pt-5">
          <h3 className="font-bold text-slate-900">Live study groups</h3>
          <div className="mt-3 space-y-2">
            {beacons.length ? beacons.map((beacon) => (
              <article key={beacon.id} className="rounded-xl bg-blue-50 p-3">
                <p className="font-semibold text-uic-blue">{beacon.course_code}</p>
                <p className="mt-0.5 text-sm text-slate-700">{beacon.description}</p>
              </article>
            )) : <p className="text-sm text-slate-500">No live groups here yet. Start one below.</p>}
          </div>
        </div>

        <form onSubmit={submitBeacon} className="mt-6 space-y-3 border-t border-slate-100 pt-5">
          <h3 className="font-bold text-slate-900">Drop a beacon</h3>
          <input required maxLength={32} value={courseCode} onChange={(event) => setCourseCode(event.target.value)} placeholder="Course code (e.g. CS 251)" className="w-full rounded-xl border border-slate-300 px-3 py-3 text-base outline-none focus:border-uic-blue focus:ring-2 focus:ring-blue-100" />
          <textarea required maxLength={280} value={description} onChange={(event) => setDescription(event.target.value)} placeholder="What are you working on?" rows={2} className="w-full resize-none rounded-xl border border-slate-300 px-3 py-3 text-base outline-none focus:border-uic-blue focus:ring-2 focus:ring-blue-100" />
          <button disabled={isSubmitting} type="submit" className="w-full rounded-xl bg-uic-blue px-4 py-3 font-semibold text-white transition-colors hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60">
            {isSubmitting ? "Dropping beacon…" : "Drop a Beacon"}
          </button>
          {message && <p role="status" className="text-center text-sm text-slate-600">{message}</p>}
        </form>
      </div>
    </section>
  );
}
