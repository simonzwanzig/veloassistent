import openrouteservice
import folium
import requests
import time

# ==========================
# KONFIGURATION
# ==========================

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjRlYmE4MmQyY2YzMzRiM2Q4ZTMzODhhNTIzOTkzNmRjIiwiaCI6Im11cm11cjY0In0="

POI_RADIUS_METERS = 150

# ==========================
# ROUTING (OpenRouteService)
# ==========================

def find_bike_route(start_name, end_name):
    client = openrouteservice.Client(key=ORS_API_KEY)

    start = client.pelias_search(start_name)["features"][0]["geometry"]["coordinates"]
    end = client.pelias_search(end_name)["features"][0]["geometry"]["coordinates"]

    route = client.directions(
        coordinates=[start, end],
        profile="cycling-regular",
        format="geojson",
        elevation=True
    )

    feature = route["features"][0]
    coords = feature["geometry"]["coordinates"]
    summary = feature["properties"]["summary"]
    ascent = feature["properties"]["ascent"]
    descent = feature["properties"]["descent"]

    print(f"✓ Distanz: {summary['distance']/1000:.2f} km")
    print(f"✓ Dauer: {summary['duration']/60:.1f} min")
    print(f"✓ Aufstieg: {ascent:.0f} m | Abstieg: {descent:.0f} m")

    return (
        coords,
        start,
        end,
        summary["distance"],
        summary["duration"],
        ascent,
        descent
    )

# ==========================
# POIs (Overpass API)
# ==========================
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter"
]

def route_bbox(route, buffer_deg=0.001):
    lons = [p[0] for p in route]
    lats = [p[1] for p in route]
    return (
        min(lons) - buffer_deg,
        min(lats) - buffer_deg,
        max(lons) + buffer_deg,
        max(lats) + buffer_deg
    )

def post_overpass(query):
    last_error = None
    for url in OVERPASS_URLS:
        try:
            r = requests.post(url, data=query, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"Overpass Timeout bei {url}")
            last_error = e
    raise last_error

def get_pois_along_route(route):
    west, south, east, north = route_bbox(route)

    query = f"""
    [out:json][timeout:60];
    (
      node({south},{west},{north},{east})["amenity"="drinking_water"];
      node({south},{west},{north},{east})["amenity"="toilets"];
      node({south},{west},{north},{east})["amenity"="cafe"];
      node({south},{west},{north},{east})["shop"="bakery"];
    );
    out body;
    """

    data = post_overpass(query)
    pois = data.get("elements", [])
    print(f"✓ Gefundene POIs: {len(pois)}")
    return pois

# ==========================
# KARTE (Folium)
# ==========================

def create_map(route, start, end, dist, dur, asc, desc, pois):
    m = folium.Map(location=[start[1], start[0]], zoom_start=13)

    folium.PolyLine(
    [(p[1], p[0]) for p in route],
    weight=6,
    color="blue"
    ).add_to(m)

    folium.Marker(
        [start[1], start[0]],
        popup="Start",
        icon=folium.Icon(color="green", icon="bicycle", prefix="fa")
    ).add_to(m)

    folium.Marker(
        [end[1], end[0]],
        popup="Ziel",
        icon=folium.Icon(color="red", icon="flag", prefix="fa")
    ).add_to(m)

    # POIs
    for poi in pois:
        tags = poi.get("tags", {})
        name = tags.get("name", "POI")
        folium.Marker(
            [poi["lat"], poi["lon"]],
            popup=name,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    # Info-Box
    info = f"""
    <div style="
        position: fixed;
        bottom: 20px;
        left: 20px;
        z-index: 9999;
        background: white;
        padding: 10px;
        border: 2px solid grey;
        font-size: 14px;">
        <b>Distanz:</b> {dist/1000:.2f} km<br>
        <b>Dauer:</b> {dur/60:.1f} min<br>
        <b>Aufstieg:</b> {asc:.0f} m<br>
        <b>Abstieg:</b> {desc:.0f} m
    </div>
    """

    m.get_root().html.add_child(folium.Element(info))
    m.save("route.html")
    print("✓ Karte gespeichert: route.html")

# ==========================
# AUTOMATISCHER START
# ==========================

if __name__ == "__main__":
    print("=== Fahrrad-Routenplaner ===\n")

    start = input("Start (Enter = Karlsruher Schloss): ").strip() or "Karlsruher Schloss"
    end = input("Ziel (Enter = Hauptbahnhof Karlsruhe): ").strip() or "Hauptbahnhof Karlsruhe"

    print("\nBerechne Route...\n")

    route, start_c, end_c, dist, dur, asc, desc = find_bike_route(start, end)

    print("\nSuche POIs entlang der Route...\n")
    pois = get_pois_along_route(route)

    create_map(route, start_c, end_c, dist, dur, asc, desc, pois)
