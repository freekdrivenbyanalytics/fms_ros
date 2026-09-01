import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useRef } from "react";
import type { GeoPoint } from "../types";

const DEFAULT_CENTER: L.LatLngExpression = [52.1, 5.1];
const DEFAULT_ZOOM = 8;

const pointIcon = L.divIcon({
  className: "",
  html: '<div style="width:14px;height:14px;border-radius:50%;background:#059669;border:2px solid white;box-shadow:0 0 2px rgba(0,0,0,0.5);"></div>',
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

interface Props {
  value: GeoPoint[] | null;
  onChange: (points: GeoPoint[]) => void;
}

export function GeoShapeEditor({ value, onChange }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const polygonRef = useRef<L.Polygon | L.Polyline | null>(null);
  const pointsRef = useRef<GeoPoint[]>(value ?? []);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;
  const redrawRef = useRef<() => void>(() => {});

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const initialPoints = value ?? [];
    const center: L.LatLngExpression =
      initialPoints.length > 0
        ? [
            initialPoints.reduce((sum, p) => sum + p.lat, 0) / initialPoints.length,
            initialPoints.reduce((sum, p) => sum + p.lng, 0) / initialPoints.length,
          ]
        : DEFAULT_CENTER;

    const map = L.map(containerRef.current).setView(center, DEFAULT_ZOOM);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map);
    mapRef.current = map;

    function redraw() {
      const latlngs = pointsRef.current.map((p) => [p.lat, p.lng] as L.LatLngTuple);

      if (polygonRef.current) {
        map.removeLayer(polygonRef.current);
        polygonRef.current = null;
      }
      if (latlngs.length >= 3) {
        polygonRef.current = L.polygon(latlngs, { color: "#059669" }).addTo(map);
      } else if (latlngs.length === 2) {
        polygonRef.current = L.polyline(latlngs, { color: "#059669" }).addTo(map);
      }

      markersRef.current.forEach((marker) => map.removeLayer(marker));
      markersRef.current = pointsRef.current.map((point, index) => {
        const marker = L.marker([point.lat, point.lng], { icon: pointIcon, draggable: true }).addTo(
          map
        );
        marker.on("drag", () => {
          const latlng = marker.getLatLng();
          pointsRef.current[index] = { lat: latlng.lat, lng: latlng.lng };
          redraw();
        });
        marker.on("dragend", () => {
          onChangeRef.current([...pointsRef.current]);
        });
        return marker;
      });
    }

    redrawRef.current = redraw;

    map.on("click", (event: L.LeafletMouseEvent) => {
      pointsRef.current = [
        ...pointsRef.current,
        { lat: event.latlng.lat, lng: event.latlng.lng },
      ];
      redraw();
      onChangeRef.current([...pointsRef.current]);
    });

    redraw();

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function removeLastPoint() {
    if (pointsRef.current.length === 0) return;
    pointsRef.current = pointsRef.current.slice(0, -1);
    redrawRef.current();
    onChangeRef.current([...pointsRef.current]);
  }

  return (
    <div>
      <div
        ref={containerRef}
        style={{ height: "320px", width: "100%" }}
        className="rounded-md border border-slate-200"
      />
      <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
        <span>Click the map to add points. Drag a point to move it.</span>
        <button
          type="button"
          onClick={removeLastPoint}
          className="px-2 py-1 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50"
        >
          Remove last point
        </button>
      </div>
    </div>
  );
}
