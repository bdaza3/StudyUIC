"use client";
import { FormEvent, useEffect, useState } from "react";
import { getCourses } from "@/lib/data";
import { getSupabaseClient } from "@/lib/supabase";
import type { Course, MapBeacon } from "@/lib/types";
import { useAuth } from "./AuthProvider";

export function MapBeaconSheet({
  coordinates,
  onClose,
  onRequireAuth,
}: {
  coordinates: [number, number] | null;
  onClose: () => void;
  onRequireAuth: () => void;
}) {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]),
    [course, setCourse] = useState(""),
    [title, setTitle] = useState(""),
    [description, setDescription] = useState(""),
    [minutes, setMinutes] = useState("120"),
    [notice, setNotice] = useState<string | null>(null);
  useEffect(() => {
    if (coordinates) void getCourses().then(setCourses);
  }, [coordinates]);
  if (!coordinates) return null;
  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!user) return onRequireAuth();
    const s = getSupabaseClient();
    const { data } = await s
      .from("course_offerings")
      .select("id")
      .eq("course_id", course)
      .eq("active", true)
      .maybeSingle();
    if (!data) return setNotice("Select an active course.");
    const duration = Number(minutes);
    if (!Number.isFinite(coordinates[0]) || !Number.isFinite(coordinates[1]))
      return setNotice("Choose a valid point on the map.");
    if (!Number.isInteger(duration) || duration < 1 || duration > 180)
      return setNotice("Choose a duration up to three hours.");
    const { error } = await s.rpc("create_map_beacon", {
      p_longitude: coordinates[0],
      p_latitude: coordinates[1],
      p_course_offering_id: data.id,
      p_title: title,
      p_description: description,
      p_duration_minutes: duration,
    });
    if (error)
      setNotice(
        error.message.includes("number")
          ? "Choose a valid map location and duration."
          : "Could not create beacon. Please try again.",
      );
    else onClose();
  };
  return (
    <div className="absolute inset-0 z-50 flex items-end bg-slate-950/35">
      <form
        onSubmit={submit}
        className="w-full rounded-t-3xl bg-white p-6 pb-[max(1.5rem,env(safe-area-inset-bottom))]"
      >
        <div className="flex justify-between">
          <div>
            <h2 className="text-xl font-bold">Create map beacon</h2>
            <p className="text-sm text-slate-600">
              Let others know you're studying at this point on the map!
            </p>
          </div>
          <button type="button" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="mt-5 space-y-3">
          <select
            required
            value={course}
            onChange={(e) => setCourse(e.target.value)}
            className="w-full rounded-xl border p-3"
          >
            <option value="">Select course</option>
            {courses.map((x) => (
              <option key={x.id} value={x.id}>
                {x.course_code} — {x.title}
              </option>
            ))}
          </select>
          <input
            required
            minLength={2}
            maxLength={80}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Beacon title (e.g. Midterm review)"
            className="w-full rounded-xl border p-3"
          />
          <textarea
            required
            maxLength={280}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What are you studying?"
            className="w-full rounded-xl border p-3"
          />
          <label className="block text-sm font-medium">
            Duration
            <select
              value={minutes}
              onChange={(e) => setMinutes(e.target.value)}
              className="mt-1 w-full rounded-xl border p-3"
            >
              <option value="30">30 minutes</option>
              <option value="60">1 hour</option>
              <option value="120">2 hours</option>
              <option value="180">3 hours (maximum)</option>
            </select>
          </label>
        </div>
        <button className="mt-4 w-full rounded-xl bg-uic-blue py-3 font-semibold text-white">
          {user ? "Create beacon" : "Sign in to create beacon"}
        </button>
        {notice && <p className="mt-3 text-center text-sm">{notice}</p>}
      </form>
    </div>
  );
}

export function MapBeaconDetail({
  beacon,
  onClose,
}: {
  beacon: MapBeacon | null;
  onClose: () => void;
}) {
  const { user } = useAuth();
  if (!beacon) return null;
  const own = user?.id === beacon.user_id;
  const cancel = async () => {
    await getSupabaseClient().from("map_beacons").delete().eq("id", beacon.id);
    onClose();
  };
  return (
    <div className="absolute inset-0 z-50 flex items-end bg-slate-950/35">
      <section className="w-full rounded-t-3xl bg-white p-6">
        <div className="flex justify-between">
          <div>
            <p className="text-sm font-semibold text-uic-flame">
              Live map beacon
            </p>
            <h2 className="text-xl font-bold">{beacon.title}</h2>
            <p className="text-sm font-semibold text-uic-blue">
              {beacon.course_code}
            </p>
          </div>
          <button onClick={onClose}>✕</button>
        </div>
        <p className="mt-3">{beacon.description}</p>
        <div className="mt-4 flex items-center justify-between rounded-xl bg-slate-50 p-3">
          <div>
            <b>👥 {beacon.attending_count} attending</b>
            <p className="text-sm text-slate-600">
              ☆ {beacon.interested_count} interested
            </p>
          </div>
          <div className="flex -space-x-2">
            {beacon.people.slice(0, 3).map((person, index) => (
              <span
                key={`${person.display_name}-${index}`}
                title={person.display_name}
                className="grid h-8 w-8 place-items-center rounded-full border-2 border-white bg-uic-blue text-xs font-bold text-white"
              >
                {person.display_name.slice(0, 1)}
              </span>
            ))}
          </div>
        </div>
        {!own && user && (
          <div className="mt-3 grid grid-cols-2 gap-2">
            <button
              onClick={() =>
                void getSupabaseClient().rpc("set_map_beacon_status", {
                  p_beacon_id: beacon.id,
                  p_status: "attending",
                })
              }
              className="rounded-xl bg-uic-blue py-3 font-semibold text-white"
            >
              I&apos;m attending
            </button>
            <button
              onClick={() =>
                void getSupabaseClient().rpc("set_map_beacon_status", {
                  p_beacon_id: beacon.id,
                  p_status: "interested",
                })
              }
              className="rounded-xl border py-3 font-semibold"
            >
              Interested
            </button>
          </div>
        )}
        <p className="mt-2 text-sm text-slate-500">
          Expires{" "}
          {new Date(beacon.expires_at).toLocaleTimeString([], {
            hour: "numeric",
            minute: "2-digit",
          })}
        </p>
        {own && (
          <button
            onClick={() => void cancel()}
            className="mt-5 w-full rounded-xl border border-red-200 py-3 font-semibold text-red-700"
          >
            Cancel beacon
          </button>
        )}
      </section>
    </div>
  );
}
