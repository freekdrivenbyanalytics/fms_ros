import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useRef } from "react";
import type { DayPlanningRoutes } from "../types";

// Oslo - shown when there are no routes to fit bounds to (e.g. an empty day).
const DEFAULT_CENTER: L.LatLngExpression = [59.9139, 10.7522];
const DEFAULT_ZOOM = 8;

// Stable per employee (keyed by id, not render order) so a given employee's
// route keeps the same color across day changes and re-fetches.
const ROUTE_COLORS = [
  "#059669",
  "#2563eb",
  "#d97706",
  "#dc2626",
  "#7c3aed",
  "#0891b2",
  "#db2777",
  "#65a30d",
];

function colorForEmployee(employeeId: number): string {
  return ROUTE_COLORS[employeeId % ROUTE_COLORS.length];
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function buildEmployeePopup(employeeName: string): HTMLElement {
  const container = document.createElement("div");
  container.className = "text-sm font-medium text-slate-900";
  container.textContent = employeeName;
  return container;
}

function buildVisitPopup(
  customerName: string | null,
  plannedStart: string | null,
  plannedEnd: string | null
): HTMLElement {
  const container = document.createElement("div");
  container.className = "text-sm";

  const name = document.createElement("div");
  name.className = "font-medium text-slate-900";
  name.textContent = customerName ?? "Unknown customer";
  container.appendChild(name);

  if (plannedStart && plannedEnd) {
    const time = document.createElement("div");
    time.className = "text-slate-600";
    time.textContent = `${formatTime(plannedStart)} – ${formatTime(plannedEnd)}`;
    container.appendChild(time);
  }

  return container;
}

interface Props {
  routes: DayPlanningRoutes;
}

export function DayRouteMap({ routes }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layersRef = useRef<L.Layer[]>([]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current).setView(DEFAULT_CENTER, DEFAULT_ZOOM);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map);
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    layersRef.current.forEach((layer) => map.removeLayer(layer));
    const newLayers: L.Layer[] = [];

    for (const employeeRoute of routes.employees) {
      const color = colorForEmployee(employeeRoute.employee_id);
      const latlngs = employeeRoute.route.map((p) => [p.lat, p.lng] as L.LatLngTuple);

      if (latlngs.length >= 2) {
        const polyline = L.polyline(latlngs, { color, weight: 4, opacity: 0.85 }).addTo(map);
        polyline.bindPopup(buildEmployeePopup(employeeRoute.employee_name));
        newLayers.push(polyline);
      }

      for (const stop of employeeRoute.stops) {
        const isHome = stop.kind === "employee";
        const marker = L.circleMarker([stop.latitude, stop.longitude], {
          radius: isHome ? 8 : 6,
          color: "#ffffff",
          weight: 2,
          fillColor: color,
          fillOpacity: 1,
        }).addTo(map);

        marker.bindPopup(
          isHome
            ? buildEmployeePopup(employeeRoute.employee_name)
            : buildVisitPopup(stop.customer_name, stop.planned_start, stop.planned_end)
        );
        newLayers.push(marker);
      }
    }

    layersRef.current = newLayers;

    const allPoints = routes.employees.flatMap((employeeRoute) =>
      employeeRoute.route.map((p) => [p.lat, p.lng] as L.LatLngTuple)
    );
    if (allPoints.length > 0) {
      map.fitBounds(allPoints, { padding: [24, 24], maxZoom: 14 });
    }
  }, [routes]);

  return (
    <div>
      <div
        ref={containerRef}
        style={{ height: "480px", width: "100%" }}
        className="rounded-md border border-slate-200"
      />
      {routes.employees.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
          {routes.employees.map((employeeRoute) => (
            <div key={employeeRoute.employee_id} className="flex items-center gap-1.5 text-xs text-slate-600">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: colorForEmployee(employeeRoute.employee_id) }}
              />
              {employeeRoute.employee_name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
