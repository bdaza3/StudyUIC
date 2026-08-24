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
