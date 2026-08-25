"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Map, { Marker, NavigationControl } from "react-map-gl/maplibre";
import { getSupabaseClient, getSupabaseConfigError } from "@/lib/supabase";
import type { StudySpot } from "@/lib/types";
import { SpotDetailDrawer } from "./SpotDetailDrawer";
import { AuthSheet } from "./AuthSheet";
import { SessionDetailSheet } from "./SessionDetailSheet";
import { CreateSessionSheet } from "./CreateSessionSheet";
import { SuggestSpotSheet } from "./SpotCommunitySheet";
import { useAuth } from "./AuthProvider";
import type { StudySession } from "@/lib/types";

const UIC_CENTER = { longitude: -87.6495, latitude: 41.8708, zoom: 15.3 };

function pointCoordinates(
  point: StudySpot["coordinates"],
): [number, number] | null {
  try {
    const geometry = typeof point === "string" ? JSON.parse(point) : point;
    if (geometry?.type !== "Point" || !Array.isArray(geometry.coordinates))
      return null;
    return geometry.coordinates as [number, number];
  } catch {
    return null;
  }
}

export function MapDashboard() {
  const [spots, setSpots] = useState<StudySpot[]>([]);
  const [selectedSpot, setSelectedSpot] = useState<StudySpot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [selectedSession, setSelectedSession] = useState<StudySession | null>(
    null,
  );
  const [createOpen, setCreateOpen] = useState(false);
  const [suggestOpen, setSuggestOpen] = useState(false);
  const [activity, setActivity] = useState<Record<string, string>>({});
  const { user } = useAuth();
  const missingStyleImages = useRef<Set<string>>(new Set());

  useEffect(() => {
    const loadSpots = async () => {
      const configError = getSupabaseConfigError();
      if (configError) {
        setError(configError);
        return;
      }

      try {
        const { data, error: queryError } = await getSupabaseClient()
          .from("study_spots")
          .select("id, name, building, outlet_density, coordinates")
          .order("name");

        if (queryError) setError(queryError.message);
        else setSpots((data ?? []) as StudySpot[]);
        const { data: activityData } =
          await getSupabaseClient().rpc("get_spot_activity");
        setActivity(
          Object.fromEntries(
            (activityData ?? []).map(
              (item: { spot_id: string; crowd_level: string }) => [
                item.spot_id,
                item.crowd_level,
              ],
            ),
          ),
        );
      } catch (loadError) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Unable to connect to Supabase.",
        );
      }
    };

    void loadSpots();
  }, []);

  const mappedSpots = useMemo(
    () =>
      spots.flatMap((spot) => {
        const coordinates = pointCoordinates(spot.coordinates);
        return coordinates ? [{ spot, coordinates }] : [];
      }),
    [spots],
  );

  return (
    <main className="relative h-[100dvh] w-full overflow-hidden bg-slate-100">
      <div className="h-full w-full">
        <Map
          initialViewState={UIC_CENTER}
          mapStyle="https://tiles.openfreemap.org/styles/liberty"
          attributionControl={false}
          onLoad={(event) => {
            const map = event.target;
            map.on("styleimagemissing", (missingEvent) => {
              const imageId = missingEvent.id;
              if (
                missingStyleImages.current.has(imageId) ||
                map.hasImage(imageId)
              )
                return;

              map.addImage(imageId, new ImageData(1, 1)); //transparent placeholder to avoid errors
              missingStyleImages.current.add(imageId);
            });
          }}
        >
          <NavigationControl position="bottom-right" showCompass={false} />
          {mappedSpots.map(({ spot, coordinates }) => (
            <Marker
              key={spot.id}
              longitude={coordinates[0]}
              latitude={coordinates[1]}
              anchor="bottom"
            >
              <button
                type="button"
                aria-label={`View ${spot.name}`}
                onClick={() => setSelectedSpot(spot)}
                className="grid h-11 w-9 place-items-center rounded-t-full rounded-b-full border-2 border-white bg-uic-flame text-lg text-white shadow-lg transition-transform active:scale-95"
              >
                <span
                  aria-hidden="true"
                  className="h-3 w-3 rounded-full bg-white"
                />
                {activity[spot.id] && (
                  <span className="absolute -right-2 -top-2 rounded-full bg-white px-1 text-[10px] text-slate-800">
                    {activity[spot.id] === "busy"
                      ? "Busy"
                      : activity[spot.id] === "moderate"
                        ? "Mod"
                        : "Quiet"}
                  </span>
                )}
              </button>
            </Marker>
          ))}
        </Map>
      </div>

      <header className="absolute inset-x-0 top-0 z-10 flex items-start justify-between p-4 pt-[max(1rem,env(safe-area-inset-top))]">
        <div className="rounded-2xl bg-white/95 px-4 py-3 shadow-lg backdrop-blur">
          <h1 className="text-lg font-bold tracking-tight text-uic-blue">
            StudyUIC
          </h1>
          <p className="text-xs text-slate-500">Find your next focus spot</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => (user ? setSuggestOpen(true) : setAuthOpen(true))}
            className="rounded-xl bg-white px-3 py-3 text-sm font-semibold text-uic-blue shadow-lg"
          >
            Suggest a spot
          </button>
          <button
            onClick={() => setAuthOpen(true)}
            className="rounded-xl bg-uic-blue px-4 py-3 text-sm font-semibold text-white shadow-lg"
          >
            {user ? "Account" : "Sign in"}
          </button>
        </div>
      </header>

      {error && (
        <p className="absolute inset-x-4 bottom-5 z-10 rounded-xl bg-red-50 p-3 text-sm text-red-700">
          Could not load spots: {error}
        </p>
      )}
      {!error && !mappedSpots.length && (
        <p className="absolute inset-x-4 bottom-5 z-10 rounded-xl bg-white p-4 text-sm shadow-lg">
          No study spots are available yet. Apply the seed migration to add the
          initial campus locations.
        </p>
      )}
      <SpotDetailDrawer
        spot={selectedSpot}
        onClose={() => setSelectedSpot(null)}
        onOpenSession={setSelectedSession}
        onCreateSession={() => setCreateOpen(true)}
        onRequireAuth={() => setAuthOpen(true)}
      />
      <SessionDetailSheet
        session={selectedSession}
        onClose={() => setSelectedSession(null)}
        onRequireAuth={() => setAuthOpen(true)}
      />
      <CreateSessionSheet
        spot={createOpen ? selectedSpot : null}
        onClose={() => setCreateOpen(false)}
      />
      <SuggestSpotSheet
        open={suggestOpen}
        onClose={() => setSuggestOpen(false)}
      />
      <AuthSheet open={authOpen} onClose={() => setAuthOpen(false)} />
    </main>
  );
}
