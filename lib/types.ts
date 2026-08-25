export type OutletDensity = "High" | "Med" | "Low";

export type StudySpot = {
  id: string;
  name: string;
  building: string;
  outlet_density: OutletDensity;
  coordinates: GeoJSON.Point | string;
};

export type StudyBeacon = {
  id: string;
  spot_id: string;
  course_code: string;
  description: string;
  created_at: string;
  expires_at: string;
};

export type Course = {
  id: string;
  department: string;
  course_number: string;
  course_code: string;
  title: string;
  description: string | null;
};
export type CourseOffering = {
  id: string;
  course_id: string;
  term: string;
  year: number;
  course?: Course;
};
export type StudySession = {
  id: string;
  spot_id: string;
  course_offering_id: string | null;
  creator_id: string;
  title: string;
  description: string | null;
  starts_at: string;
  ends_at: string;
  max_attendees: number | null;
  attendee_count: number;
  course_code: string | null;
  course_title: string | null;
};
export type SessionMember = {
  user_id: string;
  display_name: string;
  status: "joined" | "left";
  joined_at: string;
};
export type SessionMessage = {
  id: string;
  session_id: string;
  user_id: string;
  message: string;
  created_at: string;
  display_name: string;
};
