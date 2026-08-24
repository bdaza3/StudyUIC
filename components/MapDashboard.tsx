"use client";

import { useEffect, useMemo, useState } from "react";
import Map, { Marker, NavigationControl } from "react-map-gl/maplibre";
import { getSupabaseClient } from "@/lib/supabase";
import type { StudySpot } from "@/lib/types";
import { SpotDetailDrawer } from "./SpotDetailDrawer";

const UIC_CENTER = { longitude: -87.6495, latitude: 41.8708, zoom: 15.3 };

function pointCoordinates(point: StudySpot["coordinates"]): [number, number] | null {
  try {
    const geometry = typeof point === "string" ? JSON.parse(point) : point;
    if (geometry?.type !== "Point" || !Array.isArray(geometry.coordinates)) return null;
    return geometry.coordinates as [number, number];
  } catch {
    return null;
  }
}

export function MapDashboard() {
  const [spots, setSpots] = useState<StudySpot[]>([]);
  const [selectedSpot, setSelectedSpot] = useState<StudySpot | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSpots = async () => {
      const { data, error: queryError } = await getSupabaseClient()
        .from("study_spots")
        .select("id, name, building, outlet_density, coordinates")
        .order("name");

      if (queryError) setError(queryError.message);
      else setSpots((data ?? []) as StudySpot[]);
    };

    void loadSpots();
  }, []);

  const mappedSpots = useMemo(
    () => spots.flatMap((spot) => {
      const coordinates = pointCoordinates(spot.coordinates);
      return coordinates ? [{ spot, coordinates }] : [];
    }),
    [spots],
  );

  return (
    <main className="relative h-[100dvh] w-full overflow-hidden bg-slate-100">
      <div className="h-full w-full">
        <Map initialViewState={UIC_CENTER} mapStyle="https://tiles.openfreemap.org/styles/liberty" attributionControl={false}>
          <NavigationControl position="bottom-right" showCompass={false} />
          {mappedSpots.map(({ spot, coordinates }) => (
            <Marker key={spot.id} longitude={coordinates[0]} latitude={coordinates[1]} anchor="bottom">
              <button
                type="button"
                aria-label={`View ${spot.name}`}
                onClick={() => setSelectedSpot(spot)}
                className="grid h-11 w-9 place-items-center rounded-t-full rounded-b-full border-2 border-white bg-uic-flame text-lg text-white shadow-lg transition-transform active:scale-95"
              >
                <span aria-hidden="true" className="h-3 w-3 rounded-full bg-white" />
              </button>
            </Marker>
          ))}
        </Map>
      </div>

      <header className="pointer-events-none absolute inset-x-0 top-0 z-10 p-4 pt-[max(1rem,env(safe-area-inset-top))]">
        <div className="w-fit rounded-2xl bg-white/95 px-4 py-3 shadow-lg backdrop-blur">
          <h1 className="text-lg font-bold tracking-tight text-uic-blue">StudyUIC</h1>
          <p className="text-xs text-slate-500">Find your next focus spot</p>
        </div>
      </header>

      {error && <p className="absolute inset-x-4 bottom-5 z-10 rounded-xl bg-red-50 p-3 text-sm text-red-700">Could not load spots: {error}</p>}
      <SpotDetailDrawer spot={selectedSpot} onClose={() => setSelectedSpot(null)} />
    </main>
  );
}
