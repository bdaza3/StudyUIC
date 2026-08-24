"use client";

import { FormEvent, useEffect, useState } from "react";
import { getSupabaseClient } from "@/lib/supabase";
import { getCourses, getStudySessionsForSpot } from "@/lib/data";
import type { Course, StudyBeacon, StudySession, StudySpot } from "@/lib/types";
import { useAuth } from "./AuthProvider";

type Props = { spot: StudySpot | null; onClose: () => void; onOpenSession: (session: StudySession) => void; onCreateSession: () => void; courseId?: string | null; onRequireAuth: () => void };
const time = (date: string) => new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(new Date(date));

export function SpotDetailDrawer({ spot, onClose, onOpenSession, onCreateSession, courseId, onRequireAuth }: Props) {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<StudySession[]>([]); const [beacons, setBeacons] = useState<StudyBeacon[]>([]); const [courses, setCourses] = useState<Course[]>([]);
  const [offeringId, setOfferingId] = useState(""); const [description, setDescription] = useState(""); const [message, setMessage] = useState<string | null>(null);
  useEffect(() => {
    if (!spot) return;
    const supabase = getSupabaseClient(); const reloadSessions = () => void getStudySessionsForSpot(spot.id, courseId).then(setSessions).catch(() => setMessage("Unable to load study sessions."));
    const reloadBeacons = () => void supabase.from("study_beacons").select("id,spot_id,course_code,description,created_at,expires_at").eq("spot_id", spot.id).gt("expires_at", new Date().toISOString()).order("created_at", { ascending: false }).then(({ data }) => setBeacons((data ?? []) as StudyBeacon[]));
    reloadSessions(); reloadBeacons(); void getCourses().then(setCourses).catch(() => {});
    const channel = supabase.channel(`spot:${spot.id}`).on("postgres_changes", { event: "*", schema: "public", table: "study_sessions", filter: `spot_id=eq.${spot.id}` }, reloadSessions).on("postgres_changes", { event: "*", schema: "public", table: "study_beacons", filter: `spot_id=eq.${spot.id}` }, reloadBeacons).subscribe();
    return () => { void supabase.removeChannel(channel); };
  }, [spot, courseId]);
  if (!spot) return null;
  const dropBeacon = async (event: FormEvent) => {
    event.preventDefault(); if (!user) return onRequireAuth(); if (!offeringId) return setMessage("Select a course first.");
    const supabase = getSupabaseClient();
    const { data: offering } = await supabase.from("course_offerings").select("id").eq("course_id", offeringId).eq("active", true).maybeSingle();
    if (!offering) return setMessage("That course is unavailable this term.");
    const { error } = await supabase.rpc("create_beacon", { p_spot_id: spot.id, p_course_offering_id: offering.id, p_description: description });
    if (error) setMessage("Unable to drop beacon. Please try again."); else { setDescription(""); setMessage("Beacon is live for two hours."); }
  };
  return <section role="dialog" aria-modal="true" className="absolute inset-x-0 bottom-0 z-20 rounded-t-3xl bg-white shadow-2xl"><div className="mx-auto h-1.5 w-10 rounded-full bg-slate-300"/><div className="max-h-[78dvh] overflow-y-auto px-5 pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-4"><div className="flex justify-between"><div><p className="text-sm font-semibold text-uic-flame">{spot.building}</p><h2 className="text-2xl font-bold">{spot.name}</h2><p className="text-sm text-slate-600">Outlet density: {spot.outlet_density}</p></div><button onClick={onClose} className="h-10 w-10 rounded-full hover:bg-slate-100" aria-label="Close">✕</button></div><div className="mt-5 border-t pt-4"><h3 className="font-bold">Active study sessions</h3>{sessions.length ? <div className="mt-3 space-y-2">{sessions.map(session=><button key={session.id} onClick={()=>onOpenSession(session)} className="w-full rounded-xl bg-blue-50 p-3 text-left"><p className="text-sm font-semibold text-uic-blue">{session.course_code ?? "Open study"}</p><p className="font-semibold">{session.title}</p><p className="text-sm text-slate-600">{time(session.starts_at)} – {time(session.ends_at)} · 👥 {session.attendee_count}{session.max_attendees ? ` / ${session.max_attendees}` : ""}</p></button>)}</div>:<p className="mt-2 text-sm text-slate-500">No active study sessions here yet.</p>}</div><div className="mt-5 border-t pt-4"><h3 className="font-bold">🔥 Live now</h3>{beacons.length ? beacons.map(beacon=><div key={beacon.id} className="mt-2 rounded-xl bg-amber-50 p-3"><b className="text-uic-blue">{beacon.course_code}</b><p className="text-sm">{beacon.description}</p></div>):<p className="mt-2 text-sm text-slate-500">No live beacons.</p>}</div><form onSubmit={dropBeacon} className="mt-5 space-y-2 border-t pt-4"><h3 className="font-bold">Drop a beacon</h3><select required value={offeringId} onChange={e=>setOfferingId(e.target.value)} className="w-full rounded-xl border p-3"><option value="">Select course</option>{courses.map(course=><option key={course.id} value={course.id}>{course.course_code} — {course.title}</option>)}</select><textarea required value={description} onChange={e=>setDescription(e.target.value)} maxLength={280} placeholder="What are you working on?" className="w-full rounded-xl border p-3"/><button className="w-full rounded-xl bg-uic-blue py-3 font-semibold text-white">{user ? "Drop a Beacon" : "Sign in to drop a beacon"}</button>{message&&<p className="text-center text-sm text-slate-600">{message}</p>}</form></div></section>;
}
