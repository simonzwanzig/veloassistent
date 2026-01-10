import openrouteservice
import folium
from folium import Element
import json


# ==========================
# KONFIGURATION
# ==========================

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjRlYmE4MmQyY2YzMzRiM2Q4ZTMzODhhNTIzOTkzNmRjIiwiaCI6Im11cm11cjY0In0="


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
# KARTE (Folium)
# ==========================

def create_map(route, start, end, dist, dur, asc, desc):

    # lon,lat → lat,lon
    route_latlon = [(p[1], p[0]) for p in route]

    m = folium.Map(location=[start[1], start[0]], zoom_start=13)
    map_name = m.get_name()

    route_latlon = [(p[1], p[0]) for p in route]

    folium.PolyLine(
    route_latlon,
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

    # POI-Layer (leer!)

    poi_layers = [
        "💧 Trinkwasser",
        "🚻 Toiletten",
        "☕ Café",
        "🚲 Fahrradladen",
        "🥐 Bäckerei",
        "Luftpumpe",
        "Hostel",
        "Schutzhütte",
        "Campingplatz",
        "Supermarkt",
        "Bank",
        "Waschsalon",
        "Friedhof",
        "Repairstation",
        "Fahrradständer",
        "Bahnhof"

    ]

    poi_groups = {}
    for name in poi_layers:
        fg = folium.FeatureGroup(name=name, show=False)
        fg.add_to(m)
        poi_groups[name] = fg

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
    m.get_root().html.add_child(
    Element(f"<script>const ROUTE_DATA = {json.dumps(route_latlon)};</script>")
    )
    map_id = m.get_name()

    # ==========================
    # JavaScript (Lazy POIs + 250 m)
    # ==========================

    map_name = m.get_name()

    js = """
    <script>
    document.addEventListener("DOMContentLoaded", function () {

        // Leaflet-Map von Folium finden
        const map = Object.values(window).find(v => v instanceof L.Map);
        if (!map) {
            console.error("Leaflet map not found");
            return;
        }

        // Route (lat, lon) – kommt von Python als ROUTE_DATA
        const route = ROUTE_DATA;

        const loadedLayers = {};

        // Overpass-Query: NUR POIs im Radius entlang der Route
        function overpassQueryAlongRoute(route, radius, tag, value) {

            const points = route
                .filter((_, i) => i % 10 === 0) // ca. alle 200 m
                .map(p =>
                    `node(around:${radius},${p[0]},${p[1]})["${tag}"="${value}"];`
                )
                .join("\\n");

            return `
    [out:json][timeout:45];
    (
    ${points}
    );
    out body;
    `;
        }

        map.on("overlayadd", function (e) {

            const name = e.name;
            if (loadedLayers[name]) return;
            loadedLayers[name] = true;

            let tag = null;
            let value = null;

            if (name === "💧 Trinkwasser") { tag = "amenity"; value = "drinking_water"; }
            if (name === "🚻 Toiletten")  { tag = "amenity"; value = "toilets"; }
            if (name === "☕ Café")       { tag = "amenity"; value = "cafe"; }
            if (name === "🚲 Fahrradladen") { tag = "shop"; value = "bicycle"; }
            if (name === "🥐 Bäckerei")   { tag = "shop"; value = "bakery"; }
            if (name === "Luftpumpe")   { tag = "amenity"; value = "compressed_air"; }
            if (name === "Hostel")   { tag = "tourism"; value = "hostel"; }
            if (name === "Schutzhütte")   { tag = "tourism"; value = "wilderness_hut"; }
            if (name === "Campingplatz")   { tag = "tourism"; value = "camp_site"; }
            if (name === "Supermarkt")   { tag = "shop"; value = "supermarket"; }
            if (name === "Bank")   { tag = "amenity"; value = "atm"; }
            if (name === "Waschsalon")   { tag = "shop"; value = "laundry"; }
            if (name === "Friedhof")   { tag = "amenity"; value = "graveyard"; }
            if (name === "Repairstation")   { tag = "amenity"; value = "bicyle_repair_station"; }
            if (name === "Fahrradständer")   { tag = "amenity"; value = "bicycle_parking"; }
            if (name === "Bahnhof")   { tag = "railway"; value = "station"; }

            if (!tag) return;

            fetch("https://overpass-api.de/api/interpreter", {
                method: "POST",
                headers: { "Content-Type": "text/plain" },
                body: overpassQueryAlongRoute(route, 250, tag, value)
            })
            .then(r => r.json())
            .then(data => {
                data.elements.forEach(el => {
                    if (!el.lat || !el.lon) return;

                    L.marker([el.lat, el.lon])
                        .addTo(e.layer)
                        .bindPopup(`<b>${name}</b>`);
                });
            })
            .catch(err => console.error("Overpass error:", err));
        });

    });
    </script>
    """

    js = js.replace("MAP_NAME", map_name)
    folium.LayerControl(collapsed=False).add_to(m)
    route_latlon = [(p[1], p[0]) for p in route]
    js = js.replace("ROUTE_DATA", json.dumps(route_latlon))
    m.get_root().html.add_child(Element(js))

    m.save("route.html")
    print("✓ route.html erstellt")


# ==========================
# AUTOMATISCHER START
# ==========================

if __name__ == "__main__":
    print("=== Fahrrad-Routenplaner ===\n")

    start = input("Start (Enter = Karlsruher Schloss): ").strip() or "Karlsruher Schloss"
    end = input("Ziel (Enter = Hauptbahnhof Karlsruhe): ").strip() or "Hauptbahnhof Karlsruhe"

    print("\nBerechne Route...\n")

    route, s, e, d, t, a, de = find_bike_route(start, end)
    create_map(route, s, e, d, t, a, de)