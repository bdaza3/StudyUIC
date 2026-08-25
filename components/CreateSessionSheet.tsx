"use client";

import { FormEvent, useEffect, useState } from "react";
import { getCourses } from "@/lib/data";
import { getSupabaseClient } from "@/lib/supabase";
import type { Course, StudySpot } from "@/lib/types";

export function CreateSessionSheet({
  spot,
  onClose,
}: {
  spot: StudySpot | null;
  onClose: () => void;
}) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [course, setCourse] = useState("");
  const [title, setTitle] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [max, setMax] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  useEffect(() => {
    void getCourses()
      .then(setCourses)
      .catch(() => setNotice("Unable to load courses."));
  }, []);
  if (!spot) return null;
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (new Date(end) <= new Date(start))
      return setNotice("End time must be after start time.");
    const supabase = getSupabaseClient();
    const { data: offering } = await supabase
      .from("course_offerings")
      .select("id")
      .eq("course_id", course)
      .eq("active", true)
      .maybeSingle();
    if (!offering) return setNotice("Select an active course.");
    const { error } = await supabase.rpc("create_study_session", {
      p_spot_id: spot.id,
      p_course_offering_id: offering.id,
      p_title: title,
      p_description: "",
      p_starts_at: new Date(start).toISOString(),
      p_ends_at: new Date(end).toISOString(),
      p_max_attendees: max ? Number(max) : null,
    });
    if (error)
      setNotice(
        "Unable to create this session. Check the fields and try again.",
      );
    else onClose();
  };
  return (
    <div className="absolute inset-0 z-40 flex items-end bg-slate-950/40">
      <form
        onSubmit={submit}
        className="w-full rounded-t-3xl bg-white p-5 pb-[max(1.5rem,env(safe-area-inset-bottom))]"
      >
        <div className="flex justify-between">
          <h2 className="text-xl font-bold">Create session</h2>
          <button type="button" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        <p className="mt-1 text-sm text-slate-600">at {spot.name}</p>
        <div className="mt-4 space-y-3">
          <select
            required
            value={course}
            onChange={(e) => setCourse(e.target.value)}
            className="w-full rounded-xl border p-3"
          >
            <option value="">Course</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.course_code} — {c.title}
              </option>
            ))}
          </select>
          <input
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Session title"
            className="w-full rounded-xl border p-3"
          />
          <input
            required
            type="datetime-local"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            className="w-full rounded-xl border p-3"
          />
          <input
            required
            type="datetime-local"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
            className="w-full rounded-xl border p-3"
          />
          <input
            type="number"
            min="1"
            value={max}
            onChange={(e) => setMax(e.target.value)}
            placeholder="Maximum attendees (optional)"
            className="w-full rounded-xl border p-3"
          />
        </div>
        <button className="mt-4 w-full rounded-xl bg-uic-blue py-3 font-semibold text-white">
          Create study session
        </button>
        {notice && <p className="mt-3 text-center text-sm">{notice}</p>}
      </form>
    </div>
  );
}
