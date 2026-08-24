import { getSupabaseClient } from "@/lib/supabase";
import type { Course, SessionMember, SessionMessage, StudySession, StudySpot } from "@/lib/types";

export async function getStudySpots(): Promise<StudySpot[]> {
  const { data, error } = await getSupabaseClient().from("study_spots").select("id,name,building,outlet_density,coordinates").order("name");
  if (error) throw new Error("Unable to load study spots.");
  return data as StudySpot[];
}

export async function getCourses(): Promise<Course[]> {
  const { data, error } = await getSupabaseClient().from("courses").select("id,department,course_number,course_code,title,description").eq("active", true).order("course_code");
  if (error) throw new Error("Unable to load courses.");
  return data as Course[];
}

export async function getStudySessionsForSpot(spotId: string, courseId?: string | null): Promise<StudySession[]> {
  const { data, error } = await getSupabaseClient().rpc("get_sessions_for_spot", { p_spot_id: spotId, p_course_id: courseId ?? null });
  if (error) throw new Error("Unable to load study sessions.");
  return data as StudySession[];
}

export async function getActiveStudySessions(courseId?: string | null): Promise<StudySession[]> {
  const { data, error } = await getSupabaseClient().rpc("get_active_study_sessions", { p_course_id: courseId ?? null });
  if (error) throw new Error("Unable to load active study sessions.");
  return data as StudySession[];
}

export async function getSessionMembers(sessionId: string): Promise<SessionMember[]> {
  const { data, error } = await getSupabaseClient().rpc("get_session_members", { p_session_id: sessionId });
  if (error) throw new Error("Unable to load attendees.");
  return data as SessionMember[];
}

export async function getSessionMessages(sessionId: string): Promise<SessionMessage[]> {
  const { data, error } = await getSupabaseClient().rpc("get_session_messages", { p_session_id: sessionId });
  if (error) throw new Error("Unable to load chat history.");
  return data as SessionMessage[];
}
